import networkx as nx
import plotly.graph_objects as go
import math
import random
import datetime
import plotly.express as px
import pandas as pd

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

def _generate_2d_graph_figure(graph, use_full_names=False, node_color_values=None, color_palette=None, colorbar_title=None, showlegend=False, colorbar_range=None, hide_trace_from_legend=False, legend_settings=None, graph_title=None):
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

    # Create legend configuration based on settings
    legend_config = {}
    if showlegend and legend_settings:
        legend_config = dict(
            x=legend_settings.get('x', 0.98),
            y=legend_settings.get('y', 0.98), 
            xanchor=legend_settings.get('xanchor', 'right'),
            yanchor=legend_settings.get('yanchor', 'top'),
            bgcolor=legend_settings.get('bgcolor', 'rgba(255,255,255,0.95)'),
            bordercolor='rgba(0,0,0,0.5)',
            borderwidth=1,
            font=dict(size=legend_settings.get('font_size', 8)),
            itemwidth=30,
            itemsizing='constant',
            tracegroupgap=0,
            orientation='v',
            itemclick='toggleothers',
            itemdoubleclick='toggle',
            entrywidth=legend_settings.get('entrywidth', 0.5),
            entrywidthmode='fraction'
        )
        
        annotations = []
    elif showlegend:
        # Default legend config
        legend_config = dict(
            x=0.98, y=0.98, xanchor='right', yanchor='top',
            bgcolor='rgba(255,255,255,0.95)', bordercolor='rgba(0,0,0,0.5)',
            borderwidth=1, font=dict(size=8), itemwidth=30, itemsizing='constant',
            tracegroupgap=0, orientation='v', itemclick='toggleothers',
            itemdoubleclick='toggle', entrywidth=0.5, entrywidthmode='fraction'
        )
        
        annotations = []
    else:
        annotations = []

    fig = go.Figure(data=[edge_trace, edge_marker_trace] + node_traces,
                    layout=go.Layout(
                        showlegend=showlegend and legend_settings is not None,
                        hovermode='closest',
                        margin=dict(b=20,l=5,r=5,t=40),
                        legend=legend_config,
                        annotations=annotations,
                        xaxis=dict(
                            showgrid=False, 
                            zeroline=False, 
                            showticklabels=False,
                            domain=[0, 1]  # Graph uses full width
                        ),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                    ))

    if hide_trace_from_legend:
        # Remove just traces from legend
        for trace in fig.data:
            if hasattr(trace, 'mode') and 'lines' in str(trace.mode):
                trace.showlegend = False
            if hasattr(trace, 'name') and not trace.name:
                trace.showlegend = False

    if graph_title:
        fig.update_layout(title=graph_title)        

    return fig

def visualize_graph_two_d(graph, use_full_names=False, legend_settings=None):
    return _generate_2d_graph_figure(graph, use_full_names=use_full_names, showlegend=True, hide_trace_from_legend=True, legend_settings=legend_settings, graph_title='Graph Colored by Type')

def visualize_graph_two_d_risk(graph, use_full_names=False, legend_settings=None):
    # Color nodes by risk_score attribute
    risk_scores = {n: graph.nodes[n].get('risk_score', 0) for n in graph.nodes}
    return _generate_2d_graph_figure(
        graph,
        use_full_names=use_full_names,
        node_color_values=risk_scores,
        color_palette='Inferno',
        colorbar_title='Risk Score',
        showlegend=False,
        legend_settings=legend_settings,
        graph_title='Graph Colored by Risk Score',
    )

