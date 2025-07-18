# This is a Panel application that allows users to visualize and interact with a graph based on a GraphML xlmns file.
# It provides functionalities to load a graph, display it, and interact with its nodes and edges.

import panel as pn
from panel import widgets
import io
import networkx as nx
import plotly.graph_objects as go
import os
import pandas as pd

pn.extension('plotly')
pn.extension('jsoneditor')

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


def update_dropdowns(graph):
    node_names = list(graph.nodes())
    edge_names = [f"{u} - {v}" for u, v in graph.edges()]
    node_dropdown.options = node_names
    edge_dropdown.options = edge_names
    # Set values only after both options are set
    if node_names:
        node_dropdown.value = node_names[0]
        update_node_info(node_names[0], graph)
    else:
        node_dropdown.value = None
        node_info_pane.object = "No nodes available."
    if edge_names:
        edge_dropdown.value = edge_names[0]
        # Directly update info pane instead of calling callback
        edge_str = edge_names[0]
        if edge_str and " - " in edge_str:
            u, v = edge_str.split(" - ", 1)
            edge_tuple = (u, v)
            if edge_tuple in graph.edges:
                attrs = graph.edges[edge_tuple]
                info = f"**Edge:** {edge_tuple}"
                edge_info_pane.object = info
                # Display attributes as editable table
                if attrs:
                    df = pd.DataFrame(list(attrs.items()), columns=["Attribute", "Value"])
                    df = df[["Attribute", "Value"]]
                    edge_attr_df.value = df.copy()
                else:
                    edge_attr_df.value = pd.DataFrame(columns=["Attribute", "Value"])
            else:
                edge_info_pane.object = "No edge selected."
                edge_attr_df.value = pd.DataFrame(columns=["Attribute", "Value"])
        else:
            edge_info_pane.object = "No edge selected."
            edge_attr_df.value = pd.DataFrame(columns=["Attribute", "Value"])
    else:
        edge_dropdown.value = None
        edge_info_pane.object = "No edges available."
        edge_attr_df.value = pd.DataFrame(columns=["Attribute", "Value"])

def update_node_info(node, graph):
    if node is not None and node in graph.nodes:
        attrs = graph.nodes[node]
        info = f"**Node:** {node}"
        node_info_pane.object = info
        # Display attributes as editable table
        if attrs:
            df = pd.DataFrame(list(attrs.items()), columns=["Attribute", "Value"])
            # Ensure only 'Attribute' and 'Value' columns are present
            df = df[["Attribute", "Value"]]
            node_attr_df.value = df.copy()
        else:
            node_attr_df.value = pd.DataFrame(columns=["Attribute", "Value"])
    else:
        node_info_pane.object = "No node selected."
        node_attr_df.value = pd.DataFrame(columns=["Attribute", "Value"])

def node_dropdown_callback(event):
    if current_graph[0] is not None:
        update_node_info(event.new, current_graph[0])

def edge_dropdown_callback(event):
    if current_graph[0] is not None:
        edge_str = event.new
        if edge_str and " - " in edge_str:
            u, v = edge_str.split(" - ", 1)
            edge_tuple = (u, v)
            if edge_tuple in current_graph[0].edges:
                attrs = current_graph[0].edges[edge_tuple]
                info = f"**Edge:** {edge_tuple}"
                edge_info_pane.object = info
                # Display attributes as editable table
                if attrs:
                    df = pd.DataFrame(list(attrs.items()), columns=["Attribute", "Value"])
                    df = df[["Attribute", "Value"]]
                    edge_attr_df.value = df.copy()
                else:
                    edge_attr_df.value = pd.DataFrame(columns=["Attribute", "Value"])
            else:
                edge_info_pane.object = "No edge selected."
                edge_attr_df.value = pd.DataFrame(columns=["Attribute", "Value"])
        else:
            edge_info_pane.object = "No edge selected."
            edge_attr_df.value = pd.DataFrame(columns=["Attribute", "Value"])
    else:
        edge_info_pane.object = "No graph loaded."
        edge_attr_df.value = pd.DataFrame(columns=["Attribute", "Value"])


def file_input_callback(event):
    if file_input.value is not None:
        try:
            file_bytes = io.BytesIO(file_input.value)
            G = nx.read_graphml(file_bytes)
            fig = visualize_graph_two_d(G)
            plot_pane.object = fig
            current_graph[0] = G
            update_dropdowns(G)
        except Exception as e:
            plot_pane.object = None
            node_dropdown.options = []
            edge_dropdown.options = []
            node_info_pane.object = "Failed to load graph."
            edge_info_pane.object = "Failed to load graph."
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
                current_graph[0] = G
                update_dropdowns(G)
        except Exception as e:
            plot_pane.object = None
            three_d_pane.object = None
            node_dropdown.options = []
            edge_dropdown.options = []
            node_info_pane.object = "Failed to autoload graph."
            edge_info_pane.object = "Failed to autoload graph."
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
    sizing_mode='stretch_width'
))


