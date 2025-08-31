import io
import networkx as nx
import random
import os
import plotly.graph_objs as go
import math
import datetime
import pandas as pd

from graph_generator.mepg_generator import generate_mep_graph, define_building_characteristics, determine_number_of_risers, locate_risers, determine_voltage_level, distribute_loads, determine_riser_attributes, place_distribution_equipment, connect_nodes, clean_graph_none_values

from helpers.visualization import visualize_graph_two_d, visualize_graph_two_d_risk, visualize_graph_three_d

from helpers.maintenance_tasks import process_maintenance_tasks

class GraphController:
    def __init__(self):
        self.current_graph = [None]  # Keep existing format for compatibility
        self.view_settings = {
            'use_full_names': False,
            'visualization_type': '2d_type'
        }
        self.legend_preset = "compact_tr"  # Default preset
        self.maintenance_tasks = None
        self.replacement_tasks = None
        self.monthly_budget_money = 10000.0  # Default budget
        self.monthly_budget_time = 40.0  # Default budget
        self.months_to_schedule = 360  # Default months to schedule

    def run_rul_simulation(self):
        """Run a maintenance task simulation and store results in pn.state.cache"""

        process_maintenance_tasks(
            tasks=self.maintenance_tasks,
            replacement_tasks=self.replacement_tasks,
            graph=self.current_graph[0],
            monthly_budget_time=self.monthly_budget_time,
            monthly_budget_money=self.monthly_budget_money,
            months_to_schedule=self.months_to_schedule,
        )
        
    def get_legend_settings(self):
        """Get legend configuration based on current preset"""
        presets = {
            "compact_tr": {
                'x': 0.98, 'y': 0.98, 'xanchor': 'right', 'yanchor': 'top',
                'font_size': 8, 'entrywidth': 0.4, 'bgcolor': 'rgba(255,255,255,0.9)'
            },
            "compact_tl": {
                'x': 0.02, 'y': 0.98, 'xanchor': 'left', 'yanchor': 'top',
                'font_size': 8, 'entrywidth': 0.4, 'bgcolor': 'rgba(255,255,255,0.9)'
            },
            "compact_br": {
                'x': 0.98, 'y': 0.02, 'xanchor': 'right', 'yanchor': 'bottom',
                'font_size': 8, 'entrywidth': 0.4, 'bgcolor': 'rgba(255,255,255,0.9)'
            },
            "compact_bl": {
                'x': 0.02, 'y': 0.02, 'xanchor': 'left', 'yanchor': 'bottom',
                'font_size': 8, 'entrywidth': 0.4, 'bgcolor': 'rgba(255,255,255,0.9)'
            },
            "hidden": None  # No legend
        }
        return presets.get(self.legend_preset, presets["compact_tr"])
    
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

    def update_visualization_type(self, new_type):
        """Update the visualization type"""
        self.view_settings['visualization_type'] = new_type

    def get_visualization_data(self, viz_type=None):
        """Get visualization figure for current graph"""
        if not self.current_graph[0]:
            return None
        
        viz_type = viz_type or self.view_settings['visualization_type']
        use_full_names = self.view_settings['use_full_names']
        
        if viz_type == '2d_type':
            return visualize_graph_two_d(self.current_graph[0], use_full_names, self.get_legend_settings())
        elif viz_type == '2d_risk':
            return visualize_graph_two_d_risk(self.current_graph[0], use_full_names, self.get_legend_settings())
        elif viz_type == '3d':
            return visualize_graph_three_d(self.current_graph[0], use_full_names, self.get_legend_settings())
        
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

    def upload_maintenance_task_list(self, file_content):
        """Upload task list from file content"""
        self.maintenance_tasks = pd.read_csv(io.BytesIO(file_content))
        self.maintenance_tasks = self.maintenance_tasks.to_dict(orient='records')

    def get_maintenance_task_list_df(self):
        """Get the task list DataFrame"""
        return pd.DataFrame(self.maintenance_tasks)

    def update_hours_budget(self, new_budget):
        """Update the hours budget"""
        self.monthly_budget_time = new_budget

    def update_money_budget(self, new_budget):
        """Update the money budget"""
        self.monthly_budget_money = new_budget

    def update_weeks_to_schedule(self, new_weeks):
        """Update the weeks to schedule"""
        self.months_to_schedule = new_weeks

    def upload_replacement_task_list(self, file_content):
        """Upload replacement task list from file content"""
        self.replacement_tasks = pd.read_csv(io.BytesIO(file_content))
        self.replacement_tasks = self.replacement_tasks.to_dict(orient='records')

    def get_replacement_task_list_df(self):
        """Get the replacement task list DataFrame"""
        return pd.DataFrame(self.replacement_tasks)