def visualize_graph_three_d(graph, use_full_names=False, legend_settings=None):
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
    # Create legend configuration based on settings  
    legend_config = {}
    if legend_settings:
        legend_config = dict(
            x=legend_settings.get('x', 0.98),
            y=legend_settings.get('y', 0.98), 
            xanchor=legend_settings.get('xanchor', 'right'),
            yanchor=legend_settings.get('yanchor', 'top'),
            bgcolor=legend_settings.get('bgcolor', 'rgba(255,255,255,0.95)'),
            bordercolor='rgba(0,0,0,0.5)',
            borderwidth=1,
            font=dict(size=legend_settings.get('font_size', 8)),
            itemwidth=30,
            itemsizing='constant',
            tracegroupgap=0,
            orientation='v',
            itemclick='toggleothers',
            itemdoubleclick='toggle',
            entrywidth=legend_settings.get('entrywidth', 0.5),
            entrywidthmode='fraction'
        )
        
        annotations = []
    else:
        # Default legend config
        legend_config = dict(
            x=0.98, y=0.98, xanchor='right', yanchor='top',
            bgcolor='rgba(255,255,255,0.95)', bordercolor='rgba(0,0,0,0.5)',
            borderwidth=1, font=dict(size=8), itemwidth=30, itemsizing='constant',
            tracegroupgap=0, orientation='v', itemclick='toggleothers',
            itemdoubleclick='toggle', entrywidth=0.5, entrywidthmode='fraction'
        )
        
        annotations = []

    fig = go.Figure(data=fig_data,
                    layout=go.Layout(
                        showlegend=legend_settings is not None,
                        hovermode='closest',
                        margin=dict(b=20,l=5,r=5,t=40),
                        legend=legend_config,
                        annotations=annotations,
                        scene=dict(
                            domain=dict(x=[0, 1], y=[0, 1]),  # 3D scene uses full area
                            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=axis_range),
                            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=axis_range),
                            zaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=axis_range)
                        )
                    ))
    
    fig.update_layout(title='3D Graph Colored by Type')
    
    return fig

def generate_bar_chart_figure(prioritized_schedule, current_date: pd.Timestamp):
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

    numbers_of_executed = []
    numbers_of_deferred = []

    month_datetime_periods = prioritized_schedule.keys()
    month_names = [month.start_time.strftime("%Y-%m") for month in month_datetime_periods]

    for month in prioritized_schedule:
        numbers_of_executed.append(len(prioritized_schedule[month].get('executed_tasks')))
        numbers_of_deferred.append(len(prioritized_schedule[month].get('deferred_tasks')))

    # Create stacked bar chart - order matters for stacking
    fig.add_trace(go.Bar(
        x=month_names, 
        y=numbers_of_executed, 
        name='Executed', 
        marker_color='green',
        hovertemplate='<b>%{x}</b><br>Executed: %{y}<extra></extra>'
    ))
    fig.add_trace(go.Bar(
        x=month_names, 
        y=numbers_of_deferred, 
        name='Deferred', 
        marker_color='red',
        hovertemplate='<b>%{x}</b><br>Deferred: %{y}<extra></extra>'
    ))

    fig.update_layout(
        title='Task Status Each Month', 
        xaxis_title='Time', 
        yaxis_title='Number of Tasks',
        barmode='stack'  # This makes it a stacked bar chart
    )

    # Ensure zoom buttons only affect x-axis, default range is last 6 months + next 12 months
    default_range = [
        (current_date - pd.DateOffset(months=6)).to_pydatetime(),
        (current_date + pd.DateOffset(months=12)).to_pydatetime()
    ]
    default_range_count = default_range[1].month - default_range[0].month + (default_range[1].year - default_range[0].year) * 12

    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=3, label="3m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all")
                ])
            ),
            rangeslider=dict(visible=True),
            type="date",
            range=default_range
        )
    )

    # Add a button to reset the x-axis range to default
    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                buttons=[
                    dict(
                        label="Reset Zoom",
                        method="relayout",
                        args=[{
                            "xaxis.range": default_range,
                            "xaxis.count": default_range_count
                        }]
                    )
                ],
                pad={"r": 10, "t": 10},
                showactive=False,
                x=1.025,
                xanchor="left",
                y=0.8,
                yanchor="top"
            ),
        ]
    )

    # Add a vertical line for the current date
    current_date_dt = pd.to_datetime(current_date).to_pydatetime()
    fig.add_vline(x=current_date_dt, line=dict(color='red', dash='dash'))
    # Add annotation for the current date
    fig.add_annotation(
        x=current_date_dt,
        y=1,
        yref='paper',
        text="Current Date",
        showarrow=False,
        xanchor='left',
        yanchor='bottom',
        font=dict(color='red')
    )

    return fig

