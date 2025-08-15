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

from rul_helper import apply_rul_to_graph

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
                        if val == -1:
                            row[key] = None
                        else:
                            row[key] = val
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
            freq_months = template['recommended_frequency_months']
            print(f"Processing node {node_id} with template {task_id}, frequency: {freq_months} months")
            if freq_months == -1 or freq_months is None:
                # Use node's expected_lifespan
                node_lifespan = attrs['expected_lifespan'] * 12  # Convert years to months
                if node_lifespan is None:
                    raise ValueError(f"expected_lifespan missing for node {node_id} but required by template {task_id}")
                freq_months = int(node_lifespan)
                print(f"Using node's expected lifespan: {node_lifespan} months for node {node_id}")

            # Determine money_cost
            money_cost = template['money_cost']
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
                'priority': template['default_priority'],
                'time_cost': template['time_cost'],
                'money_cost': money_cost,
                'notes': template.get('notes'),
                'description': template.get('description'),
                'task_id': task_id,
                'recommended_frequency_months': freq_months,
                'equipment_installation_date': installation_date,
                'risk_score': attrs.get('risk_score')
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

    print("Tasks DataFrame:")
    print(tasks_df.head())

    # Get earliest installation date
    earliest_date = tasks_df['equipment_installation_date'].min()

    # Get the month of the earliest installation date
    earliest_month = earliest_date.to_period('M')

    print()
    print(f"Creating calendar schedule starting from {earliest_month} for {num_months_to_schedule} months")
    print(f"Budget (Time: {monthly_budget_time}, Money: {monthly_budget_money})")

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
            'tasks': []
        }
        print()

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

        print(f"Month {month}: Budget (Time: {time_budget_for_month}, Money: {money_budget_for_month}, Rollover is {does_budget_rollover})")

        # Get tasks scheduled for this month
        tasks_for_month = tasks_df[tasks_df['scheduled_month'] == month]

        # If there are no tasks, continue to the next month
        if tasks_for_month.empty:
            print(f"No tasks scheduled for month {month}.")
            continue

        # Prioritize tasks based on the graph node's risk score
        # Sort tasks by priority (reverse), then by risk (not reverse)
        tasks_for_month = tasks_for_month.sort_values(by=['priority', 'risk_score'], ascending=[True, False])

        month_record['tasks_scheduled_for_month'] = tasks_for_month
        month_record['executed_tasks'] = []
        month_record['deferred_tasks'] = []

        # Simulate task execution and budget consumption
        print(f"Processing month {month} with {len(tasks_for_month)} tasks")
        for index, task in tasks_for_month.iterrows():
            task_time_cost = task['time_cost']
            task_money_cost = task['money_cost']

            if time_budget_for_month >= task_time_cost and money_budget_for_month >= task_money_cost:
                # Execute task
                time_budget_for_month -= task_time_cost
                money_budget_for_month -= task_money_cost
                # Update the scheduled_month based on the recommended_frequency_months
                tasks_df.at[index, 'scheduled_month'] = month + task['recommended_frequency_months']
                print(f"  Executing task {task['task_instance_id']} (Time: {task_time_cost}, Cost: {task_money_cost}), Remaining Budget (Time: {time_budget_for_month}, Money: {money_budget_for_month}), Next Scheduled Month: {tasks_df.at[index, 'scheduled_month']}, Recommended Frequency: {task['recommended_frequency_months']}")
                month_record['executed_tasks'].append(task)
            else:
                # Defer task
                print(f"  Deferring task {task['task_instance_id']} (Time: {task_time_cost}, Cost: {task_money_cost})")

                month_record['deferred_tasks'].append(task)

                tasks_df.at[index, 'scheduled_month'] = month + 1
                # Update the graph's tasks_deferred_count
                graph.nodes[task['equipment_id']]['tasks_deferred_count'] += 1
                print(f"  Updated tasks_deferred_count for node {task['equipment_id']} to {graph.nodes[task['equipment_id']]['tasks_deferred_count']}")

        # Update the graph's remaining useful life (RUL)
        # TODO Debug RUL calculation
        apply_rul_to_graph(graph)
        monthly_records_dict[month] = month_record

        print(f"End of month {month}: Remaining Budget (Time: {time_budget_for_month}, Money: {money_budget_for_month})")

        # break # DEBUG the first month

    return calendar_schedule

# def prioritize_calendar_tasks(
#     graph,
#     calendar_schedule: Dict[str, List[Dict[str, Any]]],
#     monthly_budget_time: float,
#     monthly_budget_money: float,
#     months_to_schedule: int = 36,
#     animate: bool = False,
#     remove_nodes_with_no_rul: bool = False,
#     *,
#     generate_full_then_slice: bool = True,
# ) -> Dict[str, List[Dict[str, Any]]]:
#     """
#     TEMPLATE: Prioritize and schedule maintenance tasks with clear phases and extensibility.

