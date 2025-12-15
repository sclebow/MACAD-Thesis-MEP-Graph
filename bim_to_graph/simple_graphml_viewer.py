# This is a simple GraphML viewer for visualizing the graph representation of Electrical Equipment elements in a BIM model.
# It uses the python Panel library as a UI
# It loads a GraphML file and displays the graph using NetworkX and Plotly

import panel as pn
import networkx as nx
import plotly.graph_objs as go
from io import BytesIO
import pandas as pd

pn.extension('plotly', 'tabulator')

DEFAULT_FILE_PATH = "./bim_to_graph/output_graph.graphml"

def create_hierarchical_layout(G):
    """Create a hierarchical tree-like layout for the graph using a Sugiyama-style algorithm"""
    
    # Assign nodes to levels based on longest path from root
    levels = {}
    
    # Find root nodes (nodes with no incoming edges)
    in_degrees = dict(G.in_degree())
    roots = [node for node, degree in in_degrees.items() if degree == 0]
    
    if not roots:
        roots = [min(G.nodes(), key=lambda x: G.degree(x))]
    
    # BFS to assign levels
    from collections import deque
    queue = deque([(root, 0) for root in roots])
    visited = set()
    
    while queue:
        node, level = queue.popleft()
        
        if node in visited:
            continue
        
        visited.add(node)
        levels[node] = max(levels.get(node, -1), level)
        
        for neighbor in G.neighbors(node):
            if neighbor not in visited:
                queue.append((neighbor, level + 1))
    
    # Group nodes by level
    level_groups = {}
    for node, level in levels.items():
        if level not in level_groups:
            level_groups[level] = []
        level_groups[level].append(node)
    
    # Assign x positions within each level
    pos = {}
    max_level = max(level_groups.keys()) if level_groups else 0
    
    for level in range(max_level + 1):
        nodes_at_level = level_groups.get(level, [])
        num_nodes = len(nodes_at_level)
        
        if num_nodes == 1:
            x_positions = [0]
        else:
            # Spread nodes across x-axis with proper spacing
            spacing = 3.0
            x_positions = [i * spacing - (num_nodes - 1) * spacing / 2 for i in range(num_nodes)]
        
        for node, x in zip(nodes_at_level, x_positions):
            pos[node] = (x, -level)
    
    return pos

def plot_graph(G, name_id_toggle, selected_node_params):
    # Try to create a tree layout, fallback to spring if it fails
    try:
        # Convert to tree if possible, or use hierarchical layout
        if nx.is_tree(G):
            pos = nx.nx_agraph.graphviz_layout(G, prog='dot')
        else:
            # For non-tree graphs, try to create a hierarchical layout
            pos = create_hierarchical_layout(G)
    except:
        # Fallback to spring layout if tree layout fails
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
    node_ids = []
    for node in G.nodes(data=True):
        n, attrs = node
        x, y = pos[n]
        node_x.append(x)
        node_y.append(y)
        node_ids.append(n)
        if name_id_toggle and 'name' in attrs:
            node_text.append(str(attrs['name']))
        else:
            node_text.append(str(n))
    
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=node_text,
        textposition='top center',
        customdata=node_ids,
        marker=dict(
            showscale=False,
            color='#1f77b4',
            size=12,
            line_width=2),
        hoverinfo='none'
    )

    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        showlegend=False,
                        margin=dict(b=50, l=50, r=50, t=50),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        hovermode='closest'))
    
    return fig

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
        self.plotly_pane = None
        
    def load_and_plot_graphml(self, file_obj, name_id_toggle):
        if not file_obj:
            return pn.pane.Markdown('Upload a .graphml file.')
        
        try:
            self.G = nx.read_graphml(BytesIO(file_obj))
            # Reset node parameters table
            self.selected_node_params.value = pd.DataFrame({'Parameter': ['Click on a node to view parameters'], 'Value': ['']})
            
            # Create the plot
            fig = plot_graph(self.G, name_id_toggle, self.selected_node_params)
            self.plotly_pane = pn.pane.Plotly(fig, config={'responsive': True}, sizing_mode='stretch_both')
            
            # Set up click event handler
            self.plotly_pane.param.watch(self.handle_click_event, 'click_data')
            
            return self.plotly_pane
            
        except Exception as e:
            return pn.pane.Markdown(f"**Error loading GraphML:** {e}")
    
    def handle_click_event(self, event):
        """Handle click events on the plotly graph"""
        if event.new and self.G:
            click_data = event.new
            if 'points' in click_data and len(click_data['points']) > 0:
                point = click_data['points'][0]
                if 'customdata' in point:
                    node_id = point['customdata']
                    self.update_node_parameters_table(node_id)
    
    def update_node_parameters_table(self, node_id):
        """Update the node parameters table with the selected node's data"""
        if node_id in self.G.nodes:
            node_attrs = self.G.nodes[node_id]
            
            # Create a list of parameter dictionaries for the table
            params_data = []
            params_data.append({'Parameter': 'Node ID', 'Value': str(node_id)})
            for key, value in node_attrs.items():
                params_data.append({'Parameter': key, 'Value': str(value)})
            
            self.selected_node_params.value = pd.DataFrame(params_data)

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
    pn.Column(
        "## Node Parameters",
        pn.pane.Markdown("Click on a node in the graph to view its parameters here."),
        viewer.selected_node_params,
        width=550,
        sizing_mode='stretch_height'
    ),
    sizing_mode='stretch_both'
)

app.servable()