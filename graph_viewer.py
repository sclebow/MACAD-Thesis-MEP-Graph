# This is a Panel application that allows users to visualize and interact with a graph based on a GraphML xlmns file.
# It provides functionalities to load a graph, display it, and interact with its nodes and edges.

import panel as pn
from panel import widgets
import io
import networkx as nx
import plotly.graph_objects as go
import os
import pandas as pd
import random
import math
import datetime

# Import helper files
from helpers.maintenance_tasks import process_maintenance_tasks
# from helpers.node_risk import *
# from helpers.rul_helper import apply_rul_to_graph
# Import MEP graph generator
from helpers.rul_helper import apply_maintenance_log_to_graph
from graph_generator.mepg_generator import generate_mep_graph, define_building_characteristics, determine_number_of_risers, locate_risers, determine_voltage_level, distribute_loads, determine_riser_attributes, place_distribution_equipment, connect_nodes
from graph_generator.mepg_generator import clean_graph_none_values

print("\n" * 5)

pn.extension('plotly')
pn.extension('jsoneditor')

class GraphController:
    def __init__(self):
        self.current_graph = [None]  # Keep existing format for compatibility
        self.view_settings = {
            'use_full_names': False,
            'visualization_type': '2d_type'
        }
    
    def load_graph_from_file(self, file_bytes):
        """Load graph from file bytes and apply processing"""
        try:
            file_buffer = io.BytesIO(file_bytes)
            G = nx.read_graphml(file_buffer)
            
            # Validate and clean graph data
            self._validate_graph_data(G)
            
            # Apply risk scores and RUL with error handling
            try:
                from helpers.node_risk import apply_risk_scores_to_graph
                G = apply_risk_scores_to_graph(G)
            except Exception as e:
                print(f"Warning: Risk score calculation failed: {e}")
            
            try:
                from helpers.rul_helper import apply_rul_to_graph
                G = apply_rul_to_graph(G)
            except Exception as e:
                print(f"Warning: RUL calculation failed: {e}")
            
            self.current_graph[0] = G
            return {'success': True, 'message': 'Graph loaded successfully'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _validate_graph_data(self, graph):
        """Validate and clean graph data"""
        for node_id, attrs in graph.nodes(data=True):
            # Ensure numeric values are not None
            for key, value in attrs.items():
                if value is None and key in ['x', 'y', 'z', 'propagated_power', 'power_rating']:
                    attrs[key] = 0.0
                    print(f"Warning: Set {key} to 0.0 for node {node_id}")
        
        for edge in graph.edges(data=True):
            edge_attrs = edge[2]
            for key, value in edge_attrs.items():
                if value is None and key in ['voltage', 'current_rating', 'power']:
                    edge_attrs[key] = 0.0
                    print(f"Warning: Set {key} to 0.0 for edge {edge[0]}-{edge[1]}")
    
    def generate_new_graph(self, building_params):
        """Generate new graph with given parameters"""
        try:
            construction_year = int(building_params['construction_year'])
            
            building_attributes = {
                "total_load": int(building_params['total_load']),
                "building_length": building_params['building_length'],
                "building_width": building_params['building_width'],
                "num_floors": int(building_params['num_floors']),
                "floor_height": building_params['floor_height'],
                "construction_date": datetime.datetime(construction_year, 1, 1).strftime("%Y-%m-%d"),
            }
            
            # Set seed if provided
            if building_params.get('seed'):
                random.seed(int(building_params['seed']))
            
            # Generate the graph using existing functions
            building_attrs = define_building_characteristics(building_attributes)
            num_risers = determine_number_of_risers(building_attrs)
            riser_locations = locate_risers(building_attrs, num_risers)
            voltage_info = determine_voltage_level(building_attrs)
            floor_loads, end_loads = distribute_loads(building_attrs, voltage_info)
            riser_floor_attributes = determine_riser_attributes(building_attrs, riser_locations, floor_loads, end_loads, voltage_info)
            distribution_equipment = place_distribution_equipment(building_attrs, riser_floor_attributes, voltage_info)
            cluster_strength = building_params.get('cluster_strength', 0.95)
            G = connect_nodes(building_attrs, riser_locations, distribution_equipment, voltage_info, end_loads, cluster_strength)
            
            # Apply risk scores and RUL
            from helpers.node_risk import apply_risk_scores_to_graph
            from helpers.rul_helper import apply_rul_to_graph
            
            G = apply_risk_scores_to_graph(G)
            G = apply_rul_to_graph(G)
            G = clean_graph_none_values(G)
            
            self.current_graph[0] = G
            return {'success': True, 'graph': G}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_visualization_data(self, viz_type=None):
        """Get visualization figure for current graph"""
        if not self.current_graph[0]:
            return None
        
        viz_type = viz_type or self.view_settings['visualization_type']
        use_full_names = self.view_settings['use_full_names']
        
        if viz_type == '2d_type':
            return visualize_graph_two_d(self.current_graph[0], use_full_names)
        elif viz_type == '2d_risk':
            return visualize_graph_two_d_risk(self.current_graph[0], use_full_names)
        elif viz_type == '3d':
            return visualize_graph_three_d(self.current_graph[0], use_full_names)
        
        return None
    
    def get_component_data(self):
        """Get lists of nodes and edges for dropdowns"""
        if not self.current_graph[0]:
            return {'nodes': [], 'edges': []}
        
        return {
            'nodes': list(self.current_graph[0].nodes()),
            'edges': [f"{u} - {v}" for u, v in self.current_graph[0].edges()]
        }
    
    def update_node_attributes(self, node_id, attributes_dict):
        """Update node attributes from dataframe"""
        if not self.current_graph[0] or node_id not in self.current_graph[0].nodes:
            return {'success': False, 'error': 'Invalid node'}
        
        for k, v in attributes_dict.items():
            if k in ["x", "y", "z"]:
                try:
                    self.current_graph[0].nodes[node_id][k] = float(v)
                except Exception:
                    self.current_graph[0].nodes[node_id][k] = v
            else:
                self.current_graph[0].nodes[node_id][k] = v
        
        return {'success': True}
    
    def save_graph_to_file(self, filename):
        """Save current graph to file"""
        if not self.current_graph[0]:
            return {'success': False, 'error': 'No graph loaded'}
        
        try:
            if not filename.lower().endswith('.mepg'):
                filename += '.mepg'
            
            output_dir = 'graph_outputs'
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, filename)
            
            self.current_graph[0].graph["source"] = "Panel Graph Viewer Export"
            nx.write_graphml(self.current_graph[0], output_path)
            
            return {'success': True, 'path': output_path}
        except Exception as e:
            return {'success': False, 'error': str(e)}

