"""
Maintenance Task List Helper

This module will provide functions to generate, import, and prioritize maintenance tasks for MEP equipment based on the generated graph.

The goal is to:
- Import a maintenance task list from a CSV file
- Define the structure and columns of the maintenance task list
- Provide placeholder functions for prioritizing and managing tasks

---




# =============================
# GENERIC TASK TEMPLATE STRUCTURE
# =============================
#
# This table defines the structure for generic maintenance task templates,
# which are not tied to specific equipment instances, but to equipment types.
#
# Column Name                | Type     | Units      | Example Value         | Description
# -------------------------- | -------- | ---------- | --------------------- | ---------------------------------------------------
# task_id                    | str      | -          | T001                  | Unique identifier for the maintenance task template
# equipment_type             | str      | -          | transformer           | Type of equipment this task applies to
# task_type                  | str      | -          | inspection            | Type of maintenance (e.g., inspection, replacement)
# recommended_frequency_months| int     | months     | 12                    | Suggested interval between tasks
# description                | str      | -          | "Visual inspection of windings" | Description of the maintenance task
# default_priority           | int      | -          | 1                     | Default priority level for this task type (1=high)
# time_cost                  | float    | hours      | 2.5                   | Estimated time required to complete the task
# money_cost                 | float    | USD        | 500.0                 | Estimated cost to complete the task
# notes                      | str      | -          | "Check for oil leaks" | Free text notes or instructions

# =============================
# DETAILED TASK LIST STRUCTURE (Generated from Graph)
# =============================
#
# This table defines the structure for the detailed maintenance task list,
# which is generated for specific equipment instances in the graph using the generic templates.
#
# Column Name                | Type     | Units      | Example Value         | Description
# -------------------------- | -------- | ---------- | --------------------- | ---------------------------------------------------
# task_instance_id           | str      | -          | T001-EL1              | Unique identifier for this specific maintenance task
# equipment_id               | str      | -          | EL1                   | Unique identifier for the equipment instance (from graph)
# equipment_type             | str      | -          | transformer           | Type of equipment (copied from template)
# task_type                  | str      | -          | inspection            | Type of maintenance (copied from template)
# scheduled_date             | str/date | YYYY-MM-DD | 2025-08-01            | Date the task is scheduled
# last_maintenance_date      | str/date | YYYY-MM-DD | 2024-08-01            | Last time this equipment was maintained
# priority                   | int      | -          | 1                     | Calculated or copied from template
# time_cost                  | float    | hours      | 2.5                   | Estimated time required (from template)
# money_cost                 | float    | USD        | 500.0                 | Estimated cost (from template)
# status                     | str      | -          | pending               | Current status (pending, in_progress, complete, etc.)
# notes                      | str      | -          | "Check for oil leaks" | Free text notes or instructions

---
"""

import csv
from typing import List, Dict, Any
import datetime
from dateutil.relativedelta import relativedelta
import os
import networkx as nx
import sys
import pandas as pd
import random

try:
    from helpers.animate_maintenance_tasks import animate_prioritized_schedule
except ImportError:
    from animate_maintenance_tasks import animate_prioritized_schedule

try:
    from rul_helper import apply_rul_to_graph, apply_condition_improvement
except ImportError:
    from helpers.rul_helper import apply_rul_to_graph, apply_condition_improvement

# Placeholder: Load maintenance tasks from a CSV file
def load_maintenance_tasks(csv_path: str) -> List[Dict[str, Any]]:
    """Load generic maintenance task templates from a CSV file and return as a list of dicts. If recommended_frequency_months or money_cost is -1, set to None to indicate it should be filled from the equipment node's attributes later."""
    tasks = []
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Convert numeric fields and handle -1 as None
            for key in ['recommended_frequency_months', 'default_priority', 'time_cost', 'money_cost']:
                if key in row:
                    try:
                        val = float(row[key]) if '.' in row[key] else int(row[key])
                    except (ValueError, TypeError):
                        row[key] = None
            tasks.append(row)
    return tasks

