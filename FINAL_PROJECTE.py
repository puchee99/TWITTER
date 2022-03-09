#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec  5 15:45:47 2019

@author: puche99
"""
import networkx as nx
import tweepy
import matplotlib.pyplot as plt
import os
import random
import pickle

consumer_key = "lY8nNMx7eI4J3bFVDZwh5VZBi"
consumer_secret = "SkaFJ8s2eBhBdR3PBl6wBgb0VKPym9dZkAn9WGUHSiKQlgMmi0"
access_token = "1202593632747962368-ncrjFsSPmLoc4ygUey2OH6rvePtkWA"
access_token_secret = "M53a9od044FURPiMqeqTPSWONB0vzUPGnvhOry5Mg6Mpw"

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth, wait_on_rate_limit = True, wait_on_rate_limit_notify = True)

    
#Calcula el nombre de nivells que farà la cerca. També quants nodes guardar a cada nivell
def branches(max_nodes_to_crawl, aux = 10):
    '''
    :param max_nodes_to_crawl: number of nodes to crawl
    :param aux: arbitrary value to know the levels
    :return: 
        layers: number of levels
        [start,start2,start3]: nodes to crawl in different levels
    '''
    if max_nodes_to_crawl < aux:
        layers = 2
        start = 1
        start2 = aux -1
        start3 = None
    elif max_nodes_to_crawl < aux**2:
        layers = 3
        start = 1
        start2 = aux // 3
        start3 = start2 * 2
    return(layers,[start,start2,start3])

def first_layer(seed, max_followers, explore = 5, filesave = None):
    """"
        Donat un seed s'exploren n seguidors. S'afegeixen els usuaris si no tenen més de 10k seguidors
    """
    results = []
    try:
        seed_followers = api.followers_ids(seed.screen_name)
        random.shuffle(seed_followers)
        print('Layer_started with :'+str(seed.screen_name)+' and '+str(len(seed_followers))+' followers' )
        for tf in seed_followers[:explore]: 
            if api.get_user(tf).followers_count < max_followers: 
                results.append((seed.screen_name,api.get_user(tf).screen_name))
                status = api.show_friendship(source_id = seed.id_str,target_id = api.get_user(tf).id_str)
                if status[0].following == True:
                    results.append((api.get_user(tf).screen_name,seed.screen_name))
    except:
        print('Cannot with that user')
    return results

def crawler(seed, max_nodes_to_crawl = 18, max_followers = 10000): 
    """
        Inicialitza el crawler i finalment crida la funció per escriure i guardar un set de noms 
    """
    queue = dict()
    tw_seed = api.get_user(seed)
    layers,starts = branches(max_nodes_to_crawl)
    queue['ly'] = first_layer(tw_seed, max_followers,starts[0])
    if layers >= 2:
        queue['ly2'] = list()
        [queue['ly2'].append(first_layer(api.get_user(name[1]),10000,starts[1])) for name in queue['ly']]
    if layers >= 3:
        queue['ly3'],aux = list(),list()
        for val in range(len(queue['ly2'])):
            aux+= queue['ly2'][val]
        [queue['ly3'].append(first_layer(api.get_user(name[1]),10000,starts[2])) for name in aux]
    doc_name = str(tw_seed.screen_name)+"_"+str(max_nodes_to_crawl)+".txt"
    save(queue,layers,doc_name)
    f = open(doc_name,"r")
    names = []
    for lines in f:
        names.append(lines.split()[0])
        names.append(lines.split()[-1])
    names = list(set(names))
    add_all_followers(names,doc_name)        
    return

def add_all_followers(names,filename):
    """
        Comprova que si de tots els usuaris crawlejats hi ha alguna relació que no s'havia apuntat
        Això és molt útil perquè sino perdem informació del graf, ja que si una aresta real és bidireccional,
            i la guardem direcional només en un sentit, tenim  informació errònea
    """
    new_connections = []
    for usr in names:
        for usr2 in names:
            try:
                if api.show_friendship(source_id = api.get_user(usr).id_str,target_id = api.get_user(usr2).id_str)[0].following == True:
                    new_connections.append((api.get_user(usr).screen_name,api.get_user(usr2).screen_name))
            except:
                print('Private user')
        print('next_usr')
    f = open(filename,"a")
    for x in new_connections:
        f.write(x[0] + " , " + x[1] + "\n")
    return
    
def save(dict_que, layers,filename):
    """ 
    :param dict_que: dictionary with all the edges saved by crawler
    :param layers: number of levels
    :param filename: name of the file to save
    :return: the function does not return any parameter.
    """
    f = open(filename,"w")
    for x in dict_que['ly']:
        f.write(x[1] + " , " + x[0] + "\n")
    if layers >= 2:
        for dif_seed in dict_que['ly2']:
            for x in dif_seed:
                f.write(x[1] + " , " + x[0] + "\n")
    if layers >= 3:
        for dif_seed in dict_que['ly3']:
            for x in dif_seed:
                f.write(x[1] + " , " + x[0] + "\n")
    print("...saved...")
    return

def export_edges_to_graph(file_name):
    '''
    :param file_name: name of the txt file that contains the edges of the graf.
    :return: the function does not return any parameter.
    '''
    path = os.path.dirname(file_name)
    aux_arests,nodes,arests = [],[],[]
    
    with open(os.path.join(path, './' + file_name), 'r', encoding='cp1252') as f1:
        for line in f1:
            aux_arests.append(line.split())

    for line in aux_arests:
        arests.append((line[0], line[2]))
        nodes.append(line[0])
        nodes.append(line[2])
        
    nodes = list(set(nodes))   
    G = nx.DiGraph()
    G.add_nodes_from(nodes)
    G.add_edges_from(arests)
    nx.draw(G, with_labels = True)
    plt.show()
    nx.write_gpickle(G, file_name[:-4]+".pickle")
    
    return(G)

def export_graph_to_gexf(g, file_name):
    '''
    :param g: A graph with the corresponding networkx format.
    :param file_name: name of the file that will be saved.
    :return: the function does not return any parameter.
    '''
    nx.gexf.write_gexf(g, file_name+".gexf")
    return


def retrieve_bidirectional_edges(graph, file_name): ## 2
    '''
    :param graph: A graph with the corresponding networkx format.
    :param file_name: name of the file that will be saved.
    :return: the function does not return any parameter.
    '''
    graph2 = nx.DiGraph.to_undirected(graph,True)
    graph2.remove_nodes_from(list(nx.isolates(graph2)))
    nx.write_gpickle(graph2, file_name+".pickle")
    return graph2

def prune_low_degree_nodes(g, file_name ,min_degree = 2): ## 2
    #eliminar nodes mes petits min_degree
    '''
    :param g: A graph with the corresponding networkx format.
    :param min_degree: lower bound value for the degree
    :param file_name: name of the file that will be saved.
    :return: the function does not return any parameter.
    '''
    graph = g.copy()
    for n in g.nodes:
        if g.degree[n] <= 2:
            graph.remove_node(n)
    nx.write_gpickle(graph, file_name+".pickle")
    return graph

def info_part2(graph):
    print(type(graph))
    print('Order of '+str(graph.order()))
    print('Size of '+str(graph.size()))
    if type(graph) == nx.classes.digraph.DiGraph:
        print('Mean In degree '+str(sum([x[1] for x in graph.in_degree])/len(graph.in_degree)))
        print('Mean Out degree '+str(sum([x[1] for x in graph.out_degree])/len(graph.out_degree)))
    else:
        print('Mean of '+str(sum([x[1] for x in graph.degree])/len(graph.degree)))
    return graph
"""