class SystemViewController:
    def __init__(self, graph_controller):
        self.graph_controller = graph_controller
        self.widgets = {}
        
    def register_widgets(self, widgets_dict):
        """Register UI widgets for event handling"""
        self.widgets.update(widgets_dict)
    
    def setup_callbacks(self):
        """Set up all event callbacks"""
        # File operations
        if 'file_input' in self.widgets:
            self.widgets['file_input'].param.watch(self.handle_file_load, 'value')
        if 'save_button' in self.widgets:
            self.widgets['save_button'].on_click(self.handle_save_graph)
        
        # Visualization controls
        if 'name_toggle' in self.widgets:
            self.widgets['name_toggle'].param.watch(self.handle_name_toggle, 'value')
        
        # Node/edge selection
        if 'node_dropdown' in self.widgets:
            self.widgets['node_dropdown'].param.watch(self.handle_node_selection, 'value')
        if 'edge_dropdown' in self.widgets:
            self.widgets['edge_dropdown'].param.watch(self.handle_edge_selection, 'value')
        if 'node_attr_df' in self.widgets:
            self.widgets['node_attr_df'].param.watch(self.handle_node_attr_change, 'value')
        if 'edge_attr_df' in self.widgets:
            self.widgets['edge_attr_df'].param.watch(self.handle_edge_attr_change, 'value')
    
    def handle_file_load(self, event):
        """Handle file upload"""
        if event.new is not None:
            result = self.graph_controller.load_graph_from_file(event.new)
            if result['success']:
                self.refresh_all_displays()
                print("Graph loaded successfully")
            else:
                print(f"Error loading graph: {result['error']}")
    
    def handle_save_graph(self, event):
        """Handle save graph button"""
        if 'save_input' in self.widgets:
            filename = self.widgets['save_input'].value or "graph.mepg"
            result = self.graph_controller.save_graph_to_file(filename)
            if result['success']:
                if 'save_status' in self.widgets:
                    self.widgets['save_status'].object = f"**Graph saved to `{result['path']}`**"
                    self.widgets['save_status'].visible = True
                print(f"Graph saved to {result['path']}")
            else:
                if 'save_status' in self.widgets:
                    self.widgets['save_status'].object = f"**Error saving graph:** {result['error']}"
                    self.widgets['save_status'].visible = True
                print(f"Error saving graph: {result['error']}")
    
    def handle_name_toggle(self, event):
        """Handle name display toggle"""
        self.graph_controller.view_settings['use_full_names'] = event.new
        self.update_all_visualizations()
    
    def handle_node_selection(self, event):
        """Handle node dropdown selection"""
        if event.new and self.graph_controller.current_graph[0]:
            self.update_node_info(event.new)
    
    def handle_edge_selection(self, event):
        """Handle edge dropdown selection"""
        if event.new and self.graph_controller.current_graph[0]:
            self.update_edge_info(event.new)
    
    def handle_node_attr_change(self, event):
        """Handle node attribute dataframe changes"""
        if 'node_dropdown' in self.widgets:
            node = self.widgets['node_dropdown'].value
            if node and event.new is not None:
                df = event.new
                if len(df) > 0:
                    attrs = dict(zip(df["Attribute"], df["Value"]))
                    result = self.graph_controller.update_node_attributes(node, attrs)
                    if result['success']:
                        self.update_all_visualizations()
    
    def handle_edge_attr_change(self, event):
        """Handle edge attribute dataframe changes"""
        if 'edge_dropdown' in self.widgets:
            edge_str = self.widgets['edge_dropdown'].value
            if edge_str and " - " in edge_str and event.new is not None:
                u, v = edge_str.split(" - ", 1)
                edge_tuple = (u, v)
                if edge_tuple in self.graph_controller.current_graph[0].edges:
                    df = event.new
                    if len(df) > 0:
                        attrs = dict(zip(df["Attribute"], df["Value"]))
                        for k, v in attrs.items():
                            self.graph_controller.current_graph[0].edges[edge_tuple][k] = v
                        self.update_all_visualizations()
    
    def refresh_all_displays(self):
        """Refresh all UI displays after data change"""
        self.update_all_visualizations()
        self.update_dropdowns()
        # Automatically process maintenance tasks when graph is loaded
        self.auto_process_maintenance_tasks()
    
    def auto_process_maintenance_tasks(self):
        """Automatically trigger maintenance task processing if a graph is loaded"""
        try:
            if self.graph_controller.current_graph[0] is not None:
                # Call the global process_tasks_callback function
                process_tasks_callback()
        except Exception as e:
            print(f"Warning: Auto maintenance processing failed: {e}")
    
    def update_all_visualizations(self):
        """Update all visualization panes"""
        if 'plot_pane' in self.widgets:
            fig = self.graph_controller.get_visualization_data('2d_type')
            if fig:
                self.widgets['plot_pane'].object = fig
        
        if 'plot_risk_pane' in self.widgets:
            fig = self.graph_controller.get_visualization_data('2d_risk')
            if fig:
                self.widgets['plot_risk_pane'].object = fig
        
        if 'three_d_pane' in self.widgets:
            fig = self.graph_controller.get_visualization_data('3d')
            if fig:
                self.widgets['three_d_pane'].object = fig
    
    def update_dropdowns(self):
        """Update node and edge dropdown options"""
        data = self.graph_controller.get_component_data()
        
        if 'node_dropdown' in self.widgets:
            self.widgets['node_dropdown'].options = data['nodes']
            if data['nodes']:
                self.widgets['node_dropdown'].value = data['nodes'][0]
        
        if 'edge_dropdown' in self.widgets:
            self.widgets['edge_dropdown'].options = data['edges']
            if data['edges']:
                self.widgets['edge_dropdown'].value = data['edges'][0]
    
    def update_node_info(self, node_id):
        """Update node info display and attribute table"""
        if not self.graph_controller.current_graph[0]:
            return
            
        if node_id and node_id in self.graph_controller.current_graph[0].nodes:
            attrs = self.graph_controller.current_graph[0].nodes[node_id]
            
            if 'node_info_pane' in self.widgets:
                self.widgets['node_info_pane'].object = f"**Node:** {node_id}"
            
            if 'node_attr_df' in self.widgets:
                if attrs:
                    df = pd.DataFrame(list(attrs.items()), columns=["Attribute", "Value"])
                    self.widgets['node_attr_df'].value = df.copy()
                else:
                    self.widgets['node_attr_df'].value = pd.DataFrame(columns=["Attribute", "Value"])
        else:
            # Handle case where node doesn't exist
            if 'node_info_pane' in self.widgets:
                self.widgets['node_info_pane'].object = f"**Node not found:** {node_id}"
            if 'node_attr_df' in self.widgets:
                self.widgets['node_attr_df'].value = pd.DataFrame(columns=["Attribute", "Value"])
            
            # Refresh dropdown to remove invalid options
            self.update_dropdowns()
    
    def update_edge_info(self, edge_str):
        """Update edge info display and attribute table"""
        if not self.graph_controller.current_graph[0]:
            return
            
        if edge_str and " - " in edge_str:
            u, v = edge_str.split(" - ", 1)
            edge_tuple = (u, v)
            if edge_tuple in self.graph_controller.current_graph[0].edges:
                attrs = self.graph_controller.current_graph[0].edges[edge_tuple]
                
                if 'edge_info_pane' in self.widgets:
                    self.widgets['edge_info_pane'].object = f"**Edge:** {edge_tuple}"
                
                if 'edge_attr_df' in self.widgets:
                    if attrs:
                        df = pd.DataFrame(list(attrs.items()), columns=["Attribute", "Value"])
                        self.widgets['edge_attr_df'].value = df.copy()
                    else:
                        self.widgets['edge_attr_df'].value = pd.DataFrame(columns=["Attribute", "Value"])
            else:
                if 'edge_info_pane' in self.widgets:
                    self.widgets['edge_info_pane'].object = f"**Edge not found:** {edge_str}"
                if 'edge_attr_df' in self.widgets:
                    self.widgets['edge_attr_df'].value = pd.DataFrame(columns=["Attribute", "Value"])

