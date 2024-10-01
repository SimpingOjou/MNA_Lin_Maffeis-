# By: Lin Chang Hui Simone (CP: 10661335; MAT: 934949)
# & Simone Maffeis (CP: 10732382; MAT: 937024)

#Consegna:
#Dato un circuito LRTI con sintassi LTSpice in input, risolvo quest'ultimo in DC.
#Risoluzione basata sul metodo MNA. Abbiamo gestito ogni generatore pilotato.
#Togliendo i commenti alle y_string si può vedere in string


#importo librerie
import os
from os import system, name, execv
from Tools.scripts.nm2def import symbols
from sympy import *

# variabili globali & eccezioni
from sympy.matrices.common import NonInvertibleMatrixError
comp_list = []
nodes_list = []

#definizione della classe componente
class Comp:
    # funzione di inizializzazione
    def __init__(self, name, value, np, nn, npx, nnx, dep):
        self.kind = name[0]  # tipo di componente (res, cavo, ecc.)
        self.name = name
        #self.sym = symbols(name)

        if self.kind == 'G' or self.kind == 'H' or self.kind == 'F' or self.kind == 'E':
            self.value = symbols(value) #creo simbolo equivalente al parametro
        else:
            self.value = Rational(value) #è un valore.

        self.np = np
        self.nn = nn

        #nodi dipendenti pos/neg
        self.npx = npx
        self.nnx = nnx

        #dipendenza CCVS
        self.dep = dep

def menu():
    file_name = '-1'
    cls()
    print('Script realizzato da Lin Chang Hui Simone (10661335) e Maffeis Simone (10732382).')
    print('Dato un circuito LRTI con sintassi LTSpice in input, lo risolvo in DC.')
    print('Risoluzione basata sul metodo MNA.\n\n')
    input('Premi invio per continuare...')
    cls()

    while (true):
        print("[1] Circuito con 2 generatori di tensione e 1 di corrente (Esempio);")
        print("[2] Circuito con VCCS (Esempio);")
        print("[3] Circuito con CCVS (Esempio);")
        print("[4] Circuito con CCCS (Esempio);")
        print("[5] Circuito con VCVS (Esempio);")
        print("[6] Risoluzione NetList arbitraria presente nel PC;\n")
        try:
            entrata = int(input("Inserire il numero corrispondente alla scelta: "))
            if entrata < 1 or entrata > 6:
                print("\nNumero non valido.")
                input('Premi invio per continuare...')
                cls()
            else:
                cls()
                break
        except ValueError:
            print("\nSi prega di inserire un numero.")
            input('Premi invio per continuare...')
            cls()  
            continue
    if (entrata == 1):
        file_name = '2GT1GC.net'
    if (entrata == 2):
        file_name = 'VCCS.net'
    if (entrata == 3):
        file_name = 'CCVS.net'
    if (entrata == 4):
        file_name = 'CCCS.net'
    if (entrata == 5):
        file_name = 'VCVS.net'
    if (entrata == 6):
        file_name = input("Inserire nome del file se nella stessa cartella, altrimenti directory: ")
    return file_name    

def end():
    while (true):
        risposta = str(input("\nContinuare a usare lo script? (S/n): ")).lower()
        if risposta == "" or risposta == "s":
            print("\nRiavvio dello script...")
            input('Premi invio per continuare...')
            os.system("python main.py")
            quit()
        elif risposta == "n":
            quit()
        else: 
            continue
            
#funzione pulizia terminale
def cls(): 
  
    #se windows
    if name == 'nt': 
        _ = system('cls') 
  
    #se posix
    else: 
        _ = system('clear') 

# lettura del file
def parse(path):
    try:
        circuit_file = open(path, "r")
        lines = circuit_file.readlines()
        circuit_file.close()
    except FileNotFoundError:
        print("\nFile non trovato o directory non valida.\nAssicurarsi di aver inserito anche l'estensione del file (.net, .txt, ecc.)")
        print("\nUscita dal programma.")
        quit()
    #prendo le informazioni utili dal file
    for line in lines:
        line = line.strip().upper()
        #salto i pezzi non rilevanti
        if line == "":
            continue

        if line.find("*") != -1:
            continue
        elif line.startswith("."):
            continue
        else:  #è un componente!
            #separo la lista in sottoelementi
            m_line = line.split()

        # aggiungo il nuovo componente nella lista dei componenti
        if m_line[0].startswith('G') or m_line[0].startswith('E'): #VCCS o VCVS
            m_line[5] = m_line[5].replace(',', '.') #da problemi se c'è la virgola
            componente = Comp(m_line[0].upper(), m_line[5], m_line[1].upper(), m_line[2].upper(), m_line[3].upper(), m_line[4].upper(), '-1')
            comp_list.append(componente)
        elif m_line[0].startswith('H') or m_line[0].startswith('F'): #CCVS o CCCS
            m_line[4] = m_line[4].replace(',', '.')
            componente = Comp(m_line[0].upper(), m_line[4], m_line[1].upper(), m_line[2].upper(), -1, -1, m_line[3].upper())
            comp_list.append(componente)
        else:
            m_line[3] = m_line[3].replace(',', '.')
            componente = Comp(m_line[0].upper(), m_line[3], m_line[1].upper(), m_line[2].upper(), -1, -1, '-1')
            comp_list.append(componente)

