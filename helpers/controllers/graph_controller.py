import io
import networkx as nx
import random
import os
import plotly.graph_objs as go
import math
import datetime

from graph_generator.mepg_generator import generate_mep_graph, define_building_characteristics, determine_number_of_risers, locate_risers, determine_voltage_level, distribute_loads, determine_riser_attributes, place_distribution_equipment, connect_nodes
from graph_generator.mepg_generator import clean_graph_none_values

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

    def reset_graph(self):
        """Reset the graph controller"""
        self.__init__()