#     Overview
#     - Generate a month-by-month schedule, completing tasks within budgets and deferring the rest.
#     - Always increment node 'tasks_deferred_count' when deferring to preserve RUL impact.
#     - Update RUL after each processed month via apply_rul_to_graph (supports both penalties and future restorative logic).
#     - Optionally remove nodes whose RUL drops to 0.
#     - By default, generate the FULL schedule until all tasks are resolved, then slice to first `months_to_schedule` months.

#     Inputs
#     - graph: networkx Graph with node attributes including installation_date, expected_lifespan, etc.
#     - calendar_schedule: Dict[str YYYY-MM -> List[task dict]] initial tasks by month.
#     - monthly_budget_time, monthly_budget_money: per-month budgets.
#     - months_to_schedule: number of months to include in the returned result.
#     - animate: optional visualization hook.
#     - remove_nodes_with_no_rul: remove nodes with RUL <= 0 after monthly update.
#     - generate_full_then_slice: when True (default), simulate until all tasks are processed, then return only the first N months.

#     Outputs
#     - Dict with a key per month (YYYY-MM) containing:
#         - new_completed, new_deferred, deferred_completed, deferred_deferred
#         - graph_snapshot (deep copy after that month)
#       Plus a top-level 'lost_deferred_tasks' list if tasks are dropped due to slicing-only mode.

#     Notes
#     - Sorting strategy: by node_risk_score desc, tie-break by months_deferred desc, then by money/time cost asc (TODO: tune).
#     - Restorative maintenance: not handled here; handled inside apply_rul_to_graph based on completed tasks if needed.
#     """

#     try:
#         from rul_helper import apply_rul_to_graph
#     except ImportError:
#         from helpers.rul_helper import apply_rul_to_graph

#     # Local helpers
#     def parse_month_key(m: str) -> datetime.datetime:
#         return datetime.datetime.strptime(m, '%Y-%m')

#     def month_key(dt: datetime.datetime) -> str:
#         return dt.strftime('%Y-%m')

#     def first_of_month(dt: datetime.datetime) -> datetime.datetime:
#         return dt.replace(day=1)

#     # Prepare graph (remove end loads)
#     for node in list(graph.nodes):
#         if graph.nodes[node].get('type') == 'end_load':
#             graph.remove_node(node)

#     # Normalize calendar keys and find start month
#     if not calendar_schedule:
#         return {'lost_deferred_tasks': []}
#     # Ensure keys are YYYY-MM and lists are mutable
#     calendar_schedule = {k[:7]: list(v) for k, v in calendar_schedule.items()}
#     start_dt = min(parse_month_key(k) for k in calendar_schedule.keys())

#     prioritized_schedule: Dict[str, Dict[str, Any]] = {}
#     lost_deferred_tasks: List[Dict[str, Any]] = []

#     # Simulation loop
#     current_dt = start_dt
#     processed_months = set()
#     max_guard_months = 2400  # safety guard against infinite loops
#     steps = 0

#     def months_with_tasks() -> List[str]:
#         return [k for k, v in calendar_schedule.items() if v]

#     def last_task_month_dt() -> datetime.datetime | None:
#         mts = months_with_tasks()
#         if not mts:
#             return None
#         return max(parse_month_key(m) for m in mts)

#     while steps < max_guard_months:
#         steps += 1
#         # Advance to the next month that has tasks >= current_dt
#         available_months = sorted(calendar_schedule.keys())
#         next_months = [m for m in available_months if parse_month_key(m) >= first_of_month(current_dt) and calendar_schedule[m]]
#         if not next_months:
#             break  # no remaining tasks anywhere

#         month = next_months[0]
#         current_dt = parse_month_key(month)
#         if month in processed_months:
#             # Already processed; move to next chronological month with tasks
#             # Find the next month with tasks after this one
#             remaining = [m for m in available_months if parse_month_key(m) > current_dt and calendar_schedule[m]]
#             if not remaining:
#                 break
#             month = remaining[0]
#             current_dt = parse_month_key(month)

#         # Prepare task lists
#         month_tasks = list(calendar_schedule.get(month, []))
#         # Sort by risk desc, then months_deferred desc
#         month_tasks.sort(key=lambda t: (
#             t.get('node_risk_score') if t.get('node_risk_score') is not None else -float('inf'),
#             t.get('months_deferred', 0)
#         ), reverse=True)

#         remaining_time = monthly_budget_time
#         remaining_money = monthly_budget_money

#         new_completed: List[Dict[str, Any]] = []
#         new_deferred: List[Dict[str, Any]] = []
#         deferred_completed: List[Dict[str, Any]] = []
#         deferred_deferred: List[Dict[str, Any]] = []

#         # Process tasks for this month
#         for task in month_tasks:
#             task_time = task.get('time_cost') or 0
#             task_money = task.get('money_cost') or 0
#             is_deferred = task.get('months_deferred', 0) > 0

#             node_id = task.get('equipment_id')
#             node_attrs = graph.nodes.get(node_id)
#             if node_attrs is None:
#                 continue
#             if node_attrs.get('tasks_deferred_count') is None:
#                 node_attrs['tasks_deferred_count'] = 0

#             if task_time <= remaining_time and task_money <= remaining_money:
#                 # Complete now
#                 remaining_time -= task_time
#                 remaining_money -= task_money