# END OF SystemViewController CLASS

def hierarchy_pos(G, root=None, width=1., vert_gap = 0.2, vert_loc = 0, xcenter = 0.5):

    '''
    From Joel's answer at https://stackoverflow.com/a/29597209/2966723.  
    Licensed under Creative Commons Attribution-Share Alike 
    
    If the graph is a tree this will return the positions to plot this in a 
    hierarchical layout.
    
    G: the graph (must be a tree)
    
    root: the root node of current branch 
    - if the tree is directed and this is not given, 
      the root will be found and used
    - if the tree is directed and this is given, then 
      the positions will be just for the descendants of this node.
    - if the tree is undirected and not given, 
      then a random choice will be used.
    
    width: horizontal space allocated for this branch - avoids overlap with other branches
    
    vert_gap: gap between levels of hierarchy
    
    vert_loc: vertical location of root
    
    xcenter: horizontal location of root
    '''
    if not nx.is_tree(G):
        raise TypeError('cannot use hierarchy_pos on a graph that is not a tree')

    if root is None:
        if isinstance(G, nx.DiGraph):
            root = next(iter(nx.topological_sort(G)))  #allows back compatibility with nx version 1.11
        else:
            root = random.choice(list(G.nodes))

    def _hierarchy_pos(G, root, width=1., vert_gap = 0.2, vert_loc = 0, xcenter = 0.5, pos = None, parent = None):
        '''
        see hierarchy_pos docstring for most arguments

        pos: a dict saying where all nodes go if they have been assigned
        parent: parent of this branch. - only affects it if non-directed

        '''
    
        if pos is None:
            pos = {root:(xcenter,vert_loc)}
        else:
            pos[root] = (xcenter, vert_loc)
        children = list(G.neighbors(root))
        if not isinstance(G, nx.DiGraph) and parent is not None:
            children.remove(parent)  
        if len(children)!=0:
            dx = width/len(children) 
            nextx = xcenter - width/2 - dx/2
            for child in children:
                nextx += dx
                pos = _hierarchy_pos(G,child, width = dx, vert_gap = vert_gap, 
                                    vert_loc = vert_loc-vert_gap, xcenter=nextx,
                                    pos=pos, parent = root)
        return pos

            
    return _hierarchy_pos(G, root, width, vert_gap, vert_loc, xcenter)

# Visualization functions

def _generate_2d_graph_figure(graph, use_full_names=False, node_color_values=None, color_palette=None, colorbar_title=None, showlegend=False, colorbar_range=None):
    # Shared logic for 2D graph visualization
    try:
        # Select a valid root node (first node in the graph)
        if len(graph.nodes) == 0:
            return go.Figure()
        root_node = next(iter(graph.nodes))
        pos = hierarchy_pos(graph, root_node, width = 2*math.pi, xcenter=0)
        pos = {u:(r*math.cos(theta),r*math.sin(theta)) for u, (theta, r) in pos.items()}

    except Exception as e:
        print(f"Error calculating positions: {e}")
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
        edge_0_name = graph.nodes[edge[0]].get('full_name', edge[0]) if use_full_names else edge[0]
        edge_1_name = graph.nodes[edge[1]].get('full_name', edge[1]) if use_full_names else edge[1]
        hover_text = f"{edge_0_name} - {edge_1_name}"
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
        showlegend=showlegend
    )

    node_x = []
    node_y = []
    names = []
    node_text = []
    for node, attrs in graph.nodes(data=True):
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        # Use full name or short name based on toggle
        display_name = attrs.get('full_name', node) if use_full_names else node
        names.append(display_name)
        hover = f"{display_name}<br>Type: {attrs.get('type', 'Unknown')}<br>" + "<br>".join([f"{k}: {v}" for k, v in attrs.items() if k not in ['type', 'full_name']])
        node_text.append(hover)

    # Node size scaling based on propagated_power
    prop_powers = [graph.nodes[n].get('propagated_power', 0) for n in graph.nodes]
    if prop_powers:
        min_power = min(prop_powers)
        max_power = max(prop_powers)
        if max_power == min_power:
            norm_power = [0.5 for _ in prop_powers]
        else:
            norm_power = [(p - min_power) / (max_power - min_power) for p in prop_powers]
        # Scale size between 10 and 30
        node_sizes = [10 + 20 * x for x in norm_power]
    else:
        node_sizes = [15 for _ in graph.nodes]

    # Node coloring logic
    if node_color_values is not None:
        # Use provided values and palette
        color_vals = [node_color_values.get(n, 0) for n in graph.nodes]
        palette = color_palette or 'Viridis'
        colorbar_dict = dict(title=colorbar_title or 'Value')
        marker_dict = dict(
            color=color_vals,
            colorscale=palette,
            size=node_sizes,
            colorbar=colorbar_dict,
            line_width=2,
            opacity=0.85
        )
        if colorbar_range:
            marker_dict['cmin'] = colorbar_range[0]
            marker_dict['cmax'] = colorbar_range[1]
        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode='markers+text',
            text=names,
            textposition="top center",
            hoverinfo='text',
            marker=marker_dict,
            hovertext=node_text,
            name='Nodes'
        )
        node_traces = [node_trace]
    else:
        node_types = [graph.nodes[n].get('type', 'Unknown') for n in graph.nodes]
        unique_types = list(sorted(set(node_types)))
        plotly_palette = [
            'rgba(99,110,250,0.85)', 'rgba(239,85,59,0.85)', 'rgba(0,204,150,0.85)', 'rgba(171,99,250,0.85)', 'rgba(255,161,90,0.85)', 'rgba(25,211,243,0.85)',
            'rgba(255,102,146,0.85)', 'rgba(182,232,128,0.85)', 'rgba(255,151,255,0.85)', 'rgba(254,203,82,0.85)', 'rgba(31,119,180,0.85)', 'rgba(255,127,14,0.85)',
            'rgba(44,160,44,0.85)', 'rgba(214,39,40,0.85)', 'rgba(148,103,189,0.85)', 'rgba(140,86,75,0.85)', 'rgba(227,119,194,0.85)', 'rgba(127,127,127,0.85)',
            'rgba(188,189,34,0.85)', 'rgba(23,190,207,0.85)'
        ]
        type_color_map = {t: plotly_palette[i % len(plotly_palette)] for i, t in enumerate(unique_types)}
        node_colors = [type_color_map[t] for t in node_types]
        node_traces = []
        node_type_list = node_types
        for t in unique_types:
            indices = [i for i, typ in enumerate(node_type_list) if typ == t]
            if not indices:
                continue
            trace = go.Scatter(
                x=[node_x[i] for i in indices],
                y=[node_y[i] for i in indices],
                mode='markers+text',
                text=[names[i] for i in indices],
                textposition="top center",
                hoverinfo='text',
                marker=dict(
                    color=[node_colors[i] for i in indices],
                    size=[node_sizes[i] for i in indices],
                    line_width=2,
                    opacity=0.85
                ),
                hovertext=[node_text[i] for i in indices],
                name=str(t)
            )
            node_traces.append(trace)

    fig = go.Figure(data=[edge_trace, edge_marker_trace] + node_traces,
                    layout=go.Layout(
                        showlegend=showlegend,
                        hovermode='closest',
                        margin=dict(b=20,l=5,r=5,t=40),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                    ))
    return fig

