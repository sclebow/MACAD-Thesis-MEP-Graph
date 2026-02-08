# This is a simple GraphML viewer for visualizing the graph representation of Electrical Equipment elements in a BIM model.
# It uses the python Panel library as a UI
# It loads a GraphML file and displays the graph using NetworkX and PyVis

import panel as pn
import networkx as nx
from io import BytesIO
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
import math
try:
    from networkx.drawing.nx_agraph import graphviz_layout
except ImportError:
    graphviz_layout = None

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

pn.extension('tabulator', notifications=True)

DEFAULT_FILE_PATH = "./bim_to_graph/output_graph.graphml"

def create_plotly_graph(G, name_id_toggle=True):
    """Convert NetworkX graph to Plotly Figure using graphviz_layout (dot)"""
    if graphviz_layout is None:
        raise ImportError("networkx.nx_agraph.graphviz_layout is required. Please install pygraphviz.")

    # Use graphviz_layout for node positions
    # pack=True separates disconnected components; overlap="false" prevents node overlap
    pos = graphviz_layout(G, prog="dot", args='-Goverlap=false -Gpack=true -Gpackmode=graph -Gpad=0.5')

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

    # Prepare node traces
    node_x = []
    node_y = []
    node_text = []
    node_color = []
    node_size = []
    node_ids = []
    for node, attrs in G.nodes(data=True):
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        label = attrs.get('name', str(node)) if name_id_toggle else str(node)
        category = attrs.get('category', 'Unknown')
        color = category_color_map.get(category, '#1f77b4')
        size = category_size_map.get(category, default_size)
        tooltip_lines = [f"Node ID: {node}"]
        tooltip_lines.append("-" * 30)
        for key, value in attrs.items():
            tooltip_lines.append(f"{key}: {value}")
        tooltip = "<br>".join(tooltip_lines)
        node_text.append(tooltip)
        node_color.append(color)
        node_size.append(size)
        node_ids.append(node)

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode='markers+text',
        text=[attrs.get('name', str(n)) if name_id_toggle else str(n) for n, attrs in G.nodes(data=True)],
        textposition="top center",
        hoverinfo='text',
        hovertext=node_text,
        marker=dict(
            color=node_color,
            size=node_size,
            line=dict(width=2, color='#333')
        ),
        customdata=node_ids,
        name='Nodes'
    )

    # Prepare edge traces
    edge_x = []
    edge_y = []
    for u, v in G.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=1, color='#888'),
        hoverinfo='none',
        mode='lines',
        name='Edges'
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        showlegend=False,
        margin=dict(l=20, r=20, t=20, b=20),
        plot_bgcolor='white',
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=600
    )
    return fig, category_color_map

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
            # Create the Plotly graph
            fig, category_color_map = create_plotly_graph(self.G, name_id_toggle)
            legend_pane = self.create_legend(category_color_map)
            self.plotly_pane = pn.pane.Plotly(fig, config={"displayModeBar": True}, sizing_mode='stretch_width', min_height=620)
            return pn.Column(
                legend_pane,
                self.plotly_pane,
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
plot_output = pn.bind(viewer.load_and_plot_graphml, file_input, name_id_toggle)
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