# gioco con le matrici
def compute_circuit():
    # contatore nodi
    counter = 0
    nodes_list.append(0)

    #gestione delle serie (poco elegante, ma funziona)
    for inst_comp in comp_list:
        if inst_comp.np.startswith('P'):
            for iinst_comp in comp_list:
                if iinst_comp.nn == inst_comp.np:
                    inst_comp.np = iinst_comp.np
                    iinst_comp.nn = inst_comp.nn

    #conta dei nodi
    for inst_comp in comp_list:
        # esiste il nodo p/n nella nostra lista?
        if inst_comp.np not in nodes_list and inst_comp.np.startswith('N'):
            #aggiungo nodo positivo
            nodes_list.append(inst_comp.np)
            counter += 1
        if inst_comp.nn not in nodes_list and inst_comp.nn.startswith('N'):
            #nn
            nodes_list.append(inst_comp.nn)  
            counter += 1
        # esistono generatori di tensione?
        if inst_comp.kind == 'V' or inst_comp.kind == 'H' or inst_comp.kind == 'E':
            counter += 1
 
    # definizione matrice nxn (AGAt)
    y_matrix = [[0 for row in range(0, counter)] for col in range(0, counter)]
    #y_string = [['0' for row in range(0, counter)] for col in range(0, counter)]

    # definizione vettore V (potenziali) e J (valori noti)
    v_string = ['0' for row in range(0,counter)]
    j_string = ['0' for row in range(0, counter)]
    j_matrix = [0 for row in range(0, counter)]

    node_num = 0  # contatore di lavoro sul nodo/gen

    # lavoro sulla lista dei nodi \ GND
    for node in nodes_list[1:]:
        # aggiungo i nodi alla V
        v_string[node_num] = node

        node_num += 1

    # lavoro sulla lista dei componenti
    for inst_comp in comp_list:
        # è il gen di tensione?
        if inst_comp.kind == 'V': 
            j_matrix[node_num] = Rational(inst_comp.value)
            v_string[node_num] = inst_comp.name
            j_string[node_num] = inst_comp.name

            node_num += 1

        if inst_comp.kind == 'H' or inst_comp.kind == 'E':
            v_string[node_num] = inst_comp.name
            
            node_num += 1

        # è un gen di corrente?
        if inst_comp.kind == 'I':
            # controllo verso corrente
            if inst_comp.np != '0':
                j_matrix[v_string.index(inst_comp.np)] -= inst_comp.value
                j_string[v_string.index(inst_comp.np)] += '-' + inst_comp.name
                
            if inst_comp.nn != '0':
                j_matrix[v_string.index(inst_comp.nn)] += inst_comp.value
                j_string[v_string.index(inst_comp.nn)] += '+' + inst_comp.name
 
    # riempiamo la matrice Y
    for inst_comp in comp_list:
        # parte NA
        if inst_comp.kind == 'R':
            # controllo non abbia collegamento a terra e inserisco valore
            if inst_comp.np != '0':
               y_matrix[v_string.index(inst_comp.np)][v_string.index(inst_comp.np)] += Rational(1/inst_comp.value)
               #y_string[v_string.index(inst_comp.np)][v_string.index(inst_comp.np)] += ("+(1/" + inst_comp.name + ")")

            if inst_comp.nn != '0':
                y_matrix[v_string.index(inst_comp.nn)][v_string.index(inst_comp.nn)] += Rational(1/inst_comp.value)
                #y_string[v_string.index(inst_comp.nn)][v_string.index(inst_comp.nn)] += ("+(1/" + inst_comp.name + ")")

            if inst_comp.nn != '0' and inst_comp.np != '0':
                # inserimento di G
                y_matrix[v_string.index(inst_comp.nn)][v_string.index(inst_comp.np)] += Rational(-1/inst_comp.value)
                y_matrix[v_string.index(inst_comp.np)][v_string.index(inst_comp.nn)] += Rational(-1/inst_comp.value)
                #y_string[v_string.index(inst_comp.nn)][v_string.index(inst_comp.np)] += ("+(-1/" + inst_comp.name + ")")
                #y_string[v_string.index(inst_comp.np)][v_string.index(inst_comp.nn)] += ("+(-1/" + inst_comp.name + ")")
        # è VCCS?
        if inst_comp.kind == 'G':
            #controllo se corrente entra o esce dal nodo
            #sinceramente non so come mai funzioni, secondo me è sbagliato
            if inst_comp.np != '0': #così funziona se e solo se un nodo è messa a terra...
                #y_string[v_string.index(inst_comp.npx)][v_string.index(inst_comp.npx)] += '+G'
                #y_string[v_string.index(inst_comp.npx)][v_string.index(inst_comp.nnx)] += '-G'

                y_matrix[v_string.index(inst_comp.npx)][v_string.index(inst_comp.npx)] += inst_comp.value
                y_matrix[v_string.index(inst_comp.npx)][v_string.index(inst_comp.nnx)] -= inst_comp.value
            else: #np è 0, quindi corrente entrante nel nodo
                #prendo la riga "ponteziale maggiore" e le colonne "potenziale minore" a cui è attaccata
                #la tensione per cui è dipendente

                #y_string[v_string.index(inst_comp.nnx)][v_string.index(inst_comp.npx)] += '-G'
                #y_string[v_string.index(inst_comp.nnx)][v_string.index(inst_comp.nnx)] += '+G'

                y_matrix[v_string.index(inst_comp.nnx)][v_string.index(inst_comp.npx)] -= inst_comp.value
                y_matrix[v_string.index(inst_comp.nnx)][v_string.index(inst_comp.nnx)] += inst_comp.value
        # parte modificata di NA
        if inst_comp.kind == 'V' or inst_comp.kind == 'H' or inst_comp.kind == 'E':
            # controllo non abbia collegamento a terra e inserisco valore
            if inst_comp.np != '0':
                y_matrix[v_string.index(inst_comp.np)][v_string.index(inst_comp.name)] += 1
                y_matrix[v_string.index(inst_comp.name)][v_string.index(inst_comp.np)] += 1
                #y_string[v_string.index(inst_comp.np)][v_string.index(inst_comp.name)] += '+1'
                #y_string[v_string.index(inst_comp.name)][v_string.index(inst_comp.np)] += '+1'   

            if inst_comp.nn != '0':
                y_matrix[v_string.index(inst_comp.nn)][v_string.index(inst_comp.name)] -= 1
                y_matrix[v_string.index(inst_comp.name)][v_string.index(inst_comp.nn)] -= 1
                #y_string[v_string.index(inst_comp.nn)][v_string.index(inst_comp.name)] += '-1'
                #y_string[v_string.index(inst_comp.name)][v_string.index(inst_comp.nn)] += '-1'
        #è CCVS?
        if inst_comp.kind == 'H':
            y_matrix[v_string.index(inst_comp.name)][v_string.index(inst_comp.dep)] -= inst_comp.value
        # è CCCS?
        if inst_comp.kind == 'F':
            if inst_comp.np != '0':
                y_matrix[v_string.index(inst_comp.np)][v_string.index(inst_comp.dep)] -= inst_comp.value
                y_matrix[v_string.index(inst_comp.nn)][v_string.index(inst_comp.dep)] += inst_comp.value
            else:
                y_matrix[v_string.index(inst_comp.np)][v_string.index(inst_comp.dep)] += inst_comp.value
                y_matrix[v_string.index(inst_comp.nn)][v_string.index(inst_comp.dep)] -= inst_comp.value
        #è VCVS?
        if inst_comp.kind == 'E':
            if inst_comp.npx != '0':
                y_matrix[v_string.index(inst_comp.name)][v_string.index(inst_comp.npx)] -= inst_comp.value
                y_matrix[v_string.index(inst_comp.name)][v_string.index(inst_comp.nnx)] += inst_comp.value
            else:
                y_matrix[v_string.index(inst_comp.name)][v_string.index(inst_comp.npx)] += inst_comp.value
                y_matrix[v_string.index(inst_comp.name)][v_string.index(inst_comp.nnx)] -= inst_comp.value
            

    # lavoriamo sull'output
    v_counter = 0

    for v_counter in range(counter):
        if v_string[v_counter] in nodes_list:
            v_string[v_counter] = 'V' + v_string[v_counter]
        else:  # se non è un nodo, è un generatore di tensione
            v_string[v_counter] = 'I(' + v_string[v_counter] + ')'

    y_matrix = Matrix(y_matrix)
    j_matrix = Matrix(j_matrix)

    try:
        res_sym = j_matrix.transpose() * y_matrix.inv()
    except NonInvertibleMatrixError as ex:
        print('Inserimento di matrice non invertibile')

    print('Matrice AGAt:\n')
    #print (y_string)
    pprint(y_matrix)
    print('\nVettore trasposto dei valori noti:\n') #trasposto per fattore estetico sull'output
    print(j_string)
    pprint(j_matrix.transpose())
    print('\nSoluzione:')
    for values in range(counter):
        print(v_string[values] + ' = ' + str(res_sym[values]))

# esecuzione
if __name__ == "__main__":
    parse(menu())
    compute_circuit()
    end()