# Node selection dropdown and info
selection_table_height = 400
node_dropdown = pn.widgets.Select(name="Select Node", options=[])
node_info_pane = pn.pane.Markdown("No node selected.")
# Editable DataFrame for node attributes
node_attr_df = pn.widgets.DataFrame(
    pd.DataFrame(columns=["Attribute", "Value"]),
    editors={
        "Attribute": None,
        "Value": {
            "type": "string",
            "x": "float",
            "y": "float",
            "z": "float"
        }
    },
    height=selection_table_height,
    show_index=False,
)
current_graph = [None]  # Mutable container for current graph

def node_attr_df_callback(event):
    node = node_dropdown.value
    if node and current_graph[0] is not None:
        # Convert DataFrame to dict and update node attributes
        df = event.new
        attrs = dict(zip(df["Attribute"], df["Value"]))
        for k, v in attrs.items():
            # Cast x, y, z to float if possible
            if k in ["x", "y", "z"]:
                try:
                    current_graph[0].nodes[node][k] = float(v)
                except Exception:
                    current_graph[0].nodes[node][k] = v
            else:
                current_graph[0].nodes[node][k] = v
        # Refresh visualizations after node attribute edit
        plot_pane.object = visualize_graph_two_d(current_graph[0])
        three_d_pane.object = visualize_graph_three_d(current_graph[0])
node_attr_df.param.watch(node_attr_df_callback, 'value')
node_dropdown.param.watch(node_dropdown_callback, 'value')

# Add a dropdown for selecting an edge from the graph
edge_dropdown = pn.widgets.Select(name="Select Edge", options=[])
edge_info_pane = pn.pane.Markdown("No edge selected.")
edge_dropdown.param.watch(edge_dropdown_callback, 'value')

# Editable DataFrame for edge attributes
edge_attr_df = pn.widgets.DataFrame(
    pd.DataFrame(columns=["Attribute", "Value"]),
    editors={"Attribute": None, "Value": "string"},
    height=selection_table_height,
    show_index=False,
)

def edge_attr_df_callback(event):
    edge_str = edge_dropdown.value
    if edge_str and current_graph[0] is not None and " - " in edge_str:
        u, v = edge_str.split(" - ", 1)
        edge_tuple = (u, v)
        if edge_tuple in current_graph[0].edges:
            df = event.new
            attrs = dict(zip(df["Attribute"], df["Value"]))
            for k, v in attrs.items():
                current_graph[0].edges[edge_tuple][k] = v
            # Refresh visualizations after edge attribute edit
            plot_pane.object = visualize_graph_two_d(current_graph[0])
            three_d_pane.object = visualize_graph_three_d(current_graph[0])
edge_attr_df.param.watch(edge_attr_df_callback, 'value')

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

node_column = pn.Column("### Node Selection", node_dropdown, node_info_pane, node_attr_df, sizing_mode='stretch_width')

edge_column = pn.Column("### Edge Selection", edge_dropdown, edge_info_pane, edge_attr_df, sizing_mode='stretch_width')

# Create a row for selections
selection_row = pn.Row(node_column, edge_column, sizing_mode='stretch_width')
app.append(selection_row)


# --- Save Graph UI ---
import datetime

def get_default_filename():
    today = datetime.datetime.now().strftime('%y%m%d')
    return f"{today}_graph.mepg"

filename_input = pn.widgets.TextInput(name="Save As Filename", value=get_default_filename())
save_button = pn.widgets.Button(name="Save Graph", button_type="primary")
save_status = pn.pane.Markdown(visible=False)

def save_graph_callback(event):
    if current_graph[0] is not None:
        fname = filename_input.value.strip()
        if not fname:
            fname = get_default_filename()
        # Ensure .mepg extension
        if not fname.lower().endswith('.mepg'):
            fname += '.mepg'
        # Ensure graph_outputs folder exists
        output_dir = 'graph_outputs'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        out_path = os.path.join(output_dir, fname)
        try:
            current_graph[0].graph["source"] = "Panel Graph Viewer Export"
            nx.write_graphml(current_graph[0], out_path)
            save_status.object = f"**Graph saved to `{out_path}`**"
            save_status.visible = True
        except Exception as e:
            save_status.object = f"**Error saving graph:** {e}"
            save_status.visible = True
    else:
        save_status.object = "**No graph loaded to save.**"
        save_status.visible = True

save_button.on_click(save_graph_callback)

save_row = pn.Row(filename_input, save_button)
app.append(pn.Column("### Save Graph", save_row, save_status, sizing_mode='stretch_width'))

print("Starting MEP System Graph Viewer...")
app.servable()