def generate_failure_timeline_figure(graph: nx.Graph, current_date: pd.Timestamp):
    """
    Creates a timeline figure for node failures over time.
    X-axis: Time
    Each node is a dot based on its remaining useful life (RUL).
    """

    # Remove end_load types from the graph
    nodes = []
    for node_id, node_data in graph.nodes(data=True):
        if node_data.get('type') != 'end_load':
            nodes.append((node_id, node_data))

    min_marker_size = 15
    max_marker_size = 50

    fig = go.Figure()

    node_dict = {}

    for node_id, node_data in nodes:
        rul_days = node_data.get('remaining_useful_life_days')
        if rul_days is not None:
            node_dict[node_id] = {
                'rul_days': rul_days,
                'type': node_data.get('type'),
                'risk_score': node_data.get('risk_score'),
                'date': current_date + datetime.timedelta(days=rul_days),
                'risk_level': node_data.get('risk_level')
            }

    # Sort node_dict by date
    node_dict = dict(sorted(node_dict.items(), key=lambda item: item[1]['date']))

    # Size markers based on risk scores
    risk_scores = [node['risk_score'] for node in node_dict.values()]
    marker_sizes = [
        min_marker_size + (max_marker_size - min_marker_size) * (risk_score / max(risk_scores)) if max(risk_scores) > 0 else min_marker_size
        for risk_score in risk_scores
    ]
    
    types = [node['type'] for node in node_dict.values()]
    unique_types = list(sorted(set(types)))
    type_colors = [px.colors.qualitative.Plotly[i % len(px.colors.qualitative.Plotly)] for i in range(len(unique_types))]

    type_color_dict = {t: type_colors[i] for i, t in enumerate(unique_types)}

    node_colors = []
    for t in types:
        node_colors.append(type_color_dict.get(t))

    fig.add_trace(go.Scatter(
        x=[node['date'] for node in node_dict.values()],
        y=list(node_dict.keys()),
        mode='markers',
        marker=dict(size=marker_sizes, color=node_colors),
        hovertext=[
            f"Node: {node_id}<br>"
            f"Type: {node['type']}<br>"
            f"Risk Score: {node['risk_score']}<br>"
            f"RUL (days): {node['rul_days']}<br>"
            f"Failure Date: {node['date']}<br>"
            f"Risk Level: {node['risk_level']}"
            for node_id, node in node_dict.items()
        ],
        hoverinfo='text'
    ))

    # Add a legend
    for t in unique_types:
        fig.add_trace(go.Scatter(
            x=[None],
            y=[None],
            mode='markers',
            marker=dict(size=marker_sizes[0], color=type_color_dict.get(t)),
            name=t
        ))
        
    # Remove traces from the legend
    for trace in fig.data:
        if hasattr(trace, 'mode') and 'lines' in str(trace.mode):
            trace.showlegend = False
        if hasattr(trace, 'name') and not trace.name:
            trace.showlegend = False

    fig.update_layout(showlegend=True)

    fig.update_layout(title='Node Failure Timeline', xaxis_title='Failure Date', yaxis_title='Equipment ID')

    # Add invisible trace to force secondary x-axis to appear
    fig.add_trace(go.Scatter(
        x=[node['date'] for node in list(node_dict.values())[:1]],  # Just first date
        y=[list(node_dict.keys())[0]] if node_dict else [None],     # Just first node
        mode='markers',
        marker=dict(size=0.1, color='rgba(0,0,0,0)'),  # Completely transparent
        xaxis='x2',  # Assign to secondary x-axis
        showlegend=False,
        hoverinfo='skip'
    ))

    # Show xlabels at the top and bottom
    fig.update_layout(
        xaxis2=dict(
            title='Failure Date',
            overlaying='x', 
            side="top",
            showticklabels=True,
            matches='x'  # Sync with primary x-axis
        )
    )

    # Add a vertical line for the current date
    current_date_dt = pd.to_datetime(current_date).to_pydatetime()
    fig.add_vline(x=current_date_dt, line=dict(color='red', dash='dash'))
    # Add annotation for the current date
    fig.add_annotation(
        x=current_date_dt,
        y=1,
        yref='paper',
        text="Current Date",
        showarrow=False,
        xanchor='left',
        yanchor='bottom',
        font=dict(color='red')
    )

    # Update the height based on number of nodes
    fig.update_layout(height=300 + 20 * len(node_dict), title='Node Failure Timeline')

    return fig, node_dict

