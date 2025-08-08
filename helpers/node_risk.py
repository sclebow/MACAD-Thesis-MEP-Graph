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

    # New risk score: (propagated_power / total_load + betweenness_centrality) / 2
    if not isinstance(graph, nx.DiGraph):
        raise ValueError("The graph must be a directed graph.")

    # Calculate total load (sum of all node loads)
    total_load = sum(graph.nodes[n].get('propagated_power') for n in graph.nodes)
    if total_load == 0:
        total_load = 1  # Prevent division by zero

    risk_scores = {}
    # Helper to count descendants excluding 'end_load' nodes
    def filtered_descendants_count(graph, node):
        descendants = nx.descendants(graph, node)
        filtered = [n for n in descendants if graph.nodes[n].get('type') != 'end_load']
        return len(filtered)

    # Compute max filtered descendants for normalization
    max_descendants = max(filtered_descendants_count(graph, n) for n in graph.nodes) if graph.nodes else 1
    if max_descendants == 0:
        max_descendants = 1

    for node in graph.nodes:
        propagated_power = graph.nodes[node].get('propagated_power')
        norm_power = propagated_power / total_load
        descendants_count = filtered_descendants_count(graph, node)
        norm_descendants = descendants_count / max_descendants
        risk = (norm_power + norm_descendants) / 2
        risk_scores[node] = risk

    # Normalize so the highest risk is 1
    max_risk = max(risk_scores.values()) if risk_scores else 1
    if max_risk == 0:
        max_risk = 1
    normalized_scores = {node: score / max_risk for node, score in risk_scores.items()}
    return normalized_scores
    
def apply_risk_scores_to_graph(graph):
    """
    Apply risk scores to the graph nodes as attributes.

    Parameters:
    graph (networkx.DiGraph): The input directed graph.
    """
    try:
        if not isinstance(graph, nx.DiGraph):
            raise ValueError("The graph must be a directed graph.")

        risk_scores = calculate_risk_scores(graph)
        for node, score in risk_scores.items():
            graph.nodes[node]['risk_score'] = score

    except Exception as e:
        # Apply a default risk score if calculation fails
        print(f"Error calculating risk scores: {e}")
        default_score = 0
        for node in graph.nodes:
            graph.nodes[node]['risk_score'] = default_score

    return graph
