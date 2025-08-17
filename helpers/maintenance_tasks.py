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
import json
import os
import copy
import networkx as nx
import sys
import pandas as pd

try:
    from helpers.animate_maintenance_tasks import animate_prioritized_schedule
except ImportError:
    from animate_maintenance_tasks import animate_prioritized_schedule

try:
    from rul_helper import apply_rul_to_graph
except ImportError:
    from helpers.rul_helper import apply_rul_to_graph

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

# Placeholder: Generate maintenance tasks from a graph
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
            install_dt = datetime.datetime.strptime(installation_date, "%Y-%m-%d").date()

            # Determine frequency (months)
            freq_months = int(template['recommended_frequency_months'])
            print(f"Processing node {node_id} with template {task_id}, frequency: {freq_months} months")
            if freq_months == -1 or freq_months is None:
                # Add flag for 'is_replacement'
                is_replacement = True
                # Use node's expected_lifespan
                node_lifespan = attrs['expected_lifespan'] * 12  # Convert years to months
                if node_lifespan is None:
                    raise ValueError(f"expected_lifespan missing for node {node_id} but required by template {task_id}")
                freq_months = int(node_lifespan)
                print(f"Using node's expected lifespan: {node_lifespan} months for node {node_id}")
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

# Placeholder: Prioritize maintenance tasks
def prioritize_tasks(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Assign a priority score to each task based on risk, age, and other factors. For generic templates, this may just return the default_priority."""
    # TODO: Implement prioritization logic
    ...

# Placeholder: Export maintenance tasks to CSV
def export_tasks_to_csv(tasks: List[Dict[str, Any]], csv_path: str):
    """Export the list of generic maintenance task templates to a CSV file."""
    fieldnames = tasks[0].keys() if tasks else []
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for task in tasks:
            writer.writerow(task)

# Placeholder: Update task status
def update_task_status(tasks: List[Dict[str, Any]], task_id: str, new_status: str):
    """Update the status of a specific task (if tracking template status, e.g., for review/approval)."""
    # TODO: Implement status update logic
    ...

# Additional helper functions can be added as needed
def create_prioritized_calendar_schedule(tasks: List[Dict[str, Any]], graph: nx.Graph,
                                         num_months_to_schedule: int, monthly_budget_time: float, 
                                         monthly_budget_money: float, does_budget_rollover: bool=False):
    """
    Create a calendar schedule for the tasks, grouping by month, as a dictionary.
    Includes all months between the earliest and latest task dates, even if no tasks exist in those months."""

    # Initial tasks_deferred_count in the graph
    for node in graph.nodes:
        graph.nodes[node]['tasks_deferred_count'] = 0

    calendar_schedule = {}

    tasks_df = pd.DataFrame(tasks)

    # Convert 'equipment_installation_date' to datetime, it is in the format %Y-%m-%d
    tasks_df['equipment_installation_date'] = pd.to_datetime(tasks_df['equipment_installation_date'], format='%Y-%m-%d')
    
    # Initialize the task schedule by determining the first instance of the task, using 'recommended_frequency_months' and 'equipment_installation_date'
    # Add a 'scheduled_month' column to the dataframe
    # Use Period arithmetic for months
    tasks_df['scheduled_month'] = tasks_df.apply(lambda row: (row['equipment_installation_date'].to_period('M') + int(row['recommended_frequency_months'])), axis=1)

    # Sort tasks by scheduled month
    tasks_df = tasks_df.sort_values(by='scheduled_month')

    # print("Tasks DataFrame:")
    # print(tasks_df.head())

    # Get earliest installation date
    earliest_date = tasks_df['equipment_installation_date'].min()

    # Get the month of the earliest installation date
    earliest_month = earliest_date.to_period('M')

    # print()
    # print(f"Creating calendar schedule starting from {earliest_month} for {num_months_to_schedule} months")
    # print(f"Budget (Time: {monthly_budget_time}, Money: {monthly_budget_money})")

    rollover_time_budget = 0.0
    rollover_money_budget = 0.0
    time_budget_for_month = 0.0
    money_budget_for_month = 0.0

    monthly_records_dict = {}

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
            'deferred_tasks': []
        }
        # print()

        if does_budget_rollover:
            rollover_money_budget += money_budget_for_month
            rollover_time_budget += time_budget_for_month
            # print(f"Month {month}: Rollover (Time: {rollover_time_budget}, Money: {rollover_money_budget})")
            month_record['rollover_time_budget'] = rollover_time_budget
            month_record['rollover_money_budget'] = rollover_money_budget

        time_budget_for_month = monthly_budget_time # Reset each month, remaining budget
        money_budget_for_month = monthly_budget_money # Reset each month, remaining budget
        # print(f"Month {month}: Initial Budget (Time: {time_budget_for_month}, Money: {money_budget_for_month}, Rollover is {does_budget_rollover})")

        if does_budget_rollover:
            money_budget_for_month += rollover_money_budget
            time_budget_for_month += rollover_time_budget
            rollover_money_budget = 0.0 # Reset rollover budget
            rollover_time_budget = 0.0 # Reset rollover budget
            # print(f"Month {month}: Rollover Budget (Time: {time_budget_for_month}, Money: {money_budget_for_month})")

        month_record['time_budget'] = time_budget_for_month
        month_record['money_budget'] = money_budget_for_month

        # print(f"Month {month}: Budget (Time: {time_budget_for_month}, Money: {money_budget_for_month}, Rollover is {does_budget_rollover})")

        # Get tasks scheduled for this month
        tasks_for_month = tasks_df[tasks_df['scheduled_month'] == month]
        month_record['tasks_scheduled_for_month'] = tasks_for_month

        # If there are no tasks, continue to the next month
        if tasks_for_month.empty:
            # print(f"No tasks scheduled for month {month}.")
            # Update RUL
            graph = apply_rul_to_graph(graph, current_date=month.start_time)
            month_record['graph'] = graph.copy()
            monthly_records_dict[month] = month_record
            continue

        # Prioritize tasks based on the graph node's risk score
        # Sort tasks by priority (reverse), then by risk (not reverse)
        tasks_for_month = tasks_for_month.sort_values(by=['priority', 'risk_score'], ascending=[True, False])

        # Simulate task execution and budget consumption
        # print(f"Processing month {month} with {len(tasks_for_month)} tasks")
        for index, task in tasks_for_month.iterrows():
            task_time_cost = task['time_cost']
            task_money_cost = task['money_cost']

            if time_budget_for_month >= task_time_cost and money_budget_for_month >= task_money_cost:
                if task['is_replacement']:
                    # Update the installation date for replacement tasks
                    graph.nodes[task['equipment_id']]['installation_date'] = month.start_time.strftime('%Y-%m-%d')
                    task['equipment_installation_date'] = month.start_time.strftime('%Y-%m-%d')
                    # Reset deferred count for replacement tasks
                    graph.nodes[task['equipment_id']]['tasks_deferred_count'] = 0
                    # print(f"  Replacing equipment {task['equipment_id']} with new installation date {task['equipment_installation_date']}")
                # Execute task
                time_budget_for_month -= task_time_cost
                money_budget_for_month -= task_money_cost
                # Update the scheduled_month based on the recommended_frequency_months
                tasks_df.at[index, 'scheduled_month'] = month + task['recommended_frequency_months']
                # print(f"  Executing task {task['task_instance_id']} (Time: {task_time_cost}, Cost: {task_money_cost}), Remaining Budget (Time: {time_budget_for_month}, Money: {money_budget_for_month}), Next Scheduled Month: {tasks_df.at[index, 'scheduled_month']}, Recommended Frequency: {task['recommended_frequency_months']}")
                month_record['executed_tasks'].append(task)
            else:
                # Defer task
                # print(f"  Deferring task {task['task_instance_id']} (Time: {task_time_cost}, Cost: {task_money_cost})")

                month_record['deferred_tasks'].append(task)

                tasks_df.at[index, 'scheduled_month'] = month + 1
                # Update the graph's tasks_deferred_count
                graph.nodes[task['equipment_id']]['tasks_deferred_count'] += 1
                # print(f"  Updated tasks_deferred_count for node {task['equipment_id']} to {graph.nodes[task['equipment_id']]['tasks_deferred_count']}")

        # Update the graph's remaining useful life (RUL)
        # TODO Debug RUL calculation
        graph = apply_rul_to_graph(graph, current_date=month.start_time)
        month_record['graph'] = graph.copy()
        monthly_records_dict[month] = month_record

        # print(f"End of month {month}: Remaining Budget (Time: {time_budget_for_month}, Money: {money_budget_for_month})")

        # break # DEBUG the first month
    print("Finished processing all months.")
    return monthly_records_dict

def process_maintenance_tasks(tasks_file_path: str, graph, monthly_budget_time: float, monthly_budget_money: float, months_to_schedule: int = 36, animate=False) -> Dict[str, List[Dict[str, Any]]]:
    """
    Process the maintenance tasks and prioritize them based on the graph and budgets.
    Returns a prioritized schedule of tasks grouped by month.
    """
    # Make a copy of the graph to avoid modifying the original
    graph = copy.deepcopy(graph)

    # Create a calendar schedule from the tasks
    tasks = load_maintenance_tasks(tasks_file_path)
    tasks = generate_maintenance_tasks_from_graph(graph, tasks)
        
    # Prioritize the tasks in the calendar schedule
    prioritized_schedule = create_prioritized_calendar_schedule(tasks, graph=graph, num_months_to_schedule=months_to_schedule, monthly_budget_time=monthly_budget_time, monthly_budget_money=monthly_budget_money)

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
    graph_file = "./example_graph.mepg"
    try:
        print(f"Loading task templates from: {task_csv}")
        templates = load_maintenance_tasks(task_csv)
        print(f"Loaded {len(templates)} templates.")
    except Exception as e:
        print(f"Error loading task templates: {e}")
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
    calendar_schedule = create_prioritized_calendar_schedule(detailed_tasks, graph=G, num_months_to_schedule=36, monthly_budget_time=1000000, monthly_budget_money=1000000)

if __name__ == "__main__":
    main()