def visualize_graph_two_d(graph, use_full_names=False):
    return _generate_2d_graph_figure(graph, use_full_names=use_full_names)

def visualize_graph_two_d_risk(graph, use_full_names=False):
    # Color nodes by risk_score attribute
    risk_scores = {n: graph.nodes[n].get('risk_score', 0) for n in graph.nodes}
    return _generate_2d_graph_figure(
        graph,
        use_full_names=use_full_names,
        node_color_values=risk_scores,
        color_palette='Inferno',
        colorbar_title='Risk Score',
        showlegend=False
    )

def visualize_graph_three_d(graph, use_full_names=False):
    """
    Visualizes a NetworkX graph in 3D using Plotly.
    Uses the x, y, z coordinates of nodes for 3D positioning.
    """
    pos = nx.spring_layout(graph, dim=3)

    # Get node types for color mapping
    node_types = [graph.nodes[n].get('type', 'Unknown') for n in graph.nodes]
    unique_types = list(sorted(set(node_types)))
    plotly_palette = [
        '#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3',
        '#FF6692', '#B6E880', '#FF97FF', '#FECB52', '#1f77b4', '#ff7f0e',
        '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f',
        '#bcbd22', '#17becf'
    ]
    type_color_map = {t: plotly_palette[i % len(plotly_palette)] for i, t in enumerate(unique_types)}
    node_colors = [type_color_map[t] for t in node_types]

    node_x = []
    node_y = []
    node_z = []
    names = []
    node_text = []
    node_type_list = []
    for idx, (node, attrs) in enumerate(graph.nodes(data=True)):
        x = attrs.get('x', 0)
        y = attrs.get('y', 0)
        z = attrs.get('z', 0)
        node_x.append(x)
        node_y.append(y)
        node_z.append(z)
        # Use full name or short name based on toggle
        display_name = attrs.get('full_name', node) if use_full_names else node
        names.append(display_name)
        node_type = attrs.get('type', 'Unknown')
        node_type_list.append(node_type)
        hover = f"{display_name}<br>Type: {node_type}<br>" + "<br>".join([f"{k}: {v}" for k, v in attrs.items() if k not in ['type', 'full_name']])
        node_text.append(hover)

    # Set axis ranges to ensure equal scale
    all_coords = node_x + node_y + node_z
    if all_coords:
        min_coord = min(all_coords)
        max_coord = max(all_coords)
        # Add a small margin
        margin = 0.05 * (max_coord - min_coord) if max_coord > min_coord else 1
        axis_range = [min_coord - margin, max_coord + margin]
    else:
        axis_range = [-1, 1]

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
        # First segment: (x0, y0, z0) -> (x1, y1, z0)
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]
        edge_z += [z0, z0, None]
        # Second segment: (x1, y1, z0) -> (x1, y1, z1)
        edge_x += [x1, x1, None]
        edge_y += [y1, y1, None]
        edge_z += [z0, z1, None]
        # Add invisible marker at the bend and at the midpoint of the vertical segment for better hover
        bend_x = x1
        bend_y = y1
        bend_z = z0
        mid_z = (z0 + z1) / 2
        edge_marker_x.extend([(x0 + x1) / 2, bend_x, bend_x])
        edge_marker_y.extend([(y0 + y1) / 2, bend_y, bend_y])
        edge_marker_z.extend([z0, bend_z, mid_z])
        # Create hover text for edges using display names
        edge_0_name = graph.nodes[edge[0]].get('full_name', edge[0]) if use_full_names else edge[0]
        edge_1_name = graph.nodes[edge[1]].get('full_name', edge[1]) if use_full_names else edge[1]
        hover_text = f"{edge_0_name} - {edge_1_name}"
        edge_attrs = graph.edges[edge]
        if edge_attrs:
            hover_text += "<br>" + "<br>".join([f"{k}: {v}" for k, v in edge_attrs.items()])
        edge_marker_text.extend([hover_text, hover_text, hover_text])
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
    # Use propagated_power to scale node size
    prop_powers = [graph.nodes[n].get('propagated_power', 0) for n in graph.nodes]
    if prop_powers:
        min_power = min(prop_powers)
        max_power = max(prop_powers)
        if max_power == min_power:
            norm_power = [0.5 for _ in prop_powers]
        else:
            norm_power = [(p - min_power) / (max_power - min_power) for p in prop_powers]
        # Scale size between 4 and 16
        node_sizes = [4 + 12 * x for x in norm_power]
    else:
        node_sizes = [8 for _ in graph.nodes]

    # Create a trace for each type for legend
    node_traces = []
    for t in unique_types:
        indices = [i for i, typ in enumerate(node_type_list) if typ == t]
        if not indices:
            continue
        trace = go.Scatter3d(
            x=[node_x[i] for i in indices],
            y=[node_y[i] for i in indices],
            z=[node_z[i] for i in indices],
            mode='markers+text',
            text=[names[i] for i in indices],
            textposition="top center",
            hoverinfo='text',
            marker=dict(
                color=type_color_map[t],
                size=[node_sizes[i] for i in indices],
                line_width=2
            ),
            hovertext=[node_text[i] for i in indices],
            name=str(t)
        )
        node_traces.append(trace)
    # --- Add building bounds as a rectangular prism if metadata is present ---
    building_length = graph.graph.get('building_length')
    building_width = graph.graph.get('building_width')
    num_floors = graph.graph.get('num_floors')
    floor_height = graph.graph.get('floor_height')
    prism_trace = None
    if all(v is not None for v in [building_length, building_width, num_floors, floor_height]):
        try:
            # Convert to float for plotting
            lx = float(building_length)
            ly = float(building_width)
            lz = float(num_floors) * float(floor_height)
            # Prism corners (origin at 0,0,0)
            x_corners = [0, lx, lx, 0, 0, lx, lx, 0]
            y_corners = [0, 0, ly, ly, 0, 0, ly, ly]
            z_corners = [0, 0, 0, 0, lz, lz, lz, lz]
            # 12 lines for the box edges
            prism_lines = [
                [0,1],[1,2],[2,3],[3,0], # bottom
                [4,5],[5,6],[6,7],[7,4], # top
                [0,4],[1,5],[2,6],[3,7]  # verticals
            ]
            prism_x = []
            prism_y = []
            prism_z = []
            for a, b in prism_lines:
                prism_x += [x_corners[a], x_corners[b], None]
                prism_y += [y_corners[a], y_corners[b], None]
                prism_z += [z_corners[a], z_corners[b], None]
            prism_trace = go.Scatter3d(
                x=prism_x, y=prism_y, z=prism_z,
                mode='lines',
                line=dict(color='rgba(0,200,0,0.7)', width=4),
                name='Building Bounds',
                hoverinfo='skip',
                showlegend=True
            )
        except Exception as e:
            print(f"Error drawing building bounds: {e}")
            prism_trace = None
    # Compose figure data
    fig_data = [edge_trace, edge_marker_trace] + node_traces
    if prism_trace:
        fig_data.append(prism_trace)
    fig = go.Figure(data=fig_data,
                    layout=go.Layout(
                        showlegend=True,
                        hovermode='closest',
                        margin=dict(b=20,l=5,r=5,t=40),
                        scene=dict(
                            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=axis_range),
                            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=axis_range),
                            zaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=axis_range)
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
    """Delegate to controller"""
    system_controller.handle_node_selection(event)

def edge_dropdown_callback(event):
    """Delegate to controller"""
    system_controller.handle_edge_selection(event)