def load_replacement_tasks(csv_path: str) -> List[Dict[str, Any]]:
    """Load condition-based replacement/repair task templates from a CSV file."""
    tasks = []
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Convert numeric fields
            for key in ['time_cost', 'money_cost', 'condition_level', 'rul_percentage_effect']:
                if key in row:
                    try:
                        row[key] = float(row[key])
                    except (ValueError, TypeError):
                        row[key] = None
            tasks.append(row)
    # Sort by condition_level descending to check for most severe tasks first
    tasks.sort(key=lambda x: x['condition_level'], reverse=True)
    return tasks

def generate_maintenance_tasks_from_graph(graph, tasks) -> List[Dict[str, Any]]:
    """
    Generate a list of maintenance tasks for each equipment node in the graph, using the generic task templates for each equipment type.
    Only include nodes whose 'type' matches a template 'equipment_type'.
    task_instance_id = {task_id}-{node_id}
    scheduled_date = installation_date + recommended_frequency_months (in months)
    last_maintenance_date = installation_date
    status = 'pending'
    If any template field is None, raise ValueError.
    """

    # Build a lookup for templates by equipment_type
    template_by_type = {}
    for t in tasks:
        etype = t['equipment_type']
        if etype not in template_by_type:
            template_by_type[etype] = []
        template_by_type[etype].append(t)

    maintenance_tasks = []
    for node_id, attrs in graph.nodes(data=True):
        node_type = attrs.get('type')
        if node_type not in template_by_type:
            continue  # skip nodes with no matching template
        for template in template_by_type[node_type]:
            # Construct task_instance_id
            task_id = template['task_id']
            task_instance_id = f"{task_id}-{node_id}"
            # Get installation_date from node (should be str or int year)
            installation_date = attrs.get('installation_date')
            
            # Handle different field name formats
            if installation_date is None:
                year_of_installation = attrs.get('Year_of_installation')
                if year_of_installation is not None:
                    # Convert year to date format (assume January 1st)
                    installation_date = f"{int(year_of_installation)}-01-01"
            
            if installation_date is None:
                print(f"Warning: Node {node_id} has no installation date field. Skipping maintenance task generation.")
                continue
                
            install_dt = datetime.datetime.strptime(installation_date, "%Y-%m-%d").date()

            # Determine frequency (months)
            freq_months = int(template['recommended_frequency_months'])
            # print(f"Processing node {node_id} with template {task_id}, frequency: {freq_months} months")
            if freq_months == -1 or freq_months is None:
                # Add flag for 'is_replacement'
                is_replacement = True
                # Use node's expected_lifespan
                node_lifespan = attrs['expected_lifespan'] * 12  # Convert years to months
                if node_lifespan is None:
                    raise ValueError(f"expected_lifespan missing for node {node_id} but required by template {task_id}")
                freq_months = int(node_lifespan)
                # print(f"Using node's expected lifespan: {node_lifespan} months for node {node_id}")
            else:
                is_replacement = False

            # Determine money_cost
            money_cost = float(template['money_cost'])
            if money_cost == -1 or money_cost is None:
                node_replacement_cost = attrs['replacement_cost']
                if node_replacement_cost is None:
                    raise ValueError(f"replacement_cost missing for node {node_id} but required by template {task_id}")
                money_cost = float(node_replacement_cost)

            # last_maintenance_date is installation_date
            last_maintenance_date = install_dt.isoformat()
            # Build task dict
            task = {
                'task_instance_id': task_instance_id,
                'equipment_id': node_id,
                'equipment_type': node_type,
                'task_type': template['task_type'],
                'priority': int(template['default_priority']),
                'time_cost': float(template['time_cost']),
                'money_cost': float(money_cost),
                'notes': template.get('notes'),
                'description': template.get('description'),
                'task_id': task_id,
                'recommended_frequency_months': int(freq_months),
                'equipment_installation_date': installation_date,
                'risk_score': attrs.get('risk_score'),
                'is_replacement': is_replacement
            }
            maintenance_tasks.append(task)
    return maintenance_tasks

