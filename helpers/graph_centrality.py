# This is a python script that uses receives a networkx graph and determines the centrality measures for each node.

import networkx as nx

def calculate_centrality_measures(graph):
    """
    Calculate various centrality measures for the given graph.
    
    Parameters:
    graph (networkx.Graph): The input graph.
    
    Returns:
    dict: A dictionary containing centrality measures for each node.
    """
    centrality_measures = {
        'degree_centrality': nx.degree_centrality(graph),
        'betweenness_centrality': nx.betweenness_centrality(graph),
        'closeness_centrality': nx.closeness_centrality(graph),
        'eigenvector_centrality': nx.eigenvector_centrality(graph, max_iter=1000)
    }
    
    return centrality_measures