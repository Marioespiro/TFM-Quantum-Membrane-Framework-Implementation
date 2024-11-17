import os
import re
import xml.etree.cElementTree as ET
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

# ===========================================================================
# ================================== SETUP ==================================
# ===========================================================================
q2 = QuantumCircuit(2,1)
q2.h(0)
q2.cx(0,1)
q2.h(0).inverse()
q2.measure(1,0)
q2.draw()

backend = AerSimulator()

# Se compila el archivo .pli
os.system("java -jar plinguacore.jar plingua presentacion.pli unpaso_presentacion.xml")
# Se copia el archivo .xml para conservar la configuración inicial
#copyfile("initialConf.xml", "unpaso.xml")

# ===========================================================================
# ================================ MAIN LOOP ================================
# ===========================================================================
# Aquí se ejecuta el simulador paso por paso, extrayendo cada vez tanto la
# estructura de membranas como los objetos de cada membrana. En el caso de
# detectarse uno o varios objetos T, se llama al sistema cuántico. Tras esto,
# se reescribe el archivo .xml para prepararlo para el próximo paso de computación.
# Ahora mismo, en lugar de llamar al archivo cuántico, simplemente para la
# computación.

parar = False
while parar == False:
    # Ejecución de un paso de computación
    os.system("java -jar plinguacore.jar plingua_sim unpaso_presentacion.xml -o unpaso_presentacion.txt -st 1 -v 0")

    # Lectura del archivo de salida
    with open ("unpaso_presentacion.txt") as f:
        lineas = f.readlines()


    # Condición de parada. Búsqueda y eliminación de la configuración inicial.
    patronParada = "^Halting"
    patronConf = "^\s+CONFIGURATION: 1"
    indiceComienzo = None

    for linea in lineas:
        if re.match(patronConf, linea):
            indiceComienzo = lineas.index(linea)
        elif re.match(patronParada,linea):
            parar = True

    lineas = lineas[indiceComienzo:]

    # Extracción de contenidos de cada membrana. Comprobación de existencia de objeto T
    idPattern = "^[\s\w]+MEMBRANE ID: "
    labelPattern = "^[\s\w]+: \d, Label: "
    chargePattern = "^[\s\w]+: \d, Label: \d, Charge: "
    parentPattern = "^[\s\w]+Parent membrane ID: "
    infoMembrana = {} # ID: (etiqueta, idPadre, [(objeto, multiplicidad)])
    hijosMembranaPiel = {} #Lo dejo aquí por posible utilidad futura, pero no se usa en este sistema
    pasoCuantico = []

    for linea in lineas:
        hayMembrana = re.match(idPattern, linea)

        if(hayMembrana):
            idMembrana = int(linea[hayMembrana.end()])

            etiquetaMembrana = linea[re.match(labelPattern, linea).end()]
            cargaMembrana = linea[re.match(chargePattern, linea).end()]
            if cargaMembrana != "0":
                cargaMembrana += "1"

            if(idMembrana != 0):
                if re.match(parentPattern, lineas[lineas.index(linea)+2]):
                    lineaPadre = lineas[lineas.index(linea)+2]
                else:
                    lineaPadre = lineas[lineas.index(linea)+3]
                idPadre = lineaPadre[re.match(parentPattern, lineaPadre).end()]
                
                if idPadre in hijosMembranaPiel.keys():
                    hijosMembranaPiel[idPadre].append(idMembrana)
                else:
                    hijosMembranaPiel[idPadre] = [idMembrana]

            lineaContenidos = lineas[lineas.index(linea)+1]
            contenidosParseado = lineaContenidos.strip().split(": ")[-1]
            
            if(contenidosParseado != "#" ):
                objetos = contenidosParseado.split(", ")
                multiconjunto = []

                if("T" in objetos):
                    objetos.remove("T")
                    pasoCuantico.append(idMembrana)

                for objeto in objetos:
                    objetoMult = objeto.split("*")
                    if len(objetoMult) > 1:
                        multiconjunto.append((objetoMult[0], objetoMult[1]))
                    else:
                        multiconjunto.append((objetoMult[0],"1"))


                #Membrana CON objetos
                infoMembrana[idMembrana] = (etiquetaMembrana, cargaMembrana, multiconjunto)
            else:
                #Membrana SIN objetos
                infoMembrana[idMembrana] = (etiquetaMembrana, cargaMembrana, None)

    # AQUÍ IRÍA EL PASO CUÁNTICO
    if len(pasoCuantico) > 0:
        for membrana in pasoCuantico:
            print("APLICACIÓN DE PASO CUÁNTICO EN LA MEMBRANA " + infoMembrana[membrana][0] + " CON EL MULTICONJUNTO " + str(infoMembrana[membrana][2]))
            job = backend.run(q2, shots=1)
            if job.result().results[0].data.counts.get("0x1") == 1:
                result = ("yes", 1)
            else:
                result = ("no", 1)
            infoMembrana[membrana][2].append(result)
            infoMembrana[membrana][2].append(("TT", 1))

    # RECONSTRUCCIÓN DEL ARCHIVO DE ENTRADA
    #print(hijosMembranaPiel)
    print(infoMembrana)

    tree = ET.parse("unpaso_presentacion.xml")
    root = tree.getroot()

    root.remove(root.find("init_config"))
    init_config = ET.Element("init_config")

    membrana_1 = ET.Element("membrane", attrib={"label":"1", "charge":infoMembrana[0][1]})
    if(infoMembrana[0][2] is not None):
        multiconjunto_1 = ET.Element("multiset")
        for objeto in infoMembrana[0][2]:
            if int(objeto[1])>1:
                multiconjunto_1.append(ET.Element("object", attrib={"name": objeto[0], "multiplicity": objeto[1]}))
            else:
                multiconjunto_1.append(ET.Element("object", attrib={"name": objeto[0]}))
        membrana_1.append(multiconjunto_1)

    for id_membrana, datos_membrana in infoMembrana.items():
        if(id_membrana != 0):
            membrana_i = ET.Element("membrane", attrib={"label": datos_membrana[0], "charge": datos_membrana[1]})
            if(datos_membrana[2] is not None):
                multiconjunto_i = ET.Element("multiset")
                for objeto in datos_membrana[2]:
                    if int(objeto[1])>1:
                        multiconjunto_i.append(ET.Element("object", attrib={"name": objeto[0], "multiplicity": objeto[1]}))
                    else:
                        multiconjunto_i.append(ET.Element("object", attrib={"name": objeto[0]}))
                membrana_i.append(multiconjunto_i)
            membrana_1.append(membrana_i)

    init_config.append(membrana_1)
    root.insert(0, init_config)

    ET.indent(tree, '  ')
    tree.write("unpaso_presentacion.xml", encoding="UTF-8", xml_declaration=True)

print("EJECUCIÓN FINALIZADA")