def get_equipment_conditions_fig(graphs: list[nx.Graph], periods: list, current_date: datetime) -> go.Figure:
    """Get the remaining useful life figure for the given graphs."""

    data_dict_list = []

    for period, graph in zip(periods, graphs):
        for node, attrs in graph.nodes(data=True):
            node_type = attrs.get('type')
            if node_type != 'end_load':
                data_dict_list.append({
                    'node': node,
                    'type': node_type,
                    'period': period,
                    'remaining_useful_life_days': attrs.get('remaining_useful_life_days')
                })

    data_df = pd.DataFrame(data_dict_list)

    # Group by period and type, and calculate the average remaining useful life
    grouped = data_df.groupby(['period', 'type'])['remaining_useful_life_days'].mean().reset_index()

    # Convert period to timestamp
    grouped['period'] = grouped['period'].dt.to_timestamp()

    # Create the figure
    fig = go.Figure()

    # X-axis is period, Y-axis is average remaining useful life, different lines for each type
    for node_type in grouped['type'].unique():
        filtered = grouped[grouped['type'] == node_type]
        fig.add_trace(go.Scatter(
            x=filtered['period'],
            y=filtered['remaining_useful_life_days'],
            mode='lines+markers',
            name=node_type
        ))

    # Add a vertical line for the current date
    current_date_dt = pd.to_datetime(current_date).to_pydatetime()
    fig.add_vline(x=current_date_dt, line=dict(color='red', dash='dash'))
    # Add annotation for the current date
    fig.add_annotation(
        x=current_date_dt,
        y=1,
        yref='paper',
        text="Current Date",
        showarrow=False,
        xanchor='left',
        yanchor='bottom',
        font=dict(color='red')
    )
    
    default_range = [
        (current_date - pd.DateOffset(months=24)).to_pydatetime(),
        (current_date + pd.DateOffset(months=60)).to_pydatetime()
    ]

    # Add time range selector
    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=3, label="3m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all")
                ])
            ),
            rangeslider=dict(visible=True),
            type="date",
            range=default_range
        )
    )

    # Add a button to reset the x-axis range to default
    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                x=1,
                y=1.15,
                showactive=False,
                buttons=[
                    dict(
                        label="Reset X-Axis",
                        method="relayout",
                        args=[{"xaxis.range": default_range}],
                    )
                ],
            )
        ]
    )

    fig.update_layout(
        xaxis_title='Time Range',
        yaxis_title='RUL', 
        title='Average Remaining Useful Life by Equipment Type Over Time'
    )

    return fig

def get_risk_distribution_fig(current_date_graph: nx.Graph):
    """Create a pie chart of the risk distribution."""
    fig = go.Figure()

    # Get the node types and their corresponding colors
    node_conditions = {node: attrs.get('risk_level') for node, attrs in current_date_graph.nodes(data=True)}
    condition_counts = pd.Series(node_conditions).value_counts()

    fig.add_trace(go.Pie(
        labels=condition_counts.index,
        values=condition_counts.values,
        hole=0.4
    ))

    fig.update_layout(title='Risk Level Distribution')

    return fig

def get_remaining_useful_life_fig(current_date_graph: nx.Graph):
    """Create a bar chart of the remaining useful life for each equipment."""
    fig = go.Figure()

    # Get the remaining useful life values
    rul_values = [attrs.get('remaining_useful_life_days') for node, attrs in current_date_graph.nodes(data=True) if attrs.get('remaining_useful_life_days') is not None]
    node_ids = [node for node, attrs in current_date_graph.nodes(data=True) if attrs.get('remaining_useful_life_days') is not None]

    # Sort by rul_values
    sorted_indices = sorted(range(len(rul_values)), key=lambda i: rul_values[i])
    node_ids = [node_ids[i] for i in sorted_indices]
    rul_values = [rul_values[i] for i in sorted_indices]

    fig.add_trace(go.Bar(
        x=node_ids,
        y=rul_values,
        marker=dict(
            color=rul_values,
            colorscale='Agsunset',
            colorbar=dict(title='RUL (days)')
        ),
    ))
    fig.update_layout(yaxis_title='Days', xaxis_title='Equipment', title='Remaining Useful Life of Equipment')

    return fig