def file_input_callback(event):
    """Delegate to controller"""
    system_controller.handle_file_load(event)

def autoload_example_graph():
    """Load example graph using controller"""
    global system_controller
    
    example_path = 'example_graph.mepg'
    if os.path.exists(example_path):
        try:
            with open(example_path, 'rb') as f:
                G = nx.read_graphml(f)
                # Check if the graph is a directed graph
                if not isinstance(G, nx.DiGraph):
                    raise ValueError("The example graph must be a directed graph.")
                fig = visualize_graph_two_d(G, use_full_names=name_toggle.value)
                plot_pane.object = fig
                fig_risk = visualize_graph_two_d_risk(G, use_full_names=name_toggle.value)
                plot_risk_pane.object = fig_risk
                three_d_fig = visualize_graph_three_d(G, use_full_names=name_toggle.value)
                three_d_pane.object = three_d_fig
                current_graph[0] = G

                # G = add_risk_scores(G)

                update_dropdowns(G)
                # Trigger the maintenance process now that the graph is loaded
                process_tasks_callback()

                file_bytes = f.read()
                result = graph_controller.load_graph_from_file(file_bytes)
                if result['success']:
                    system_controller.refresh_all_displays()
                    system_controller.update_dropdowns()
                    print("Example graph loaded successfully")
                else:
                    print(f"Failed to autoload example graph: {result['error']}")
        except Exception as e:
            print(f"Failed to autoload example graph: {e}")
    else:
        print(f"Example graph file '{example_path}' not found.")

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

# Name display toggle
name_toggle = pn.widgets.Toggle(name="Use Full Names", value=False)

def name_toggle_callback(event):
    """Delegate to controller"""
    system_controller.handle_name_toggle(event)

name_toggle.param.watch(name_toggle_callback, 'value')

# --- Graph Generator Panel ---
def generate_graph_callback(event):
    """Generate graph using controller"""
    building_params = {
        'construction_year': construction_year_slider.value,
        'total_load': total_load_slider.value,
        'building_length': building_length_slider.value,
        'building_width': building_width_slider.value,
        'num_floors': num_floors_slider.value,
        'floor_height': floor_height_slider.value,
        'cluster_strength': cluster_strength_slider.value,
        'seed': seed_input.value
    }
    
    result = graph_controller.generate_new_graph(building_params)
    if result['success']:
        system_controller.refresh_all_displays()
        generator_status.object = "**Graph generated successfully!**"
        generator_status.visible = True
        
        # Save generated graph
        output_dir = 'graph_outputs'
        os.makedirs(output_dir, exist_ok=True)
        current_date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(output_dir, f"generated_graph_{current_date_str}.mepg")
        nx.write_graphml(graph_controller.current_graph[0], output_path)
    else:
        generator_status.object = f"**Error generating graph:** {result['error']}"
        generator_status.visible = True

# Generator input widgets with help text
total_load_slider = pn.widgets.IntSlider(
    name="Total Load (kW)", 
    start=50, end=5000, step=50, value=1000
)
total_load_help = pn.pane.Markdown("*Total electrical load for the entire building. Higher loads result in more complex distribution systems with transformers and multiple voltage levels.*", margin=(0, 5))

building_length_slider = pn.widgets.FloatSlider(
    name="Building Length (m)", 
    start=5.0, end=100.0, step=1.0, value=20.0
)
building_length_help = pn.pane.Markdown("*Length of the building in meters. Affects the placement and number of electrical risers needed for distribution.*", margin=(0, 5))

building_width_slider = pn.widgets.FloatSlider(
    name="Building Width (m)", 
    start=5.0, end=100.0, step=1.0, value=20.0
)
building_width_help = pn.pane.Markdown("*Width of the building in meters. Combined with length, determines the building footprint and riser distribution strategy.*", margin=(0, 5))

num_floors_slider = pn.widgets.IntSlider(
    name="Number of Floors", 
    start=1, end=20, step=1, value=4
)
num_floors_help = pn.pane.Markdown("*Number of floors in the building. More floors create taller electrical distribution systems with vertical risers.*", margin=(0, 5))

floor_height_slider = pn.widgets.FloatSlider(
    name="Floor Height (m)", 
    start=2.0, end=6.0, step=0.1, value=3.5
)
floor_height_help = pn.pane.Markdown("*Height of each floor in meters. Affects the total building height and cable run lengths in the 3D visualization.*", margin=(0, 5))

cluster_strength_slider = pn.widgets.FloatSlider(
    name="Cluster Strength", 
    start=0.0, end=1.0, step=0.05, value=0.95
)
cluster_strength_help = pn.pane.Markdown(
    "*Controls how loads are grouped together as nodes.  Does not affect load distribution, but rather how the graph visualizes loads by grouping nearby, similar loads together as single nodes.*",
    margin=(0, 5))

construction_year_slider = pn.widgets.IntSlider(
    name="Construction Year", 
    start=1950, end=2030, step=1, value=datetime.datetime.now().year
)
construction_year_help = pn.pane.Markdown("*Year the building was constructed. This affects the baseline aging and maintenance attributes of all electrical equipment in the building.*", margin=(0, 5))

seed_input = pn.widgets.TextInput(
    name="Seed (optional)", 
    placeholder="Enter number for reproducible results"
)
seed_help = pn.pane.Markdown("*Random seed for reproducible graph generation. Use the same seed to generate identical graphs with the same parameters.*", margin=(0, 5))

generate_button = pn.widgets.Button(name="Generate Graph", button_type="primary")
generate_button.on_click(generate_graph_callback)

generator_status = pn.pane.Markdown(visible=False)

generator_panel = pn.Column(
    "### Generate New MEP Graph",
    pn.Row(total_load_slider, total_load_help),
    pn.Row(num_floors_slider, num_floors_help),
    pn.Row(building_length_slider, building_length_help),
    pn.Row(building_width_slider, building_width_help),
    pn.Row(floor_height_slider, floor_height_help),
    pn.Row(cluster_strength_slider, cluster_strength_help),
    pn.Row(construction_year_slider, construction_year_help),
    pn.Row(seed_input, seed_help),
    generate_button,
    generator_status,
    sizing_mode='stretch_width'
)

generator_accordion = pn.Accordion(
    ("Generate a New MEP Graph", generator_panel),
    # active=0,
    sizing_mode='stretch_width'
)

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
# Initialize controllers
graph_controller = GraphController()
system_controller = SystemViewController(graph_controller)

# For backward compatibility with existing code
current_graph = graph_controller.current_graph

def node_attr_df_callback(event):
    """Delegate to controller"""
    system_controller.handle_node_attr_change(event)

#node_attr_df.param.watch(node_attr_df_callback, 'value') # Commented out - controller handles this

# Add a dropdown for selecting an edge from the graph
edge_dropdown = pn.widgets.Select(name="Select Edge", options=[])
edge_info_pane = pn.pane.Markdown("No edge selected.")
# edge_dropdown.param.watch(edge_dropdown_callback, 'value') # Commented out - controller handles this

# Editable DataFrame for edge attributes
edge_attr_df = pn.widgets.DataFrame(
    pd.DataFrame(columns=["Attribute", "Value"]),
    editors={"Attribute": None, "Value": "string"},
    height=selection_table_height,
    show_index=False,
)