#                 t_done = task.copy()
#                 t_done['status'] = 'completed'
#                 if is_deferred:
#                     deferred_completed.append(t_done)
#                 else:
#                     new_completed.append(t_done)

#                 # Schedule next occurrence based on recommended_frequency_months
#                 freq = task.get('recommended_frequency_months') or 0
#                 if freq > 0:
#                     cur_date = datetime.datetime.strptime(task['scheduled_date'], '%Y-%m-%d')
#                     next_date = cur_date + relativedelta(months=int(freq))
#                     next_key = month_key(first_of_month(next_date))
#                     calendar_schedule.setdefault(next_key, []).append({
#                         **task,
#                         'scheduled_date': next_date.strftime('%Y-%m-%d'),
#                         'last_maintenance_date': task['scheduled_date'],
#                         'status': 'pending',
#                         'months_deferred': 0,
#                     })
#             else:
#                 # Defer to next month
#                 next_dt = first_of_month(parse_month_key(month) + relativedelta(months=1))
#                 next_key = month_key(next_dt)
#                 deferred_task = {**task,
#                                  'scheduled_date': next_dt.strftime('%Y-%m-%d'),
#                                  'status': 'deferred',
#                                  'months_deferred': task.get('months_deferred', 0) + 1}
#                 if is_deferred:
#                     deferred_deferred.append(deferred_task)
#                 else:
#                     new_deferred.append(deferred_task)

#                 calendar_schedule.setdefault(next_key, []).append(deferred_task)
#                 node_attrs['tasks_deferred_count'] += 1

#         # Clear processed month tasks to avoid re-processing
#         calendar_schedule[month] = []
#         processed_months.add(month)

#         # Update RUL for the first day of next month
#         graph = apply_rul_to_graph(graph, current_date=first_of_month(current_dt + relativedelta(months=1)))

#         # Optionally prune nodes with no RUL
#         if remove_nodes_with_no_rul:
#             for n in list(graph.nodes):
#                 if graph.nodes[n].get('remaining_useful_life_days') is not None and graph.nodes[n].get('remaining_useful_life_days') <= 0:
#                     graph.remove_node(n)

#         # Store snapshot
#         prioritized_schedule[month] = {
#             'new_completed': new_completed,
#             'new_deferred': new_deferred,
#             'deferred_completed': deferred_completed,
#             'deferred_deferred': deferred_deferred,
#             'graph_snapshot': copy.deepcopy(graph),
#         }

#         # Continue loop; if no tasks remaining, loop will break at top

#     # If requested, slice down to the first N months without losing integrity
#     if generate_full_then_slice and prioritized_schedule:
#         sorted_months = sorted(prioritized_schedule.keys())
#         keep = set(sorted_months[:months_to_schedule])
#         sliced = {m: prioritized_schedule[m] for m in sorted_months if m in keep}
#         # Nothing is "lost" during simulation, so lost_deferred_tasks is informational only here
#         sliced['lost_deferred_tasks'] = lost_deferred_tasks
#         result = sliced
#     else:
#         prioritized_schedule['lost_deferred_tasks'] = lost_deferred_tasks
#         result = prioritized_schedule

#     if animate:
#         animate_prioritized_schedule(result, monthly_budget_time, monthly_budget_money, months_to_schedule)

#     return result

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
    calendar_schedule = create_calendar_schedule(tasks)
    
    # Prioritize the tasks in the calendar schedule
    prioritized_schedule = prioritize_calendar_tasks(graph, calendar_schedule, monthly_budget_time, monthly_budget_money, months_to_schedule, animate=animate)
    
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
    calendar_schedule = create_prioritized_calendar_schedule(detailed_tasks, graph=G, num_months_to_schedule=36, monthly_budget_time=10, monthly_budget_money=100)
    # print("Generated calendar schedule for tasks:")
    # for month, tasks in calendar_schedule.items():
    #     print(f"{month}: {len(tasks)} tasks")
    #     for task in tasks:
    #         print(f"  - {task['task_instance_id']} ({task['equipment_id']}) - {task['task_type']} on {task['scheduled_date']}")
        
    #     print(f"Total time cost for {month}: {sum(t['time_cost'] for t in tasks if t['time_cost'] is not None)} hours")
    #     print(f"Total money cost for {month}: ${sum(t['money_cost'] for t in tasks if t['money_cost'] is not None):.2f}")
    #     print()

    # Prioritize calendar tasks
    # calendar_schedule = prioritize_calendar_tasks(graph=G, calendar_schedule=calendar_schedule, monthly_budget_time=10, monthly_budget_money=100)

    # # Save to CSV
    # output_dir = "./maintenance_tasks/"
    # filenname = "example_detailed_maintenance_tasks.csv"
    # if not os.path.exists(output_dir):
    #     os.makedirs(output_dir)
    # output_path = os.path.join(output_dir, filenname)
    # print(f"Exporting tasks to: {output_path}")
    # export_tasks_to_csv(tasks, output_path)
    # print(f"Tasks exported successfully to {output_path}")

if __name__ == "__main__":
    main()
