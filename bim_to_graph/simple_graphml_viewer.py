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
import math

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

pn.extension('tabulator', notifications=True)

DEFAULT_FILE_PATH = "./bim_to_graph/output_graph.graphml"

def layout_with_disconnected_components(G, k=2, iterations=200, scale=5000):
    """
    Layout graph with proper handling of disconnected components.
    Larger components are centered, smaller ones are positioned around the periphery.
    """
    # Get connected components (use weakly_connected for directed graphs)
    if nx.is_directed(G):
        components = list(nx.weakly_connected_components(G))
    else:
        components = list(nx.connected_components(G))
    
    # If only one component or empty, use standard layout
    if len(components) <= 1:
        return nx.spring_layout(G, k=k, iterations=iterations, scale=scale)
    
    # Sort components by size (largest first)
    components = sorted(components, key=len, reverse=True)
    
    pos = {}
    
    # Layout the largest component at the center
    largest_subgraph = G.subgraph(components[0]).copy()
    largest_pos = nx.spring_layout(largest_subgraph, k=k, iterations=iterations, scale=scale)
    pos.update(largest_pos)
    
    # Calculate bounding box of the largest component
    if largest_pos:
        x_coords = [p[0] for p in largest_pos.values()]
        y_coords = [p[1] for p in largest_pos.values()]
        max_extent = max(max(x_coords) - min(x_coords), max(y_coords) - min(y_coords))
    else:
        max_extent = scale
    
    # Position smaller components around the periphery
    num_small = len(components) - 1
    
    for i, component in enumerate(components[1:], start=1):
        subgraph = G.subgraph(component).copy()
        
        # Scale smaller components based on their relative size
        component_scale = scale * (len(component) / len(components[0])) ** 0.5
        component_scale = max(component_scale, scale * 0.2)  # Minimum scale
        
        # Layout this component
        sub_pos = nx.spring_layout(subgraph, k=k, iterations=iterations, scale=component_scale)
        
        # Calculate offset angle and distance to place this component
        angle = (2 * math.pi * (i - 1)) / num_small
        # Distance from center: beyond the largest component + buffer
        offset_distance = max_extent * 0.7 + component_scale * 1.5
        
        offset_x = offset_distance * math.cos(angle)
        offset_y = offset_distance * math.sin(angle)
        
        # Apply offset to all nodes in this component
        for node, (x, y) in sub_pos.items():
            pos[node] = (x + offset_x, y + offset_y)
    
    return pos

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
    # Use physics-based layout with fast stabilization, then disable physics
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
                "enabled": true,
                "type": "dynamic"
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
            "enabled": true,
            "barnesHut": {
                "gravitationalConstant": -2000,
                "springLength": 100,
                "springConstant": 0.04,
                "damping": 0.5
            },
            "stabilization": {
                "enabled": true,
                "iterations": 50,
                "fit": true
            }
        }
    }
    """)
    
    # Pre-compute node positions using NetworkX spring layout
    # This is much faster than letting vis.js compute it
    # Handle disconnected subgraphs by laying them out separately
    pos = layout_with_disconnected_components(G, k=2, iterations=200, scale=5000)
    
    # Add nodes with labels and store full attributes as title (tooltip)
    # Build category-to-color mapping using Plotly's Alphabet palette
    categories = list(set(attrs.get('category', 'Unknown') for _, attrs in G.nodes(data=True)))
    colors = px.colors.qualitative.Alphabet
    category_color_map = {cat: colors[i % len(colors)] for i, cat in enumerate(sorted(categories))}
    
    # Define size mapping for specific categories
    category_size_map = {
        'Electrical Equipment': 35,
        'Electrical Circuit': 25,
    }
    default_size = 20
    
    for node, attrs in G.nodes(data=True):
        label = attrs.get('name', str(node)) if name_id_toggle else str(node)
        category = attrs.get('category', 'Unknown')
        node_color = category_color_map.get(category, '#1f77b4')
        node_size = category_size_map.get(category, default_size)
        
        # Get pre-computed position
        x, y = pos[node]
        
        # Create tooltip as plain text with newlines
        tooltip_lines = [f"Node ID: {node}"]
        tooltip_lines.append("-" * 30)
        for key, value in attrs.items():
            tooltip_lines.append(f"{key}: {value}")
        tooltip = "\n".join(tooltip_lines)
        
        # Store node data as JSON for click events
        node_data = json.dumps({'id': node, **{k: str(v) for k, v in attrs.items()}})
        
        net.add_node(node, label=label, title=tooltip, node_data=node_data, 
                     color=node_color, size=node_size, x=x, y=y)
    
    # Add edges
    for u, v, attrs in G.edges(data=True):
        net.add_edge(u, v)
    
    # Generate HTML string
    html = net.generate_html()
    
    return html, category_color_map

class GraphMLViewer(pn.viewable.Viewer):
    """GraphML Viewer with node click support using Panel's reactive framework"""
    
    def __init__(self):
        super().__init__()
        self.G = None
        self.node_data_cache = {}  # Cache node data by node ID
        
        # Node selector dropdown
        self.node_selector = pn.widgets.Select(
            name='Select Node',
            options={'-- Select a node --': ''},
            value='',
            sizing_mode='stretch_width'
        )
        self.node_selector.param.watch(self._on_node_selected, 'value')
        
        self.selected_node_params = pn.widgets.Tabulator(
            value=pd.DataFrame({'Parameter': ['Select a node to see details'], 'Value': ['']}),
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
        
        # Neo4j connection widgets
        self.neo4j_uri = pn.widgets.TextInput(
            name='Neo4j URI',
            value='bolt://localhost:7687',
            placeholder='bolt://localhost:7687',
            sizing_mode='stretch_width'
        )
        self.neo4j_username = pn.widgets.TextInput(
            name='Username',
            value='neo4j',
            sizing_mode='stretch_width'
        )
        self.neo4j_password = pn.widgets.PasswordInput(
            name='Password',
            placeholder='Enter password',
            sizing_mode='stretch_width'
        )
        self.neo4j_database = pn.widgets.TextInput(
            name='Database',
            value='neo4j',
            placeholder='neo4j (default)',
            sizing_mode='stretch_width'
        )
        self.neo4j_clear_existing = pn.widgets.Checkbox(
            name='Clear existing data before import',
            value=False
        )
        self.neo4j_export_button = pn.widgets.Button(
            name='Export to Neo4j',
            button_type='primary',
            sizing_mode='stretch_width',
            disabled=not NEO4J_AVAILABLE
        )
        self.neo4j_export_button.on_click(self._export_to_neo4j)
        
        self.neo4j_status = pn.pane.Alert(
            'Ready to export' if NEO4J_AVAILABLE else '⚠️ neo4j package not installed. Run: pip install neo4j',
            alert_type='info' if NEO4J_AVAILABLE else 'warning',
            sizing_mode='stretch_width'
        )
        
    def _on_node_selected(self, event):
        """Handle node selection from dropdown"""
        node_id = event.new
        if node_id and node_id in self.node_data_cache:
            node_data = self.node_data_cache[node_id]
            df = pd.DataFrame({
                'Parameter': list(node_data.keys()),
                'Value': [str(v) for v in node_data.values()]
            })
            self.selected_node_params.value = df
        
    def update_node_params_from_json(self, node_data_json):
        """Update the node parameters table from JSON string"""
        if node_data_json:
            try:
                node_data = json.loads(node_data_json)
                # Also update the dropdown selection
                node_id = node_data.get('id', '')
                if node_id in [v for v in self.node_selector.options.values()]:
                    self.node_selector.value = node_id
                df = pd.DataFrame({
                    'Parameter': list(node_data.keys()),
                    'Value': [str(v) for v in node_data.values()]
                })
                self.selected_node_params.value = df
            except json.JSONDecodeError:
                pass
    
    def _export_to_neo4j(self, event):
        """Export the current graph to Neo4j database"""
        if not NEO4J_AVAILABLE:
            self.neo4j_status.object = '❌ neo4j package not installed. Run: pip install neo4j'
            self.neo4j_status.alert_type = 'danger'
            return
        
        if self.G is None or len(self.G.nodes()) == 0:
            self.neo4j_status.object = '❌ No graph loaded. Please upload a GraphML file first.'
            self.neo4j_status.alert_type = 'warning'
            return
        
        uri = self.neo4j_uri.value.strip()
        username = self.neo4j_username.value.strip()
        password = self.neo4j_password.value
        database = self.neo4j_database.value.strip() or 'neo4j'
        clear_existing = self.neo4j_clear_existing.value
        
        if not uri or not username:
            self.neo4j_status.object = '❌ Please provide URI and username.'
            self.neo4j_status.alert_type = 'warning'
            return
        
        self.neo4j_status.object = '⏳ Connecting to Neo4j...'
        self.neo4j_status.alert_type = 'info'
        self.neo4j_export_button.disabled = True
        
        try:
            driver = GraphDatabase.driver(uri, auth=(username, password))
            
            # Test connection
            driver.verify_connectivity()
            
            with driver.session(database=database) as session:
                # Optionally clear existing data
                if clear_existing:
                    self.neo4j_status.object = '⏳ Clearing existing data...'
                    session.run("MATCH (n) DETACH DELETE n")
                
                self.neo4j_status.object = '⏳ Exporting nodes...'
                
                # Export nodes
                for node_id, attrs in self.G.nodes(data=True):
                    # Get category for label, default to 'Node'
                    category = attrs.get('category', 'Node')
                    # Clean category name for Neo4j label (remove spaces, special chars)
                    label = ''.join(c if c.isalnum() else '_' for c in category)
                    if not label or label[0].isdigit():
                        label = 'Node_' + label
                    
                    # Prepare properties
                    props = {'id': str(node_id)}
                    for key, value in attrs.items():
                        # Neo4j doesn't accept None values
                        if value is not None:
                            props[key] = str(value) if not isinstance(value, (int, float, bool)) else value
                    
                    # Create node with dynamic label
                    query = f"MERGE (n:`{label}` {{id: $id}}) SET n += $props"
                    session.run(query, id=str(node_id), props=props)
                
                self.neo4j_status.object = '⏳ Exporting edges...'
                
                # Export edges
                for u, v, attrs in self.G.edges(data=True):
                    # Get relationship type from edge attributes or default
                    rel_type = attrs.get('relationship', attrs.get('type', 'CONNECTED_TO'))
                    rel_type = ''.join(c if c.isalnum() else '_' for c in str(rel_type)).upper()
                    if not rel_type:
                        rel_type = 'CONNECTED_TO'
                    
                    # Prepare edge properties
                    edge_props = {}
                    for key, value in attrs.items():
                        if value is not None and key not in ['relationship', 'type']:
                            edge_props[key] = str(value) if not isinstance(value, (int, float, bool)) else value
                    
                    query = f"""
                    MATCH (a {{id: $source}})
                    MATCH (b {{id: $target}})
                    MERGE (a)-[r:`{rel_type}`]->(b)
                    SET r += $props
                    """
                    session.run(query, source=str(u), target=str(v), props=edge_props)
            
            driver.close()
            
            node_count = len(self.G.nodes())
            edge_count = len(self.G.edges())
            self.neo4j_status.object = f'✅ Successfully exported {node_count} nodes and {edge_count} edges to Neo4j!'
            self.neo4j_status.alert_type = 'success'
            
        except Exception as e:
            self.neo4j_status.object = f'❌ Error: {str(e)}'
            self.neo4j_status.alert_type = 'danger'
        finally:
            self.neo4j_export_button.disabled = False
        
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
            
            # Build node data cache and populate dropdown options
            self.node_data_cache = {}
            node_options = {'-- Select a node --': ''}
            for node, attrs in self.G.nodes(data=True):
                name = attrs.get('name', str(node))
                category = attrs.get('category', 'Unknown')
                label = f"{node} - {name} ({category})"
                node_options[label] = node
                self.node_data_cache[node] = {'id': node, **attrs}
            
            self.node_selector.options = node_options
            self.node_selector.value = ''
            
            # Reset node parameters table
            self.selected_node_params.value = pd.DataFrame({'Parameter': ['Select a node from the dropdown'], 'Value': ['']})
            
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
                id="pyvis-iframe"
                src="data:text/html;base64,{b64_html}"
                style="width:100%; height:600px; border:1px solid #ddd; border-radius:4px;"
                frameborder="0">
            </iframe>
            """
            
            self.pyvis_pane = pn.pane.HTML(iframe_html, sizing_mode='stretch_width', min_height=620)
            
            return pn.Column(
                legend_pane, 
                self.pyvis_pane, 
                sizing_mode='stretch_width'
            )
            
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
        pn.pane.Markdown("Upload a GraphML file to visualize the graph. Select a node from the dropdown or hover over nodes in the graph."),
        file_input,
        name_id_toggle,
        plot_output,
        sizing_mode='stretch_both'
    ),
    pn.Column(
        "## Node Parameters",
        viewer.node_selector,
        viewer.selected_node_params,
        pn.layout.Divider(),
        "## Export to Neo4j",
        viewer.neo4j_uri,
        pn.Row(viewer.neo4j_username, viewer.neo4j_password, sizing_mode='stretch_width'),
        viewer.neo4j_database,
        viewer.neo4j_clear_existing,
        viewer.neo4j_export_button,
        viewer.neo4j_status,
        width=450,
        sizing_mode='stretch_height'
    ),
    sizing_mode='stretch_both'
)

app.servable()