def edge_attr_df_callback(event):
    """Delegate to controller"""
    system_controller.handle_edge_attr_change(event)

# edge_attr_df.param.watch(edge_attr_df_callback, 'value')  # Commented out - controller handles this

# Create a pane to display the selected graph
current_month_pane = pn.pane.Markdown(f"**Current Month:**")
graph_pane = pn.pane.Plotly(height=600, sizing_mode='stretch_width')
bar_chart_pane = pn.pane.Plotly(height=300, sizing_mode='stretch_width')

# --- Play/Pause Animation Controls for graph_slider ---
play_button = pn.widgets.Button(name="Play", button_type="success", width=80)
pause_button = pn.widgets.Button(name="Pause", button_type="warning", width=80, disabled=True)

# Animation state
animation_running = {"value": False, "callback": None}

def animate_slider():
    total_animation_time = 2000  # 2 seconds (in milliseconds)
    timeout = total_animation_time / (graph_slider.end - graph_slider.start)
    if not animation_running["value"]:
        return
    # Increment slider value if not at end
    if graph_slider.value < graph_slider.end:
        graph_slider.value += 1
        # Schedule next callback using Panel's curdoc
        animation_running["callback"] = pn.state.curdoc.add_timeout_callback(animate_slider, timeout)
    else:
        # Reset to start
        graph_slider.value = graph_slider.start
        animate_slider()
        # stop_animation()

def start_animation(event=None):
    if not animation_running["value"]:
        animation_running["value"] = True
        play_button.disabled = True
        pause_button.disabled = False
        animate_slider()

def stop_animation(event=None):
    animation_running["value"] = False
    play_button.disabled = False
    pause_button.disabled = True
    # Remove any pending callback
    if animation_running["callback"] is not None:
        try:
            pn.state.curdoc.remove_timeout_callback(animation_running["callback"])
        except Exception:
            pass
        animation_running["callback"] = None

play_button.on_click(start_animation)
pause_button.on_click(stop_animation)

animation_controls = pn.Row(play_button, pause_button, width=200)

app.append(generator_accordion)

app.append(pn.Column(
    "### Load MEP Graph File",
    file_input,
    pn.Row("### Display Options", name_toggle),
    sizing_mode='stretch_width'
))

# Placeholder for the plot
# 2D visualization by type
two_d_column = pn.Column()
two_d_column.append("### 2D Graph Visualization (Type)")
plot_pane = pn.pane.Plotly(height=600, sizing_mode='stretch_width')
two_d_column.append(plot_pane)

# 2D visualization by risk
two_d_risk_column = pn.Column()
two_d_risk_column.append("### 2D Graph Visualization (Risk Score)")
plot_risk_pane = pn.pane.Plotly(height=600, sizing_mode='stretch_width')
two_d_risk_column.append(plot_risk_pane)

# 3D visualization
three_d_column = pn.Column()
three_d_column.append("### 3D Graph Visualization")
three_d_pane = pn.pane.Plotly(height=600, sizing_mode='stretch_width')
three_d_column.append(three_d_pane)

# Create a row to show all plots side by side
plots_row = pn.Row(two_d_column, two_d_risk_column, three_d_column, sizing_mode='stretch_width')
app.append(plots_row)

node_column = pn.Column("### Node Selection", node_dropdown, node_info_pane, node_attr_df, sizing_mode='stretch_width')

edge_column = pn.Column("### Edge Selection", edge_dropdown, edge_info_pane, edge_attr_df, sizing_mode='stretch_width')

# Create a row for selections
selection_row = pn.Row(node_column, edge_column, sizing_mode='stretch_width')
app.append(selection_row)

# --- Load Maintenance log ---
maintenance_log_input = pn.widgets.FileInput(accept='.csv')

def maintenance_log_callback(event):
    if event.new is not None:
        try:
            file_bytes = io.BytesIO(event.new)
            df = pd.read_csv(file_bytes)
            apply_maintenance_log_to_graph(df, current_graph[0])
            """debug code
            print("=== ALL Component Conditions After Maintenance ===")
            maintenance_processed = 0
            for node_id, attrs in current_graph[0].nodes(data=True):
                node_type = attrs.get('type', 'unknown')
                condition = attrs.get('current_condition', 1.0)
                condition_history = attrs.get('condition_history', [])
                
                # Show all equipment (skip end loads)
                if node_type != 'end_load':
                    print(f"{node_id} ({node_type}): condition = {condition:.2f}, history entries = {len(condition_history)}")
                    maintenance_processed += 1
        
            print(f"=== Total equipment processed: {maintenance_processed} ===")
            print("=== End Component Status ===")"""

            print("✅ Maintenance log applied successfully")
        except Exception as e:
            print(f"❌ Error loading maintenance log: {e}")

maintenance_log_input.param.watch(maintenance_log_callback, 'value')

app.append(pn.Column(
    "### Upload Maintenance Log (.csv)",
    maintenance_log_input,
    sizing_mode='stretch_width'
))

# --- Save Graph UI ---
import datetime

def get_default_filename():
    today = datetime.datetime.now().strftime('%y%m%d')
    return f"{today}_graph.mepg"

filename_input = pn.widgets.TextInput(name="Save As Filename", value=get_default_filename())
save_button = pn.widgets.Button(name="Save Graph", button_type="primary")
save_status = pn.pane.Markdown(visible=False)

def save_graph_callback(event):
    """Delegate to controller"""
    system_controller.handle_save_graph(event)

save_button.on_click(save_graph_callback)

save_row = pn.Row(filename_input, save_button)
app.append(pn.Column("### Save Graph", save_row, save_status, sizing_mode='stretch_width'))

prioritized_schedule = None