-- PART 3 --

"""
def find_cliques(g, min_size_clique): ## 3
    '''

    :param g: A graph with the corresponding networkx format.
    :param min_size_clique: the minimum size of the clique returned
    :return:
        large_cliques: a list with the large cliques
        nodes_in_large_cliques: all different nodes apprearing on these cliques
    '''
    """
    El graf no ha se ser dirigit, per tant si entra un graf dirigit
    utilitzem la funcio retrieve_bidirectional_edges que genera un graf
    no dirigit que consta de les arestes i nodes del original que poden
    formar cliques.
    """
    large_cliques =[]
    nodes_in_large_cliques = []
    
    #Actualitzem el graf donat a un no dirigit
    if nx.is_directed(g):
        g = retrieve_bidirectional_edges(g)
    
        
    iterador_cliques = nx.enumerate_all_cliques(g) #Generem un iterador de totes les cliques del graf
    accepta = False #Quan aquest parametresigui True ja no comprovarem la mida (el generador les genera en ordre)
    if min_size_clique == 0:
        accepta = True
        
    for i in iterador_cliques:
        if accepta:
            large_cliques.append(i)
            for node in i:
                if node not in nodes_in_large_cliques:
                    nodes_in_large_cliques.append(node)
        elif len(i) == min_size_clique:
            accepta = True
            large_cliques.append(i)
            nodes_in_large_cliques += i
        
    

    return large_cliques, nodes_in_large_cliques

def find_max_k_core(g): ## 3
    '''

    :param g: A graph with the corresponding networkx format.
    :return: The k-core with a maximum k value.
    '''
    '''
    La funció del modul networkx, k_core retorna el maxim k-core
    diferent de 0 si no s'expecifica el valor de la k.
    '''

    return nx.k_core(g)

def load_pickle(filename):
    '''
    :param filename: El cami d'on esta guardat el fitxer pickle
    :return: La data guardad en e pickel
    
    '''
    file = open(filename, 'rb')
    data = pickle.load(file)
    file.close()
    return data

def get_best_communicators(g): #3, Q2
    '''
    
    :param g: A graph with the corresponding networkx format.
    :return: list of the nodes that are connected to more different nodes
    
    '''
    list_nodes = []
    
    graus = list(g.degree) #Llista de tots els nodes i els seus graus
    connectats = []
    for j in range(5):
        grau_max = 0
        node_max = ''
        if j == 0:
            for n in graus:
                if n[1] > grau_max:
                    grau_max = n[1]
                    node_max = n[0]
            list_nodes.append(node_max)
            connectats.append(node_max)
            connectats += list(nx.neighbors(g, node_max))
            graus.remove((node_max, grau_max))
        else:
            for n in graus:
                aux_veins = list(nx.neighbors(g, n[0]))
                aux = [x for x in aux_veins if x not in connectats]
                if len(aux) > grau_max:
                    grau_max = n[1]
                    node_max = n[0]
            list_nodes.append(node_max)
            connectats.append(node_max)
            connectats += list(nx.neighbors(g, node_max))
            graus.remove((node_max, grau_max))

    return list_nodes

def get_cliques(g, min_size_clique): #3, Q3
    '''
    :param g: A graph with the corresponding networkx format.
    :param min_size_clique: Tamany minim que tindran les cliques (s'han de generar minim 10 cliques)
    :return: Llista amb totes les cliques obtenies i tot els nodes inclosos.
    
    '''
    '''
    Utilitzem la funció ja cread find_cliques
    '''
    cliques, nodes = find_cliques(g, min_size_clique)
    while len(cliques) < 10:
        min_size_clique -= 1
        print('Es demanen minim 10 cliques, per tant el valor minim pasar a ser', min_size_clique)
        cliques, nodes = find_cliques(g, min_size_clique)
    
    return cliques, nodes

def get_max_clique(g): #3, Q4
    '''
    :param g: A graph with the corresponding networkx format.
    :return: Una de les cliques maximes.
    
    '''
    iterador = nx.find_cliques(g) # Crea un iterador de les cliques maximes
    
    for i in iterador:
        return i # Com nomes volem analitzar els comptes d'una de les cliques maximes returnem la primera. 
    
def get_kcore_info(g): #3, Q5
    '''
    :param g: A graph with the corresponding networkx format.
    :return: Info que es demana sobre el maxim k-core.
    Aquesta infromacio es el valor de k, orde i mida del k-core.
    
    '''
    g_max = find_max_k_core(g)
    '''
    La funcio creada anteriorment find_max_k_core ens retorn el graf que conte el 
    maxim k-core.
    Per tant analitzem aquest graf i obtindrem la informacio desitjada.
    
    '''
    graus = list(g_max.degree)
    k = min([x[1] for x in graus])
    ordre = g_max.order()
    mida = g_max.size()
    print('El valor de la k es:,', k)
    print('La mida del maxim k-core es:', mida)
    print("L'ordre del maxim k-core es:", ordre)

def random_walk(G, n): #Explicat al pdf
    walks_max = n
    llista = []
    nom = list(G.nodes())[random.randrange(G.order())]
    print(nom)
    while walks_max > 0:
        walks_max-=1
        aux = list(G[nom])
        nom = aux[random.randrange(G.degree()[nom])]
        llista.append(nom)
    return sorted([(llista.count(i),i) for i in set(llista)],reverse = True)
    
def is_bot(name): #Explicat al pdf
    points = 0
    object_name = api.get_user(name)
    if object_name.protected == True:
        return 'We suppose all protected users are not bots'
    elif object_name.verified == True:
        return 'We suppose verefied users are not bots'
    if object_name.default_profile == True and object_name.default_profile_image == True:
        points += 2
    if object_name.friends_count < 10:
        points += 1
    if object_name.has_extended_profile == False:
        points += 1
    if object_name.description == '':
        points += 1
    return 'is a bot by the probability of '+str((points*20)/100) 


    
"""
g = export_edges_to_graph("CDRCatOficial_150.txt")
g2 = retrieve_bidirectional_edges(g,"CDRCatOficial_150undirected")
g3 = prune_low_degree_nodes(g2,"CDRCatOficial_150undirected_reduced")
info_part2(g)
info_part2(g2)
info_part2(g3)
export_graph_to_gexf(g,"CDRCatOficial_150")
export_graph_to_gexf(g2,"CDRCatOficial_150undirected")
export_graph_to_gexf(g3,"CDRCatOficial_150undirected_reduced")
"""