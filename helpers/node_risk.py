# This is a python script that uses receives a networkx directed graph and determines the risk score of each node

import networkx as nx

def calculate_risk_scores(graph):
    """
    Calculate risk scores for each node in the directed graph based on its attributes.

    Parameters:
    graph (networkx.DiGraph): The input directed graph.

    Returns:
    dict: A dictionary mapping each node to its risk score.
    """

    # Risk score based on downstream reachability and strong articulation points
    if not isinstance(graph, nx.DiGraph):
        raise ValueError("The graph must be a directed graph.")

    risk_scores = {}

    # 1. Find strong articulation points (nodes whose removal increases the number of strongly connected components)
    try:
        strong_articulation_points = set(nx.algorithms.connectivity.strongly_connected.strong_articulation_points(graph))
    except Exception:
        # Fallback if not available in older networkx versions
        strong_articulation_points = set()

    # 2. For each node, calculate the number of downstream nodes (descendants)
    for node in graph.nodes:
        # Remove node and count how many nodes become unreachable from its predecessors
        descendants = nx.descendants(graph, node)
        # Risk score: number of downstream nodes disconnected if this node fails
        risk = len(descendants)
        # Boost risk score if node is a strong articulation point
        if node in strong_articulation_points:
            risk += len(graph.nodes)  # Add a large penalty/bonus
        risk_scores[node] = risk

    return risk_scores
    
def apply_risk_scores_to_graph(graph):
    """
    Apply risk scores to the graph nodes as attributes.

    Parameters:
    graph (networkx.DiGraph): The input directed graph.
    """
    if not isinstance(graph, nx.DiGraph):
        raise ValueError("The graph must be a directed graph.")

    risk_scores = calculate_risk_scores(graph)
    for node, score in risk_scores.items():
        graph.nodes[node]['risk_score'] = score

    return graph
