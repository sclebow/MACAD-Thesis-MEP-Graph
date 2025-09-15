# Copyright (C) 2025  Scott Lebow and Krisztian Hajdu

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Author contact:
# Scott Lebow: scott.lebow@student.iaac.net
# Krisztian Hajdu: krisztian.hajdu@students.iaac.net

import io
import networkx as nx
import random
import os
import plotly.graph_objs as go
import math
import datetime
import pandas as pd

from graph_generator.mepg_generator import define_building_characteristics, determine_number_of_risers, locate_risers, determine_voltage_level, distribute_loads, determine_riser_attributes, place_distribution_equipment, connect_nodes, clean_graph_none_values

from helpers.node_risk import apply_risk_scores_to_graph
from helpers.rul_helper import apply_rul_to_graph
from helpers.visualization import *
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
        self.monthly_budget_money = None  # Default budget
        self.monthly_budget_time = None  # Default budget
        self.months_to_schedule = None  # Default months to schedule
        self.prioritized_schedule = None  # Store simulation results
        self.current_date = pd.Timestamp.now()
        self.maintenance_logs = None  # Store maintenance logs
        self.seed = 42  # Default seed for reproducibility

    def run_rul_simulation(self, generate_synthetic_maintenance_logs):
        """Run a maintenance task simulation and store results in pn.state.cache"""
        print(f"Running RUL simulation with current date {self.current_date}, budget hours {self.monthly_budget_time}, budget money {self.monthly_budget_money}, weeks to schedule {self.months_to_schedule}")
        self.prioritized_schedule = process_maintenance_tasks(
            tasks=self.maintenance_tasks,
            replacement_tasks=self.replacement_tasks,
            graph=self.current_graph[0],
            monthly_budget_time=self.monthly_budget_time,
            monthly_budget_money=self.monthly_budget_money,
            months_to_schedule=self.months_to_schedule,
            current_date=self.current_date,
            generate_synthetic_maintenance_logs=generate_synthetic_maintenance_logs,
            maintenance_log_dict=self.maintenance_logs,
            seed=self.seed
        )

        # Extract the maintenance logs from the schedule
        all_logs = []

        for month, data in self.prioritized_schedule.items():
            month_logs = data.get('maintenance_logs')
            all_logs.extend(month_logs)

        print(f"Total maintenance logs collected: {len(all_logs)}")
        self.maintenance_logs = all_logs
        
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
        # """Load graph from file bytes and apply processing"""
        try:
            file_buffer = io.BytesIO(file_bytes)
            G = nx.read_graphml(file_buffer)
            
            # Validate and clean graph data
            G = self._validate_graph_data(G)
            
            # Apply risk scores and RUL with error handling
            G = apply_risk_scores_to_graph(G)
            G = apply_rul_to_graph(G)
            
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
            if 'tasks_deferred_count' not in attrs or attrs['tasks_deferred_count'] is None:
                attrs['tasks_deferred_count'] = 0 # Initialize if missing
        
        for edge in graph.edges(data=True):
            edge_attrs = edge[2]
            for key, value in edge_attrs.items():
                if value is None and key in ['voltage', 'current_rating', 'power']:
                    edge_attrs[key] = 0.0
                    print(f"Warning: Set {key} to 0.0 for edge {edge[0]}-{edge[1]}")

        return clean_graph_none_values(graph)
    
    def generate_new_graph(self, building_params):
        """Generate new graph with given parameters"""
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
        
        building_attrs = define_building_characteristics(building_attributes)
        num_risers = determine_number_of_risers(building_attrs)
        riser_locations = locate_risers(building_attrs, num_risers)
        voltage_info = determine_voltage_level(building_attrs)
        floor_loads, end_loads = distribute_loads(building_attrs, voltage_info)
        riser_floor_attributes = determine_riser_attributes(building_attrs, riser_locations, floor_loads, end_loads, voltage_info)
        distribution_equipment = place_distribution_equipment(building_attrs, riser_floor_attributes, voltage_info)
        cluster_strength = building_params.get('cluster_strength')
        graph = connect_nodes(building_attrs, riser_locations, distribution_equipment, voltage_info, end_loads, cluster_strength)

        print(f"Generated graph with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges.")
        # Apply risk scores and RUL to the graph
        graph = self._validate_graph_data(graph)
        graph = apply_risk_scores_to_graph(graph)
        graph = apply_rul_to_graph(graph)


        self.current_graph[0] = graph

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

    def get_bar_chart_figure(self):
        """Get the bar chart figure for task status over time"""
        if not self.current_graph[0]:
            return None

        return generate_bar_chart_figure(self.prioritized_schedule, self.current_date)

    def get_current_date_graph(self):
        """Get the current date graph"""
        month_periods = self.prioritized_schedule.keys()

        current_month = pd.Timestamp(self.current_date).to_period('M')
        print(f"Current month period: {current_month}")
        if current_month in month_periods:
            return self.prioritized_schedule[current_month]['graph']

        return None

    def get_previous_month_graph(self, number_of_months=1):
        """Get the previous month graph"""
        month_periods = self.prioritized_schedule.keys()

        current_month = pd.Timestamp(self.current_date).to_period('M')
        previous_month = current_month - number_of_months  # Use period arithmetic instead of DateOffset
        if previous_month in month_periods:
            return self.prioritized_schedule[previous_month]['graph']

    def get_future_month_graph(self, number_of_months=1):
        """Get the future month graph"""
        month_periods = self.prioritized_schedule.keys()

        current_month = pd.Timestamp(self.current_date).to_period('M')
        future_month = current_month + number_of_months  # Use period arithmetic instead of DateOffset
        if future_month in month_periods:
            return self.prioritized_schedule[future_month]['graph']

        return None

    def get_next_12_months_data(self):
        current_month = pd.Timestamp(self.current_date).to_period('M')
        current_month_ts = current_month.to_timestamp()
        next_12_months = [(current_month_ts + pd.DateOffset(months=i)).to_period('M') for i in range(1, 13)]
        return {month: self.prioritized_schedule.get(month, {}) for month in next_12_months}

    def get_current_date_failure_timeline_figure(self):
        """Get the failure timeline figure"""
        current_date_graph = self.get_current_date_graph()

        return generate_failure_timeline_figure(current_date_graph, self.current_date)
    
    def upload_maintenance_logs(self, file_content):
        """Upload maintenance logs from file content"""
        self.maintenance_logs = pd.read_csv(io.BytesIO(file_content))
        self.maintenance_logs = self.maintenance_logs.to_dict(orient='records')

    def get_maintenance_logs_df(self):
        """Get the maintenance logs DataFrame"""
        return pd.DataFrame(self.maintenance_logs)
    
    def get_current_condition_level_df(self, ignore_end_loads=True):
        """Get the current condition level DataFrame"""
        current_date_graph = self.get_current_date_graph()

        node_condition_dict = {}        
        for node_id, attrs in current_date_graph.nodes(data=True):
            if ignore_end_loads and attrs.get('type') == 'end_load':
                continue
            node_condition_dict[node_id] = {
                'Node ID': node_id,
                'Condition Level': attrs.get('current_condition', 'N/A'),
                'RUL (months)': attrs.get('remaining_useful_life_days'),
                'Expected Lifespan (years)': attrs.get('expected_lifespan', 'N/A'),
                'Tasks Deferred Count': attrs.get('tasks_deferred_count', 0)
            }
        return pd.DataFrame.from_dict(node_condition_dict, orient='index')


    def export_data(self):
        """Export current graph and related data as a dictionary"""
        if not self.current_graph[0]:
            return None
        
        data_dict = {
            'graph': self.current_graph[0],
            'maintenance_tasks': self.maintenance_tasks,
            'replacement_tasks': self.replacement_tasks,
            'monthly_budget_money': self.monthly_budget_money,
            'monthly_budget_time': self.monthly_budget_time,
            'months_to_schedule': self.months_to_schedule,
            'prioritized_schedule': self.prioritized_schedule,
            'current_date': self.current_date,
            'maintenance_logs': self.maintenance_logs
        }
        return data_dict

    def get_budget_overview_df(self):
        """Get a DataFrame summarizing used vs. remaining budget"""
        if not self.prioritized_schedule:
            return pd.DataFrame(columns=['Month', 'Used Hours', 'Remaining Hours', 'Used Money', 'Remaining Money'])
        
        budget_data = []
        for month, data in self.prioritized_schedule.items():
            used_hours = 0
            used_money = 0
            for task in data.get('executed_tasks'):
                used_hours += task.get('time_cost')
                used_money += task.get('money_cost')
            
            for task in data.get('replacement_tasks_executed'):
                used_hours += task.get('time_cost')
                used_money += task.get('money_cost')

            remaining_hours = (self.monthly_budget_time or 0) - used_hours
            remaining_money = (self.monthly_budget_money or 0) - used_money
            
            budget_data.append({
                'Month': month.strftime('%Y-%m'),
                'Used Hours': used_hours,
                'Remaining Hours': max(remaining_hours, 0),
                'Used Money': used_money,
                'Remaining Money': max(remaining_money, 0)
            })
        
        return pd.DataFrame(budget_data)
    
    def get_average_money_budget_used(self):
        """Get average money budget used per month"""
        
        total_used = 0.0
        months_counted = 0
        for month, data in self.prioritized_schedule.items():
            month_used = sum(task.get('money_cost', 0) for task in data.get('executed_tasks'))
            month_used += sum(task.get('money_cost', 0) for task in data.get('replacement_tasks_executed'))
            total_used += month_used
            months_counted += 1
        
        return total_used / months_counted if months_counted > 0 else 0.0
    
    def get_average_hours_budget_used(self):
        """Get average hours budget used per month"""
        
        total_used = 0.0
        months_counted = 0
        for month, data in self.prioritized_schedule.items():
            month_used = sum(task.get('time_cost', 0) for task in data.get('executed_tasks'))
            month_used += sum(task.get('time_cost', 0) for task in data.get('replacement_tasks_executed'))
            total_used += month_used
            months_counted += 1
        
        return total_used / months_counted if months_counted > 0 else 0.0
    
    def get_average_RUL_of_simulation(self):
        """Get average RUL of all components in the prioritized schedule"""
        
        if not self.prioritized_schedule:
            return None
        
        total_rul = 0.0
        count = 0
        for month, data in self.prioritized_schedule.items():
            for node_id, attrs in data.get('graph').nodes(data=True):
                if 'remaining_useful_life_days' not in attrs:
                    continue
                rul = attrs.get('remaining_useful_life_days')
                total_rul += rul
                count += 1
        
        return (total_rul / count) if count > 0 else None
    
    def get_average_condition_level_of_simulation(self):
        """Get average condition level of all components in the prioritized schedule"""
        
        if not self.prioritized_schedule:
            return None
        
        total_condition = 0.0
        count = 0
        for month, data in self.prioritized_schedule.items():
            for node_id, attrs in data.get('graph').nodes(data=True):
                if 'current_condition' not in attrs:
                    continue
                condition = attrs.get('current_condition')
                total_condition += condition
                count += 1
        
        return (total_condition / count) if count > 0 else None