def generate_synthetic_condition_number(current_condition: float):
    new_condition = round(random.betavariate(alpha=5, beta=1) * current_condition, 1)
    # Clamp the condition to a realistic range [0.0, 1.0]
    return max(0.0, min(1.0, new_condition))

def generate_synthetic_maintenance_log_for_node(node_id: str, attrs: dict, current_period: pd.Period, maintenance_log_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a synthetic maintenance log entry for a given node.
    """

    current_date = current_period.start_time
    existing_condition = attrs.get('current_condition')
    if existing_condition is None:
        raise ValueError(f"Node {node_id} has no current_condition attribute.")
    condition_level = generate_synthetic_condition_number(existing_condition)

    log_entry = {
        'date': current_date.strftime('%Y-%m-%d'),
        'equipment_id': node_id,
        'old_condition': existing_condition,
        'observed_condition_level': condition_level,
        'notes': f"Synthetic log entry for {node_id} on {current_date.strftime('%Y-%m-%d')}"
    }
    return log_entry

def create_prioritized_calendar_schedule(
        tasks: List[Dict[str, Any]], 
        graph: nx.Graph,
        replacement_tasks: List[Dict[str, Any]],
        num_months_to_schedule: int, 
        monthly_budget_time: float, 
        monthly_budget_money: float, 
        does_budget_rollover: bool=False,
        current_date: pd.Timestamp=None, 
        generate_synthetic_maintenance_logs: bool = True,
        ignore_end_loads: bool = True, 
        ignore_utility_transformers: bool = True,
        maintenance_log_dict: Dict[str, Any]=None,
        seed: int = 42
                                        ) -> Dict[pd.Period, Dict[str, Any]]:
    """
    Create a calendar schedule for the tasks, grouping by month, as a dictionary.
    Includes all months between the earliest and latest task dates, even if no tasks exist in those months."""

    random.seed(seed) # For reproducibility

    tasks_df = pd.DataFrame(tasks)

    tasks_df['equipment_installation_date'] = pd.to_datetime(tasks_df['equipment_installation_date'], format='%Y-%m-%d')
    
    # Initialize the task schedule by determining the first instance of the task, using 'recommended_frequency_months' and 'equipment_installation_date'
    # Add a 'scheduled_month' column to the dataframe
    # Use Period arithmetic for months
    tasks_df['scheduled_month'] = tasks_df.apply(lambda row: (row['equipment_installation_date'].to_period('M') + int(row['recommended_frequency_months'])), axis=1)

    # Sort tasks by scheduled month
    tasks_df = tasks_df.sort_values(by='scheduled_month')

    # Get earliest installation date
    earliest_date = tasks_df['equipment_installation_date'].min()

    # Get the month of the earliest installation date
    earliest_month = earliest_date.to_period('M')

    current_date = pd.Timestamp(current_date)

    # Use the current date to adjust the number of months to schedule
    # Num months to schedule start from the current date
    months_already_passed = (current_date - earliest_date).days // 30
    print(f"Months already passed: {months_already_passed}")
    num_months_to_schedule += months_already_passed
    print(f"Adjusted number of months to schedule: {num_months_to_schedule}")

    rollover_time_budget = 0.0
    rollover_money_budget = 0.0
    time_budget_for_month = 0.0
    money_budget_for_month = 0.0

    max_num_logs = 100 # Limit the number of synthetic logs to generate in total

    if generate_synthetic_maintenance_logs:
        logs_per_period = {i: 0 for i in range(num_months_to_schedule)}
        for _ in range(max_num_logs):
            period = random.choice(range(num_months_to_schedule))
            logs_per_period[period] += 1

    monthly_records_dict = {}

    # Sort replacement tasks by condition_level smallest to largest
    replacement_tasks = sorted(replacement_tasks, key=lambda x: x['condition_level'])

    # Simulate each month, deferring tasks as needed to fit within budget
    for i in range(num_months_to_schedule):
        month = earliest_month + i
        month_record = {
            'month': month,
            'tasks_scheduled_for_month': [],
            'rollover_time_budget': 0.0,
            'rollover_money_budget': 0.0,
            'time_budget': 0.0,
            'money_budget': 0.0,
            'graph': None,
            'executed_tasks': [],
            'deferred_tasks': [],
            'maintenance_logs': [],
            'replacement_tasks_executed': [],
            'replacement_tasks_not_executed': []
        }

        if does_budget_rollover:
            rollover_money_budget += money_budget_for_month
            rollover_time_budget += time_budget_for_month
            month_record['rollover_time_budget'] = rollover_time_budget
            month_record['rollover_money_budget'] = rollover_money_budget

        time_budget_for_month = monthly_budget_time # Reset each month, remaining budget
        money_budget_for_month = monthly_budget_money # Reset each month, remaining budget

        if does_budget_rollover:
            money_budget_for_month += rollover_money_budget
            time_budget_for_month += rollover_time_budget
            rollover_money_budget = 0.0 # Reset rollover budget
            rollover_time_budget = 0.0 # Reset rollover budget

        month_record['time_budget'] = time_budget_for_month
        month_record['money_budget'] = money_budget_for_month

        # Get tasks scheduled for this month
        tasks_for_month = tasks_df[tasks_df['scheduled_month'] == month]

        # Update the graph's remaining useful life (RUL) and condition before processing the month
        graph = apply_rul_to_graph(graph, current_date=month.start_time)

        # Generate synthetic maintenance logs for this month if enabled
        if generate_synthetic_maintenance_logs:
            num_logs_to_generate = logs_per_period.get(i, 0)
            # print(f"Generating {num_logs_to_generate} synthetic maintenance logs for month {month}.")
            synthetic_logs = []
            nodes_list = list(graph.nodes(data=True))
            # Sort nodes by risk_score highest to lowest
            nodes_list = sorted(nodes_list, key=lambda x: x[1].get('risk_score'), reverse=True)

            if ignore_end_loads:
                nodes_list = [n for n in nodes_list if n[1].get('type') != 'end_load']
            if ignore_utility_transformers:
                nodes_list = [n for n in nodes_list if n[1].get('type') != 'utility_transformer']
            if nodes_list:
                for _ in range(num_logs_to_generate):
                    node_id, attrs = random.choice(nodes_list)
                    try:
                        log_entry = generate_synthetic_maintenance_log_for_node(node_id, attrs, month, month_record['maintenance_logs'])
                        synthetic_logs.append(log_entry)
                        # Update the node's current_condition based on the observed condition level
                        graph.nodes[node_id]['current_condition'] = log_entry['observed_condition_level']
                        # print(f"Generated synthetic log for node {node_id}: {log_entry}")
                    except ValueError as e:
                        print(f"Skipping log generation for node {node_id}: {e}")
            month_record['maintenance_logs'] = synthetic_logs
        else:
            if maintenance_log_dict and month in maintenance_log_dict:
                month_record['maintenance_logs'] = maintenance_log_dict[month]

        # Check for condition-triggered replacement tasks and execute them before other tasks
        for node_id, attrs in graph.nodes(data=True):
            node_condition = attrs.get('current_condition', 1.0)
            node_type = attrs.get('type')
            # Find the most severe applicable replacement task
            for r_task in replacement_tasks:
                equipment_type = r_task['equipment_type']
                condition_level = r_task['condition_level']
                if equipment_type == node_type and node_condition <= condition_level:
                    # Execute this replacement task
                    task_id = r_task['task_id']
                    task_name = r_task['task_name']
                    task_instance_id = f"{task_id}-{node_id}"
                    time_cost = r_task['time_cost']
                    money_cost = r_task['money_cost']
                    condition_improvement_amount = r_task['condition_improvement_amount']
                    base_expected_lifespan_improvement_percentage = r_task.get('base_expected_lifespan_improvement_percentage', 0.0)

                    # Check if within budget
                    # print(f"Node {node_id} requires replacement task {task_name} (condition {node_condition} <= {condition_level}). Checking budget...")
                    # print(f"Time budget: {time_budget_for_month}, Money budget: {money_budget_for_month}, Task time cost: {time_cost}, Task money cost: {money_cost}")
                    if time_budget_for_month >= time_cost and money_budget_for_month >= money_cost:
                        # Apply condition improvement
                        graph.nodes[node_id]['current_condition'] = node_condition + condition_improvement_amount

                        # Apply expected lifespan improvement if applicable
                        if "default_expected_lifespan" not in graph.nodes[node_id]:
                            graph.nodes[node_id]['default_expected_lifespan'] = attrs.get('expected_lifespan')

                        if task_name.lower() == 'full replacement':
                            graph.nodes[node_id]['installation_date'] = month.start_time.strftime('%Y-%m-%d')
                            graph.nodes[node_id]['tasks_deferred_count'] = 0
                            graph.nodes[node_id]['current_condition'] = 1.0
                            graph.nodes[node_id]['expected_lifespan'] = graph.nodes[node_id]['default_expected_lifespan']
                        else:
                            graph.nodes[node_id]['expected_lifespan'] = attrs.get('expected_lifespan') * (1 + base_expected_lifespan_improvement_percentage)
                        
                        graph.nodes[node_id]['expected_lifespan_days'] = graph.nodes[node_id]['expected_lifespan'] * 365

                        # Update budgets
                        time_budget_for_month -= time_cost
                        money_budget_for_month -= money_cost
                        # Record executed replacement
                        month_record['replacement_tasks_executed'].append({
                            'task_instance_id': task_instance_id,
                            'equipment_id': node_id,
                            'task_name': task_name,
                            'time_cost': time_cost,
                            'money_cost': money_cost,
                            'condition_improvement': condition_improvement_amount,
                            'new_condition': graph.nodes[node_id]['current_condition'],
                            'original_condition': node_condition,
                            'month_executed': month.start_time.strftime('%Y-%m-%d'),
                            'reason': 'Condition threshold exceeded'
                        })
                        # Reset replacement_required flag
                        graph.nodes[node_id]['replacement_required'] = False
                        break # You can only do one replacement task per node per month
                    
                    else:
                        # print(f"Insufficient budget to execute replacement task {task_name} for node {node_id} in month {month}. Deferring.")
                        month_record['replacement_tasks_not_executed'].append({
                            'task_instance_id': task_instance_id,
                            'equipment_id': node_id,
                            'task_name': task_name,
                            'time_cost': time_cost,
                            'money_cost': money_cost,
                            'condition_improvement': condition_improvement_amount,
                            'current_condition': node_condition,
                            'original_condition': node_condition,
                            'month_attempted': month.start_time.strftime('%Y-%m-%d'),
                            'reason': 'Condition threshold exceeded but insufficient budget'
                        })
        
        # Check if any nodes require replacement
        for node, attrs in graph.nodes(data=True):
            if attrs.get('replacement_required'):
                # Check replacement tasks for this node
                node_type = attrs.get('type')
                tasks_for_node = pd.DataFrame([t for t in replacement_tasks if t['equipment_type'] == node_type])
                # Get replacement task
                replacement_task = tasks_for_node[tasks_for_node['task_name'].str.lower() == 'full replacement']
                if not replacement_task.empty:
                    # Execute full replacement if budget allows
                    r_task = replacement_task.iloc[0]
                    task_id = r_task['task_id']
                    task_instance_id = f"{task_id}-{node}"
                    time_cost = r_task['time_cost']
                    money_cost = r_task['money_cost']
                    if time_budget_for_month >= time_cost and money_budget_for_month >= money_cost:
                        # Perform replacement
                        graph.nodes[node]['installation_date'] = month.start_time.strftime('%Y-%m-%d')
                        graph.nodes[node]['tasks_deferred_count'] = 0
                        graph.nodes[node]['current_condition'] = 1.0
                        if "default_expected_lifespan" in graph.nodes[node]:
                            graph.nodes[node]['expected_lifespan'] = graph.nodes[node]['default_expected_lifespan']
                        else:
                            graph.nodes[node]['expected_lifespan'] = attrs.get('expected_lifespan')
                        graph.nodes[node]['expected_lifespan_days'] = graph.nodes[node]['expected_lifespan'] * 365
                        # Update budgets
                        time_budget_for_month -= time_cost
                        money_budget_for_month -= money_cost
                        # Record executed replacement
                        month_record['replacement_tasks_executed'].append({
                            'task_instance_id': task_instance_id,
                            'equipment_id': node,
                            'task_name': 'Full Replacement',
                            'time_cost': time_cost,
                            'money_cost': money_cost,
                            'condition_improvement': 1.0 - attrs.get('current_condition', 1.0),
                            'new_condition': 1.0,
                            'original_condition': attrs.get('current_condition', 1.0),
                            'month_executed': month.start_time.strftime('%Y-%m-%d'),
                            'reason': 'Replacement RUL threshold exceeded'
                        })
                        # Reset replacement_required flag
                        graph.nodes[node]['replacement_required'] = False
                    else:
                        month_record['replacement_tasks_not_executed'].append({
                            'task_instance_id': task_instance_id,
                            'equipment_id': node,
                            'task_name': 'Full Replacement',
                            'time_cost': time_cost,
                            'money_cost': money_cost,
                            'condition_improvement': 0.0,
                            'current_condition': attrs.get('current_condition', 1.0),
                            'original_condition': attrs.get('current_condition', 1.0),
                            'month_attempted': month.start_time.strftime('%Y-%m-%d'),
                            'reason': 'Replacement RUL threshold exceeded but insufficient budget'
                        })

        month_record['tasks_scheduled_for_month'] = tasks_for_month

        # If there are no tasks, continue to the next month
        if tasks_for_month.empty:
            # Update RUL
            month_record['graph'] = graph.copy()
            monthly_records_dict[month] = month_record
            continue

        # Prioritize tasks based on the graph node's risk score
        # Sort tasks by priority (reverse), then by risk (not reverse)
        tasks_for_month = tasks_for_month.sort_values(by=['priority', 'risk_score'], ascending=[True, False])

        # Simulate task execution and budget consumption
        for index, task in tasks_for_month.iterrows():
            task_time_cost = task['time_cost']
            task_money_cost = task['money_cost']

            if time_budget_for_month >= task_time_cost and money_budget_for_month >= task_money_cost:
                # Apply condition improvement if the task has that effect
                if 'rul_percentage_effect' in task and pd.notna(task['rul_percentage_effect']):
                    apply_condition_improvement(graph, task['equipment_id'], task['rul_percentage_effect'], task['task_type'])

                if task['is_replacement']:
                    # Update the installation date for replacement tasks
                    graph.nodes[task['equipment_id']]['installation_date'] = month.start_time.strftime('%Y-%m-%d')
                    task['equipment_installation_date'] = month.start_time.strftime('%Y-%m-%d')
                    # Reset deferred count for replacement tasks
                    graph.nodes[task['equipment_id']]['tasks_deferred_count'] = 0
                    # Reset replacement_required
                    graph.nodes[task['equipment_id']]['replacement_required'] = False
                    # Remove the following attributes from the nodes: age_years, current_condition, aging_factor, condition_factor
                    for attr in ['age_years', 'current_condition', 'aging_factor', 'condition_factor']:
                        if attr in graph.nodes[task['equipment_id']]:
                            del graph.nodes[task['equipment_id']][attr]
                # Execute task
                time_budget_for_month -= task_time_cost
                money_budget_for_month -= task_money_cost
                # Update the scheduled_month based on the recommended_frequency_months for recurring tasks
                if 'recommended_frequency_months' in task and pd.notna(task['recommended_frequency_months']):
                    tasks_df.at[index, 'scheduled_month'] = month + int(task['recommended_frequency_months'])
                month_record['executed_tasks'].append(task)
            else:
                # Defer task
                month_record['deferred_tasks'].append(task)

                tasks_df.at[index, 'scheduled_month'] = month + 1
                # Update the graph's tasks_deferred_count
                graph.nodes[task['equipment_id']]['tasks_deferred_count'] += 1

        # Update the graph's remaining useful life (RUL)
        # This is now done at the start of the loop, so we just save the state
        month_record['graph'] = graph.copy()
        monthly_records_dict[month] = month_record

    print("Finished processing all months.")
    return monthly_records_dict

def process_maintenance_tasks(
        tasks: dict, 
        replacement_tasks: dict, 
        graph: nx.Graph, 
        monthly_budget_time: float, 
        monthly_budget_money: float, 
        months_to_schedule: int = 36, 
        animate: bool = False, 
        current_date: pd.Timestamp = pd.Timestamp.now(), 
        generate_synthetic_maintenance_logs: bool = True,
        maintenance_log_dict: Dict[str, Any]=None,
        seed: int = 42
    ) -> Dict[str, List[Dict[str, Any]]]:
    """
    Process the maintenance tasks and prioritize them based on the graph and budgets.
    Returns a prioritized schedule of tasks grouped by month.
    """
    # Make a copy of the graph to avoid modifying the original
    graph = graph.copy()

    # Create a calendar schedule from the tasks
    # tasks = load_maintenance_tasks(tasks_file_path)
    # replacement_tasks = load_replacement_tasks(replacement_tasks_path)
    tasks = generate_maintenance_tasks_from_graph(graph, tasks)

    # Prioritize the tasks in the calendar schedule
    prioritized_schedule = create_prioritized_calendar_schedule(
        tasks, 
        graph=graph, 
        replacement_tasks=replacement_tasks,
        num_months_to_schedule=months_to_schedule, 
        monthly_budget_time=monthly_budget_time, 
        monthly_budget_money=monthly_budget_money,
        current_date=current_date,
        generate_synthetic_maintenance_logs=generate_synthetic_maintenance_logs,
        maintenance_log_dict=maintenance_log_dict,
        seed=seed
    )

    return prioritized_schedule

# Simple test main function
def main():
    # This is a helper script that lives in a subdirectory of the project.
    # We need to adjust the directory to be the parent directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    os.chdir(parent_dir)

    print("--- Maintenance Task List Helper Test ---")
    # Example file paths (update as needed)
    task_csv = "./tables/example_maintenance_list.csv"
    replacement_csv = "./tables/example_replacement_types.csv"
    graph_file = "./example_graph.mepg"
    try:
        print(f"Loading task templates from: {task_csv}")
        templates = load_maintenance_tasks(task_csv)
        print(f"Loaded {len(templates)} templates.")
    except Exception as e:
        print(f"Error loading task templates: {e}")
        sys.exit(1)
    try:
        print(f"Loading replacement task templates from: {replacement_csv}")
        replacement_templates = load_replacement_tasks(replacement_csv)
        print(f"Loaded {len(replacement_templates)} replacement templates.")
    except Exception as e:
        print(f"Error loading replacement task templates: {e}")
        sys.exit(1)
    try:
        print(f"Loading graph from: {graph_file}")
        G = nx.read_graphml(graph_file)
        print(f"Loaded graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
    except Exception as e:
        print(f"Error loading graph: {e}")
        sys.exit(1)
    try:
        print("Generating maintenance tasks...")
        detailed_tasks = generate_maintenance_tasks_from_graph(G, templates)
        print(f"Generated {len(detailed_tasks)} maintenance tasks.")
    except Exception as e:
        print(f"Error generating maintenance tasks: {e}")
        sys.exit(1)

    # Create a calendar schedule for the tasks
    calendar_schedule = create_prioritized_calendar_schedule(
        detailed_tasks, 
        graph=G, 
        replacement_tasks=replacement_templates,
        num_months_to_schedule=36, 
        monthly_budget_time=1000000, 
        monthly_budget_money=1000000
    )

if __name__ == "__main__":
    main()
