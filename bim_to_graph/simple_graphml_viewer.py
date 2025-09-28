# This is a simple GraphML viewer for visualizing the graph representation of Electrical Equipment elements in a BIM model.
# It uses the python Panel library as a UI
# It loads a GraphML file and displays the graph using NetworkX and Plotly

import panel as pn
import networkx as nx
import plotly.graph_objs as go
from io import BytesIO

pn.extension('plotly')

def plot_graph(G, name_id_toggle):
    pos = nx.spring_layout(G)
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color='#888'),
        hoverinfo='none',
        mode='lines')

    node_x = []
    node_y = []
    node_text = []
    node_hover = []
    for node in G.nodes(data=True):
        n, attrs = node
        x, y = pos[n]
        node_x.append(x)
        node_y.append(y)
        if name_id_toggle and 'name' in attrs:
            node_text.append(str(attrs['name']))
        else:
            node_text.append(str(n))
        # Prepare hover text with all node parameters
        if attrs:
            hover = "<br>".join(f"{k}: {v}" for k, v in attrs.items())
        else:
            hover = str(n)
        node_hover.append(hover)
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=node_text,
        textposition='top center',
        marker=dict(
            showscale=False,
            color='#1f77b4',
            size=12,
            line_width=2),
        hoverinfo='text',
        hovertext=node_hover
    )

    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20,l=5,r=5,t=40),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))
    return fig

def load_and_plot_graphml(file_obj, name_id_toggle):
	try:
		G = nx.read_graphml(BytesIO(file_obj))
		return pn.pane.Plotly(plot_graph(G, name_id_toggle), config={'responsive': True}, sizing_mode='stretch_both')
	except Exception as e:
		return pn.pane.Markdown(f"**Error loading GraphML:** {e}")

file_input = pn.widgets.FileInput(accept='.graphml')
name_id_toggle = pn.widgets.Checkbox(name='Show Node Names', value=True)
output = pn.bind(lambda file: load_and_plot_graphml(file, name_id_toggle.value) if file else pn.pane.Markdown('Upload a .graphml file.'), file_input)

app = pn.Column(
	"# Simple GraphML Viewer",
	pn.pane.Markdown("Upload a GraphML file to visualize the graph."),
	file_input,
    name_id_toggle,
	output,
	sizing_mode='stretch_both'
)

app.servable()