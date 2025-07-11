# This is a Panel application that allows users to visualize and interact with a graph based on a GraphML xlmns file.
# It provides functionalities to load a graph, display it, and interact with its nodes and edges.

import panel as pn
from panel import widgets
import io
import networkx as nx
import plotly.graph_objects as go
import os

pn.extension('plotly')

def visualize_graph_two_d(graph):
    pos = nx.spring_layout(graph)
    edge_x = []
    edge_y = []
    edge_text = []
    edge_marker_x = []
    edge_marker_y = []
    edge_marker_text = []
    for edge in graph.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]
        # Create hover text for edges with all edge attributes
        hover_text = f"{edge[0]} - {edge[1]}"
        edge_attrs = graph.edges[edge]
        if edge_attrs:
            hover_text += "<br>" + "<br>".join([f"{k}: {v}" for k, v in edge_attrs.items()])
        # Repeat hover_text for both endpoints, None for separator
        edge_text += [hover_text, hover_text, None]
        # Add invisible marker at edge midpoint for better hover
        edge_marker_x.append((x0 + x1) / 2)
        edge_marker_y.append((y0 + y1) / 2)
        edge_marker_text.append(hover_text)
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=3, color='#888'),  # Thicker line
        hoverinfo='text',
        mode='lines',
        hovertext=edge_text
    )
    edge_marker_trace = go.Scatter(
        x=edge_marker_x, y=edge_marker_y,
        mode='markers',
        marker=dict(size=10, color='rgba(0,0,0,0)'),  # Invisible
        hoverinfo='text',
        hovertext=edge_marker_text,
        showlegend=False
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

    fig = go.Figure(data=[edge_trace, edge_marker_trace, node_trace],
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
    edge_marker_x = []
    edge_marker_y = []
    edge_marker_z = []
    edge_marker_text = []
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
        # Add invisible marker at edge midpoint for better hover
        edge_marker_x.append((x0 + x1) / 2)
        edge_marker_y.append((y0 + y1) / 2)
        edge_marker_z.append((z0 + z1) / 2)
        hover_text = f"{edge[0]} - {edge[1]}"
        edge_attrs = graph.edges[edge]
        if edge_attrs:
            hover_text += "<br>" + "<br>".join([f"{k}: {v}" for k, v in edge_attrs.items()])
        edge_marker_text.append(hover_text)
    edge_trace = go.Scatter3d(
        x=edge_x, y=edge_y, z=edge_z,
        line=dict(width=2, color='#888'),
        hoverinfo='none',
        mode='lines'
    )
    edge_marker_trace = go.Scatter3d(
        x=edge_marker_x, y=edge_marker_y, z=edge_marker_z,
        mode='markers',
        marker=dict(size=6, color='rgba(0,0,0,0)'),  # Invisible
        hoverinfo='text',
        hovertext=edge_marker_text,
        showlegend=False
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
    fig = go.Figure(data=[edge_trace, edge_marker_trace, node_trace],
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


app = pn.Column(
    sizing_mode='stretch_width'
)

app.append(pn.pane.Markdown("""
# MEP System Graph Viewer
This application allows you to visualize and interact with MEP system graphs.
"""))

# File upload widget
file_input = pn.widgets.FileInput(accept='.mepg')
file_input.param.watch(file_input_callback, 'value')
app.append(pn.Column(
    "### Load MEP Graph File",
    file_input,
))

# Placeholder for the plot
two_d_column = pn.Column()
two_d_column.append("### 2D Graph Visualization")
plot_pane = pn.pane.Plotly(height=600, sizing_mode='stretch_width')
two_d_column.append(plot_pane)

# 3D graph visualization function
# This function takes a NetworkX graph and visualizes it using Plotly.
three_d_column = pn.Column()
three_d_column.append("### 3D Graph Visualization")
three_d_pane = pn.pane.Plotly(height=600, sizing_mode='stretch_width')
three_d_column.append(three_d_pane)

# Autoload example graph if present
autoload_example_graph()

# Create a row to show both plots side by side
plots_row = pn.Row(two_d_column, three_d_column, sizing_mode='stretch_width')

app.append(plots_row)

print("Starting MEP System Graph Viewer...")
app.servable()