# Process the maintenance tasks
def process_tasks_callback(event=None):
    # Check if graph is loaded
    if current_graph[0] is None:
        print("No graph loaded. Please load or generate a graph first.")
        return
    
    tasks_file_path = tasks_file_input.value
    if not tasks_file_path:
        tasks_file_path = "./tables/example_maintenance_list.csv"
    
    replacement_tasks_path = replacement_tasks_file_input.value
    if not replacement_tasks_path:
        replacement_tasks_path = "./tables/example_replacement_types.csv"

    prioritized_schedule = process_maintenance_tasks(
        tasks_file_path=tasks_file_path,
        replacement_tasks_path=replacement_tasks_path,
        graph=current_graph[0],
        monthly_budget_time=float(monthly_budget_time_input.value),
        monthly_budget_money=float(monthly_budget_money_input.value),
        months_to_schedule=int(num_months_input.value)
    )
    # except Exception as e:
    #     print(f"Error processing maintenance tasks: {e}")
    #     return

    if prioritized_schedule:
        print("Prioritized maintenance schedule generated successfully.")

        number_of_graphs = len(prioritized_schedule)
        print(f"Number of graphs in the prioritized schedule: {number_of_graphs}")

        months = list(prioritized_schedule.keys())

        # Update slider and number input
        graph_slider.end = number_of_graphs
        graph_number_input.end = number_of_graphs
        graph_number_input.start = 1
        graph_number_input.value = graph_slider.value

        # Get the max amount of tasks from any month
        max_tasks_scheduled_for_month = max(len(prioritized_schedule[month].get('tasks_scheduled_for_month', [])) for month in months)
        max_tasks_executed_for_month = max(len(prioritized_schedule[month].get('executed_tasks', [])) for month in months)
        max_tasks_deferred_for_month = max(len(prioritized_schedule[month].get('deferred_tasks', [])) for month in months)

        max_tasks = max(max_tasks_scheduled_for_month, max_tasks_executed_for_month, max_tasks_deferred_for_month)

        def visualize_rul_graph(graph, use_full_names=False, month=None, show_end_loads=False):
            """
            Visualizes a NetworkX graph in 2D with Remaining Useful Life (RUL) coloring.
            Uses the x, y coordinates of nodes for 2D positioning.
            """
            if not show_end_loads:
                # If not showing end loads, filter out nodes with 'end_load' attribute
                graph = graph.copy()
                nodes_to_remove = []
                for n in list(graph.nodes):
                    if graph.nodes[n].get('type') == 'end_load':
                        nodes_to_remove.append(n)
                for n in nodes_to_remove:
                    graph.remove_node(n)

            # Get RUL values for coloring
            rul_values = {n: graph.nodes[n].get('remaining_useful_life_days') for n in graph.nodes}
            # Get max RUL from first month's graph for consistent color scale
            first_month_graph = prioritized_schedule[months[0]].get('graph')
            first_month_rul_values = [first_month_graph.nodes[n].get('remaining_useful_life_days', 0) for n in first_month_graph.nodes]
            max_rul = max(first_month_rul_values)

            fig = _generate_2d_graph_figure(
                graph,
                use_full_names=use_full_names,
                node_color_values=rul_values,
                color_palette='Agsunset',
                colorbar_title='Remaining Useful Life (RUL)',
                showlegend=False,
                colorbar_range=[0, max_rul]
            )

            # Add a title to the figure
            fig.update_layout(title=f"Remaining Useful Life (RUL) - {month}")

            return fig

        def update_graph(event):
            # Keep number input in sync with slider
            if graph_number_input.value != event.new:
                graph_number_input.value = event.new
            graph_index = event.new - 1
            if 0 <= graph_index < number_of_graphs:
                month = months[graph_index]
                current_month_pane.object = f"**Current Month:** {month}"
                # Get the graph snapshot and convert to Plotly figure
                graph_snapshot = prioritized_schedule[month].get('graph')
                fig = visualize_rul_graph(graph_snapshot, use_full_names=name_toggle.value, month=month, show_end_loads=show_end_loads_toggle.value)
                graph_pane.object = fig

        def _generate_task_list_figure(scheduled_tasks, executed_tasks, deferred_tasks, max_tasks):
            # Create a figure for the task list
            fig = go.Figure()
            fig.add_trace(go.Bar(x=['Scheduled', 'Executed', 'Deferred'],
                                 y=[len(scheduled_tasks), len(executed_tasks), len(deferred_tasks)],
                                 marker_color=['blue', 'green', 'red']))
            fig.update_layout(title='Task List Overview', barmode='stack')

            # Set the y-axis range
            fig.update_yaxes(range=[0, max_tasks + 10])

            return fig

        def _generate_bar_chart_figure(prioritized_schedule):
            """
            Creates a bar chart figure for task status over time.
            X-axis: Time
            Y-axis: Number of Tasks
            Bars:
              - Number of Scheduled Tasks for this Month
              - Number of Executed Tasks for this Month
              - Number of Deferred Tasks for this Month
            """
            fig = go.Figure()

            numbers_of_scheduled = []
            numbers_of_executed = []
            numbers_of_deferred = []

            month_datetime_periods = prioritized_schedule.keys()
            month_names = [month.start_time.strftime("%Y-%m") for month in month_datetime_periods]
            # for m in month_names[:10]:
            #     print(f"Month: {m}")

            for month in prioritized_schedule:
                numbers_of_scheduled.append(len(prioritized_schedule[month].get('tasks_scheduled_for_month')))
                numbers_of_executed.append(len(prioritized_schedule[month].get('executed_tasks')))
                numbers_of_deferred.append(len(prioritized_schedule[month].get('deferred_tasks')))

            print(f"Most Scheduled Tasks: {max(numbers_of_scheduled)}")
            print(f"Most Executed Tasks: {max(numbers_of_executed)}")
            print(f"Most Deferred Tasks: {max(numbers_of_deferred)}")

            fig.add_trace(go.Bar(x=month_names, y=numbers_of_scheduled, name='Scheduled', marker_color='blue'))
            fig.add_trace(go.Bar(x=month_names, y=numbers_of_executed, name='Executed', marker_color='green'))
            fig.add_trace(go.Bar(x=month_names, y=numbers_of_deferred, name='Deferred', marker_color='red'))

            fig.update_layout(title='Task Status Over Time', xaxis_title='Time', yaxis_title='Number of Tasks')
            fig.update_yaxes(range=[0, max_tasks + 10])

            # Show no x axis tick marks
            fig.update_xaxes(showticklabels=False)

            return fig

        def update_task_pane(event):
            # Update the task list pane based on the selected month
            if graph_number_input.value != event.new:
                graph_number_input.value = event.new
            graph_index = event.new - 1
            if 0 <= graph_index < number_of_graphs:
                month = months[graph_index]
                tasks_scheduled_for_month = prioritized_schedule[month].get('tasks_scheduled_for_month')
                executed_tasks = prioritized_schedule[month].get('executed_tasks')
                deferred_tasks = prioritized_schedule[month].get('deferred_tasks')
                task_list_plot.object = _generate_task_list_figure(tasks_scheduled_for_month, executed_tasks, deferred_tasks, max_tasks)

        def update_number_input(event):
            # Keep slider in sync with number input
            if graph_slider.value != event.new:
                graph_slider.value = event.new
        graph_slider.param.watch(update_graph, 'value')
        graph_slider.param.watch(update_task_pane, 'value')
        graph_number_input.param.watch(update_number_input, 'value')
        # Display the first graph by default
        if number_of_graphs > 0:
            month = months[0]
            current_month_pane.object = f"**Current Month:** {month}"
            graph_snapshot = prioritized_schedule[month].get('graph')
            fig = visualize_rul_graph(graph_snapshot, use_full_names=name_toggle.value, month=month, show_end_loads=show_end_loads_toggle.value)
            graph_pane.object = fig

            # Update the task list pane
            tasks_scheduled_for_month = prioritized_schedule[month].get('tasks_scheduled_for_month')
            executed_tasks = prioritized_schedule[month].get('executed_tasks')
            deferred_tasks = prioritized_schedule[month].get('deferred_tasks')
            task_list_plot.object = _generate_task_list_figure(tasks_scheduled_for_month, executed_tasks, deferred_tasks, max_tasks)

            # Update the line chart pane
            bar_chart_pane.object = _generate_bar_chart_figure(prioritized_schedule)
# Add inputs for maintenance task parameters

# Create a slider and number input for graph selection
graph_slider = pn.widgets.IntSlider(
    name="Select Graph",
    start=1,
    end=36,  # Default end value, will be updated later
    value=1,
    step=1
)
graph_number_input = pn.widgets.IntInput(
    name="Graph #",
    value=1,
    step=1,
    start=1,
    end=36
)
task_list_plot = pn.pane.Plotly(height=600, sizing_mode='stretch_width')

# Show both slider and number input together
app.append(pn.Column(
    "### Prioritized Maintenance Schedule",
    pn.Row(graph_slider, graph_number_input, animation_controls),
    current_month_pane,
    bar_chart_pane,
    pn.Row(graph_pane, task_list_plot),
    sizing_mode='stretch_width'
))

