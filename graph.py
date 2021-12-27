import networkx as nx
import os
import sqlite3

mainName = 'JanPaweł'

def createGraph(path):
    con = sqlite3.connect(os.path.join(path,f'{path}.db'))

    nodes = set()
    edges = set()
    print('Adding')
    for row in con.execute('select Child, Parent from relations'):
        edges.add(row)
        nodes.add(row[0])
        nodes.add(row[1])

    con.close()
    # print(nodes)
    print('Set full')

    G = nx.DiGraph()
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)
    print(G)

    nx.write_gexf(G,os.path.join(path,f'{path}.gexf'))

if __name__ == '__main__':
    createGraph()