def get_maintenance_costs_fig(prioritized_schedule: dict, current_date: pd.Timestamp, number_of_previous_months: int=12, number_of_future_months: int=24):
    """Create a line chart of monthly total maintenance costs."""
    # Get period of current date
    current_period = pd.Period(current_date, freq='M')

    # Use all periods in the prioritized_schedule to ensure continuity
    start_period = min(prioritized_schedule.keys())
    end_period = max(prioritized_schedule.keys())
    
    all_periods = pd.period_range(
        start=start_period,
        end=end_period,
        freq='M'
    )

    # Filter the prioritized_schedule by periods
    filtered_schedule = {k: v for k, v in prioritized_schedule.items() if k in all_periods}

    executed_tasks_lists = [v.get('executed_tasks') for v in filtered_schedule.values()]

    executed_replacement_tasks_lists = [v.get('replacement_tasks_executed', []) for v in filtered_schedule.values()]

    total_money_costs = []
    total_maintenance_costs = []
    total_replacement_costs = []
    for executed_task_list, executed_replacement_task_list in zip(executed_tasks_lists, executed_replacement_tasks_lists):
        total_money_cost = 0
        total_maintenance_cost = 0
        total_replacement_cost = 0
        for task in executed_task_list:
            money_cost = task.get('money_cost')
            total_money_cost += money_cost
            total_maintenance_cost += money_cost
        for task in executed_replacement_task_list:
            money_cost = task.get('money_cost')
            total_money_cost += money_cost
            total_replacement_cost += money_cost
        total_money_costs.append(total_money_cost)
        total_maintenance_costs.append(total_maintenance_cost)
        total_replacement_costs.append(total_replacement_cost)

    # Convert periods to datetime
    all_periods = all_periods.to_timestamp()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=all_periods,
        y=total_money_costs,
        mode='lines+markers',
        name='Total Combined Costs',
        fill='tozeroy',
        line=dict(shape='spline')
    ))
    fig.add_trace(go.Scatter(
        x=all_periods,
        y=total_maintenance_costs,
        mode='lines+markers',
        name='Maintenance Costs',
        fill='tozeroy',
        line=dict(shape='spline')
    ))
    fig.add_trace(go.Scatter(
        x=all_periods,
        y=total_replacement_costs,
        mode='lines+markers',
        name='Replacement Costs',
        fill='tozeroy',
        line=dict(shape='spline')
    ))
    fig.update_layout(xaxis_title='Period', yaxis_title='Cost in Period (Dollars)', title='Total Maintenance Costs Over Time')

    # Add a vertical line for the current date
    current_date_dt = pd.to_datetime(current_date).to_pydatetime()
    fig.add_vline(x=current_date_dt, line=dict(color='red', dash='dash'))
    # Add annotation for the current date
    fig.add_annotation(
        x=current_date_dt,
        y=1,
        yref='paper',
        text="Current Date",
        showarrow=False,
        xanchor='left',
        yanchor='bottom',
        font=dict(color='red')
    )

    default_range = [
        (current_date - pd.DateOffset(months=number_of_previous_months)).to_pydatetime(),
        (current_date + pd.DateOffset(months=number_of_future_months)).to_pydatetime()
    ]

    # Add time range selector
    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=3, label="3m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all")
                ])
            ),
            rangeslider=dict(visible=True),
            type="date",
            range=default_range
        )
    )
    # Add a button to reset the x-axis range to default
    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                x=1,
                y=1.15,
                showactive=False,
                buttons=[
                    dict(
                        label="Reset X-Axis",
                        method="relayout",
                        args=[{"xaxis.range": default_range}],
                    )
                ], 
            )
        ]
    )

    # Add vertical hover mode
    fig.update_layout(hovermode='x unified')

    return fig