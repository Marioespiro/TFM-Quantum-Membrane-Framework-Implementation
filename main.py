import os
import re
import xml.etree.cElementTree as ET
from math import ceil, floor, log2
#from qiskit import QuantumCircuit
#from qiskit_ibm_runtime import QiskitRuntimeService

#service = QiskitRuntimeService(channel="ibm_quantum", token = "")
# EL TOKEN ES PERSONAL E INTRANSFERIBLE, REQUIERE CUENTA DE IBM QUANTUM PLATFORM

# ===========================================================================
# ================================== INPUT ==================================
# ===========================================================================
# Aquí se introduce el enunciado del problema, es decir, la lista de cadenas.

n = ["man", "can", "ants"]

# ===========================================================================
# ================================== SETUP ==================================
# ===========================================================================
# Aquí se genera el archivo .pli que se introduce al compilador para obtener
# el .xml.

n1 = len(n[0])
n2 = len(n[1])
n3 = len(n[2])
nl = len(n)
N = ceil(log2(n1+1))

A = []
multiconjuntos = []
indice_cadena = 1
for cadena in n:
    multiconjunto_cadena = []
    indice_caracter = 1
    for caracter in cadena:
        if caracter not in A:
            A.append(caracter)
        if indice_cadena == 1:
            objeto = "a{{{},{},0,0}}".format(indice_caracter, A.index(caracter)+1)
            multiconjunto_cadena.append(objeto)
        else:
            objeto = "b{{{},{},{},0}}".format(indice_cadena, indice_caracter, A.index(caracter)+1)
            multiconjunto_cadena.append(objeto)
        indice_caracter += 1
    multiconjuntos.append("@ms(2) += " + ", ".join(multiconjunto_cadena) + ";\n")
    indice_cadena += 1

k = len(A)
K = ceil(log2(k))

def f(i,j,l):
    salida = []
    if(i==1):
        salida.append("e{{{},{}}}".format(j, l))
        for iteracion in range(K):
            indice_1 = K*(j-1+sum(len(n[t]) for t in range(1,nl)))+iteracion+1
            indice_2 = floor((l-1)/2**iteracion) % 2

            salida.append("I{{{},{}}}".format(indice_1, indice_2))
    else:
        for iteracion in range(K):
            indice_1 = K*(j-1+sum(len(n[t]) for t in range(1,i-1)))+iteracion+1
            indice_2 = floor((l-1)/2**iteracion) % 2

            salida.append("I{{{},{}}}".format(indice_1, indice_2))
    
    return ", ".join(salida)

def F(t):
    salida = []
    for iteracion in range(N):
        indice_1 = K*(sum(len(n[tt]) for tt in range(0,nl)))+iteracion+1
        indice_2 = floor(t/2**iteracion) % 2

        salida.append("I{{{},{}}}".format(indice_1, indice_2))
    return ", ".join(salida)

I1 = ["/* I1 */\n"]
for i in range(1,nl+1):
    for j in range(1,len(n[i-1])+1):
        for l in range(1, k+1):
            #for s in range(1, n1+2):
            I1.append("+[b{{{},{},{},{}}} --> {}]'2;\n".format(i, j, l, n1+1, f(i,j,l)))
        I1.append("\n")
    I1.append("\n")

I2 = ["/* I2 */\n"]
for t in range(1,nl+1):
    lista_f = []
    for iteracion in range(t+1,n1+1):
        lista_f.append(f(1, iteracion, 0))
    if(len(lista_f) > 0):
        I2.append("+[c{{{}}} --> cc{{{}}}, T, {}, {}]'2;\n".format(t, t, ", ".join(lista_f), F(t)))
    else:
        I2.append("+[c{{{}}} --> cc{{{}}}, T, {}]'2;\n".format(t, t, F(t)))
I2.append("\n")


with open("setup1.txt", encoding="UTF-8") as setup_1:
    lineas1 = setup_1.readlines()
    with open("setup2.txt", encoding="UTF-8") as setup_2:
        lineas2 = setup_2.readlines()
        with open("setup3.txt", encoding="UTF-8") as setup_3:
            lineas3 = setup_3.readlines()
            
            with open("initialConf.pli", "w", encoding="UTF-8") as f_out:
                for linea in lineas1:
                    f_out.write(linea)
                
                for multiconjunto in multiconjuntos: # Multiconjunto de objetos de entrada, separado en líneas por cadena.
                    f_out.write(multiconjunto)
                
                for linea in lineas2:
                    f_out.write(linea)

                for regla in I1:        # Reglas de tipo I1.
                    f_out.write(regla)

                for regla in I2:        # Reglas de tipo I2.
                    f_out.write(regla)
                
                for linea in lineas3:
                    f_out.write(linea)
                
                # Llamada a la función que contiene todas las reglas, utilizando los valores pertinentes en la cabecera.
                f_out.write("call rules({},{},{},{},{});\n}} /* End of main module */".format(nl, n1, n2, n3, k))

# Se compila el archivo .pli
os.system("java -jar plinguacore.jar plingua initialConf.pli unpaso.xml")
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
    os.system("java -jar plinguacore.jar plingua_sim unpaso.xml -o unpaso.txt -st 1")

    # Lectura del archivo de salida
    with open ("unpaso.txt") as f:
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
                    parar = True # Se para la computación, al no disponer de sistema cuántico

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
            # job = service.run(q2, shots=1)
            # if job.result().results[0].data.counts.get("0x1") == 1:
            #     result = ("yes", 1)
            # else:
            #     result = ("no", 1)
            # infoMembrana[membrana][2].append(result)
            # infoMembrana[membrana][2].append(("TT", 1))

    # RECONSTRUCCIÓN DEL ARCHIVO DE ENTRADA
    #print(hijosMembranaPiel)
    print(infoMembrana)

    tree = ET.parse("unpaso.xml")
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
    tree.write("unpaso.xml", encoding="UTF-8", xml_declaration=True)

print("EJECUCIÓN FINALIZADA")