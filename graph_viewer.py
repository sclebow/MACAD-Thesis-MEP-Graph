# This is a Panel application that allows users to visualize and interact with a graph based on a GraphML xlmns file.
# It provides functionalities to load a graph, display it, and interact with its nodes and edges.

import panel as pn
from panel import widgets
import io
import networkx as nx
import plotly.graph_objects as go
import os

pn.extension('plotly')

# File upload widget
file_input = pn.widgets.FileInput(accept='.mepg')

# Placeholder for the plot
plot_pane = pn.pane.Plotly(height=600, sizing_mode='stretch_width')

# 3D graph visualization function
# This function takes a NetworkX graph and visualizes it using Plotly.
three_d_pane = pn.pane.Plotly(height=600, sizing_mode='stretch_width')

def visualize_graph_two_d(graph):
    pos = nx.spring_layout(graph)
    edge_x = []
    edge_y = []
    for edge in graph.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color='#888'),
        hoverinfo='none',
        mode='lines'
    )

    node_x = []
    node_y = []
    names = []
    node_text = []
    for node, attrs in graph.nodes(data=True):
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        names.append(node)
        hover = f"{node}<br>" + "<br>".join([f"{k}: {v}" for k, v in attrs.items()])
        node_text.append(hover)
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=names,  # Show node name as label
        textposition="top center",
        hoverinfo='text',
        marker=dict(
            showscale=False,
            color='blue',
            size=15,
            line_width=2
        ),
        hovertext=node_text  # Show all attributes on hover
    )

    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20,l=5,r=5,t=40),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                    ))
    
    return fig

def visualize_graph_three_d(graph):
    """
    Visualizes a NetworkX graph in 3D using Plotly.
    Uses the x, y, z coordinates of nodes for 3D positioning.
    """
    pos = nx.spring_layout(graph, dim=3)

    node_x = []
    node_y = []
    node_z = []
    names = []
    node_text = []
    for node, attrs in graph.nodes(data=True):
        # Get the 'x', 'y', 'z' attributes from the node
        print(attrs)
        x = attrs.get('x', 0)
        y = attrs.get('y', 0)
        z = attrs.get('z', 0)

        node_x.append(x)
        node_y.append(y)
        node_z.append(z)
        names.append(node)
        hover = f"{node}<br>" + "<br>".join([f"{k}: {v}" for k, v in attrs.items()])
        node_text.append(hover)

    edge_x = []
    edge_y = []
    edge_z = []
    for edge in graph.edges():
        x0 = graph.nodes[edge[0]].get('x', 0)
        y0 = graph.nodes[edge[0]].get('y', 0)
        z0 = graph.nodes[edge[0]].get('z', 0)
        x1 = graph.nodes[edge[1]].get('x', 0)
        y1 = graph.nodes[edge[1]].get('y', 0)
        z1 = graph.nodes[edge[1]].get('z', 0)
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]
        edge_z += [z0, z1, None]
    edge_trace = go.Scatter3d(
        x=edge_x, y=edge_y, z=edge_z,
        line=dict(width=1, color='#888'),
        hoverinfo='none',
        mode='lines'
    )

    node_trace = go.Scatter3d(
        x=node_x, y=node_y, z=node_z,
        mode='markers+text',
        text=names,  # Show node name as label
        textposition="top center",
        hoverinfo='text',
        marker=dict(
            showscale=False,
            color='blue',
            size=5,
            line_width=2
        ),
        hovertext=node_text  # Show all attributes on hover
    )

    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20,l=5,r=5,t=40),
                        scene=dict(
                            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                            zaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                        )
                    ))

    return fig

def file_input_callback(event):
    if file_input.value is not None:
        try:
            file_bytes = io.BytesIO(file_input.value)
            G = nx.read_graphml(file_bytes)
            fig = visualize_graph_two_d(G)
            plot_pane.object = fig
        except Exception as e:
            plot_pane.object = None
            pn.state.notifications.error(f"Failed to load graph: {e}")

file_input.param.watch(file_input_callback, 'value')

def autoload_example_graph():
    example_path = 'example_graph.mepg'
    if os.path.exists(example_path):
        try:
            with open(example_path, 'rb') as f:
                G = nx.read_graphml(f)
                fig = visualize_graph_two_d(G)
                plot_pane.object = fig
                three_d_fig = visualize_graph_three_d(G)
                three_d_pane.object = three_d_fig
        except Exception as e:
            plot_pane.object = None
            three_d_pane.object = None
            print(f"Failed to autoload example graph: {e}")

# Autoload example graph if present
autoload_example_graph()

app = pn.Column(
    "# GraphML Viewer",
    "Upload a GraphML file to visualize the graph.",
    file_input,
    plot_pane,
    three_d_pane,
    sizing_mode='stretch_width'
)

print("Starting GraphML Viewer...")
app.servable()