monthly_budget_time_input = pn.widgets.TextInput(name="Monthly Budget (Time)", value="50")
monthly_budget_money_input = pn.widgets.TextInput(name="Monthly Budget (Money)", value="20000")
show_end_loads_toggle = pn.widgets.Checkbox(name="Show End Loads", value=False)
num_months_input = pn.widgets.TextInput(name="Months to Schedule", value="1000")
tasks_file_input = pn.widgets.FileInput(name="Tasks File", accept='.csv')
replacement_tasks_file_input = pn.widgets.FileInput(name="Replacement Tasks File", accept='.csv')
process_tasks_button = pn.widgets.Button(name="Process Tasks", button_type="primary")

maintenance_task_panel = pn.Column(
    pn.Row(monthly_budget_time_input, monthly_budget_money_input, show_end_loads_toggle),
    pn.Row(num_months_input),
    pn.Row(tasks_file_input, replacement_tasks_file_input),
    process_tasks_button
)

# Set up the button callback
process_tasks_button.on_click(process_tasks_callback)
# Automatically process tasks when graph is loaded
def auto_process_tasks_if_graph_loaded():
    if current_graph[0] is not None:
        process_tasks_callback()

auto_process_tasks_if_graph_loaded()  # Initial call to populate the app if graph is already loaded

app.append(pn.Column(
    "### Process Maintenance Tasks",
    maintenance_task_panel,
    sizing_mode='stretch_width'
))

if current_graph[0] is not None:
    testing_section = pn.Column("### RUL Testing & Parameter Controls")
    
    # Component condition testing
    condition_test_row = pn.Row()
    
    test_component_select = pn.widgets.Select(
        name="Select Component",
        options=[n for n, d in current_graph[0].nodes(data=True) if d.get('type') != 'end_load'],
        width=250
    )
    
    test_condition_slider = pn.widgets.FloatSlider(
        name="Set Condition (0=Broken, 1=Perfect)",
        start=0.0, end=1.0, step=0.05, value=0.8, width=300
    )
    
    test_update_btn = pn.widgets.Button(name="Update Condition", button_type="primary", width=150)
    test_status = pn.pane.Markdown("Ready to test component conditions", width=400)
    
    def test_update_condition(event):
        if test_component_select.value and current_graph[0]:
            try:
                from helpers.rul_helper import update_component_condition
                success = update_component_condition(
                    current_graph[0], 
                    test_component_select.value, 
                    test_condition_slider.value,
                    "Manual test update"
                )
                if success:
                    test_status.object = f"✅ Updated {test_component_select.value} condition to {test_condition_slider.value:.2f}"
                    # Refresh visualizations
                    plot_pane.object = visualize_graph_two_d(current_graph[0], use_full_names=name_toggle.value)
                else:
                    test_status.object = "❌ Update failed"
            except Exception as e:
                test_status.object = f"❌ Error: {str(e)}"
        else:
            test_status.object = "❌ No component selected or graph missing"

    test_update_btn.on_click(test_update_condition)
    
    condition_test_row.extend([test_component_select, test_condition_slider, test_update_btn])
    
    # Parameter adjustment controls
    param_control_row = pn.Row()
    
    deferment_factor_slider = pn.widgets.FloatSlider(
        name="Task Deferment Factor", 
        start=0.01, end=0.10, step=0.01, value=0.04, width=250
    )
    
    aging_factor_slider = pn.widgets.FloatSlider(
        name="Aging Acceleration Factor",
        start=0.01, end=0.05, step=0.005, value=0.02, width=250
    )
    
    update_params_btn = pn.widgets.Button(name="Update Parameters", button_type="success", width=150)
    params_status = pn.pane.Markdown("Ready to test parameters", width=400)
    
    def update_parameters(event):
        try:
            from helpers.rul_helper import adjust_rul_parameters, apply_rul_to_graph
            changes = adjust_rul_parameters(
                TASK_DEFERMENT_FACTOR=deferment_factor_slider.value,
                AGING_ACCELERATION_FACTOR=aging_factor_slider.value
            )
            
            # Recalculate RUL with new parameters
            apply_rul_to_graph(current_graph[0])
            
            # Refresh visualization
            plot_pane.object = visualize_graph_two_d(current_graph[0], use_full_names=name_toggle.value)
            
            params_status.object = f"✅ Updated parameters and recalculated RUL"
        except Exception as e:
            params_status.object = f"❌ Error: {str(e)}"
    
    update_params_btn.on_click(update_parameters)
    
    param_control_row.extend([deferment_factor_slider, aging_factor_slider, update_params_btn])
    
    # Quick condition presets
    preset_row = pn.Row()
    
    simulate_wear_btn = pn.widgets.Button(name="Simulate Equipment Wear", button_type="light", width=200)
    reset_conditions_btn = pn.widgets.Button(name="Reset All to Perfect", button_type="warning", width=200)
    preset_status = pn.pane.Markdown("Ready for quick actions", width=400)
    
    def simulate_wear(event):
        try:
            from helpers.rul_helper import update_component_condition
            count = 0
            for node_id, attrs in current_graph[0].nodes(data=True):
                if attrs.get('type') != 'end_load':
                    # Simulate random wear between 0.3 and 0.9
                    import random
                    wear_condition = random.uniform(0.3, 0.9)
                    update_component_condition(current_graph[0], node_id, wear_condition, "Simulated wear")
                    count += 1
            
            plot_pane.object = visualize_graph_two_d(current_graph[0], use_full_names=name_toggle.value)
            preset_status.object = f"✅ Simulated wear on {count} components"
        except Exception as e:
            preset_status.object = f"❌ Error: {str(e)}"
    
    def reset_conditions(event):
        try:
            from helpers.rul_helper import reset_all_conditions
            count = reset_all_conditions(current_graph[0], 1.0, "Reset to perfect")
            plot_pane.object = visualize_graph_two_d(current_graph[0], use_full_names=name_toggle.value)
            preset_status.object = f"✅ Reset {count} components to perfect condition"
        except Exception as e:
            preset_status.object = f"❌ Error: {str(e)}"
    
    
    simulate_wear_btn.on_click(simulate_wear)
    reset_conditions_btn.on_click(reset_conditions)
    
    preset_row.extend([simulate_wear_btn, reset_conditions_btn])
    
    # Assemble testing section
    testing_section.extend([
        "**Component Condition Testing:**",
        condition_test_row,
        test_status,
        "**Parameter Controls:**", 
        param_control_row,
        params_status,
        "**Quick Actions:**",
        preset_row,
        preset_status
    ])
    
    app.append(testing_section)

# Register all widgets with the controller
system_controller.register_widgets({
    'file_input': file_input,
    'save_button': save_button,
    'save_input': filename_input,
    'save_status': save_status,
    'plot_pane': plot_pane,
    'plot_risk_pane': plot_risk_pane,
    'three_d_pane': three_d_pane,
    'name_toggle': name_toggle,
    'node_dropdown': node_dropdown,
    'edge_dropdown': edge_dropdown,
    'node_info_pane': node_info_pane,
    'edge_info_pane': edge_info_pane,
    'node_attr_df': node_attr_df,
    'edge_attr_df': edge_attr_df
})

# Setup all event handlers
system_controller.setup_callbacks()

# Autoload example graph if present
autoload_example_graph()

print("Starting MEP System Graph Viewer...")
app.servable()
