# This is a simple GraphML viewer for visualizing the graph representation of Electrical Equipment elements in a BIM model.
# It uses the python Panel library as a UI
# It loads a GraphML file and displays the graph using NetworkX and PyVis

import panel as pn
import networkx as nx
from pyvis.network import Network
from io import BytesIO
import pandas as pd
import json
import base64
import plotly.express as px

pn.extension('tabulator')

DEFAULT_FILE_PATH = "./bim_to_graph/output_graph.graphml"

def create_pyvis_graph(G, name_id_toggle=True):
    """Convert NetworkX graph to PyVis HTML"""
    
    # Create PyVis network with desired settings
    # Use explicit pixel dimensions for proper sizing
    net = Network(
        # height="400",
        # width="100%",
        directed=nx.is_directed(G),
        notebook=False,
        cdn_resources='in_line'  # Embeds all JS/CSS inline
    )
    
    # Configure physics and layout
    # Use physics-based layout for better node distribution
    net.set_options("""
    {
        "nodes": {
            "borderWidth": 2,
            "shape": "dot",
            "size": 20,
            "font": {
                "size": 14
            }
        },
        "edges": {
            "arrows": {
                "to": {
                    "enabled": true,
                    "scaleFactor": 0.5
                }
            },
            "color": {
                "color": "#888888",
                "highlight": "#1f77b4",
                "inherit": false
            },
            "smooth": {
                "type": "continuous",
                "forceDirection": "none"
            }
        },
        "interaction": {
            "hover": true,
            "keyboard": {
                "enabled": true
            },
            "navigationButtons": true,
            "tooltipDelay": 100
        },
        "physics": {
            "barnesHut": {
                "gravitationalConstant": -3000,
                "springLength": 150
            },
            "minVelocity": 0.75
        }
    }
    """)
    
    # Add nodes with labels and store full attributes as title (tooltip)
    # Build category-to-color mapping using Plotly's Alphabet palette
    categories = list(set(attrs.get('category', 'Unknown') for _, attrs in G.nodes(data=True)))
    colors = px.colors.qualitative.Alphabet
    category_color_map = {cat: colors[i % len(colors)] for i, cat in enumerate(sorted(categories))}
    
    # Define size mapping for specific categories
    category_size_map = {
        'Switchboard': 35,
        'Panelboard': 30,
        'Electrical Circuit': 25,
    }
    default_size = 20
    
    for node, attrs in G.nodes(data=True):
        label = attrs.get('name', str(node)) if name_id_toggle else str(node)
        category = attrs.get('category', 'Unknown')
        node_color = category_color_map.get(category, '#1f77b4')
        node_size = category_size_map.get(category, default_size)
        
        # Create tooltip as plain text with newlines
        tooltip_lines = [f"Node ID: {node}"]
        tooltip_lines.append("-" * 30)
        for key, value in attrs.items():
            tooltip_lines.append(f"{key}: {value}")
        tooltip = "\n".join(tooltip_lines)
        
        # Store node data as JSON for click events
        node_data = json.dumps({'id': node, **{k: str(v) for k, v in attrs.items()}})
        
        net.add_node(node, label=label, title=tooltip, node_data=node_data, color=node_color, size=node_size)
    
    # Add edges
    for u, v, attrs in G.edges(data=True):
        net.add_edge(u, v)
    
    # Generate HTML string
    html = net.generate_html()
    
    return html, category_color_map

class GraphMLViewer:
    def __init__(self):
        self.G = None
        self.selected_node_params = pn.widgets.Tabulator(
            value=pd.DataFrame({'Parameter': ['No node selected'], 'Value': ['']}),
            pagination=None,
            sizing_mode='stretch_both',
            show_index=False,
            configuration={
                'columnDefaults': {
                    'resizable': True,
                    'tooltip': True,
                },
                'layout': 'fitColumns',
                'textAlign': 'left',
                'cellVertAlign': 'top',
            },
            widths={'Parameter': '40%', 'Value': '60%'}
        )
        self.pyvis_pane = None
        
    def create_legend(self, category_color_map):
        """Create an HTML legend for the category colors"""
        legend_items = []
        for category, color in sorted(category_color_map.items()):
            legend_items.append(
                f'<div style="display:flex; align-items:center; margin:4px 0;">'
                f'<span style="display:inline-block; width:16px; height:16px; '
                f'background-color:{color}; border-radius:50%; margin-right:8px; '
                f'border:1px solid #333;"></span>'
                f'<span style="font-size:13px;">{category}</span></div>'
            )
        legend_html = f'''
        <div style="padding:10px; background:#f9f9f9; border:1px solid #ddd; border-radius:4px;">
            <div style="font-weight:bold; margin-bottom:8px; border-bottom:1px solid #ccc; padding-bottom:4px;">Category Legend</div>
            {"".join(legend_items)}
        </div>
        '''
        return pn.pane.HTML(legend_html, sizing_mode='stretch_width')
    
    def load_and_plot_graphml(self, file_obj, name_id_toggle):
        if not file_obj:
            return pn.pane.Markdown('Upload a .graphml file.')
        
        try:
            self.G = nx.read_graphml(BytesIO(file_obj))
            # Reset node parameters table
            self.selected_node_params.value = pd.DataFrame({'Parameter': ['Hover over nodes to view parameters'], 'Value': ['']})
            
            # Create the PyVis graph
            html, category_color_map = create_pyvis_graph(self.G, name_id_toggle)
            
            # Create the legend
            legend_pane = self.create_legend(category_color_map)
            
            # Encode HTML as base64 for iframe src
            html_bytes = html.encode('utf-8')
            b64_html = base64.b64encode(html_bytes).decode('utf-8')
            
            # Use iframe with data URI to embed the full PyVis HTML document
            iframe_html = f"""
            <iframe 
                src="data:text/html;base64,{b64_html}"
                style="width:100%; height:600px; border:1px solid #ddd; border-radius:4px;"
                frameborder="0">
            </iframe>
            """
            
            self.pyvis_pane = pn.pane.HTML(iframe_html, sizing_mode='stretch_width', min_height=620)
            
            return pn.Column(legend_pane, self.pyvis_pane, sizing_mode='stretch_width')
            
        except Exception as e:
            return pn.pane.Markdown(f"**Error loading GraphML:** {e}")

# Initialize the viewer
viewer = GraphMLViewer()

# Create widgets
file_input = pn.widgets.FileInput(accept='.graphml')
name_id_toggle = pn.widgets.Checkbox(name='Show Node Names', value=True)

file_input.value = open(DEFAULT_FILE_PATH, 'rb').read()

# Bind the plotting function
plot_output = pn.bind(viewer.load_and_plot_graphml, file_input, name_id_toggle)

# Create the main layout
app = pn.Row(
    pn.Column(
        "# Simple GraphML Viewer",
        pn.pane.Markdown("Upload a GraphML file to visualize the graph. Click on nodes to view their parameters."),
        file_input,
        name_id_toggle,
        plot_output,
        sizing_mode='stretch_both'
    ),
    # pn.Column(
    #     "## Node Parameters",
    #     pn.pane.Markdown("Click on a node in the graph to view its parameters here."),
    #     viewer.selected_node_params,
    #     width=550,
    #     sizing_mode='stretch_height'
    # ),
    sizing_mode='stretch_both'
)

app.servable()