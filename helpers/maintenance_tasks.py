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
            if freq_months > 0:
                scheduled_dt = install_dt + relativedelta(months=int(freq_months))
                scheduled_date = scheduled_dt.isoformat()
            else:
                scheduled_date = install_dt.isoformat()

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
                'scheduled_date': scheduled_date,
                'last_maintenance_date': last_maintenance_date,
                'priority': template['default_priority'],
                'time_cost': template['time_cost'],
                'money_cost': money_cost,
                'status': 'pending',
                'notes': template.get('notes', ''),
                'description': template.get('description', ''),
                'task_id': task_id,
                'recommended_frequency_months': freq_months,
                'node_risk_score': attrs.get('risk_score'),
                'months_deferred': 0,  
            }
            # Check for any None values in required fields
            for k in ['recommended_frequency_months', 'priority', 'time_cost', 'money_cost']:
                if task.get(k) is None:
                    raise ValueError(f"Field '{k}' is None for task {task['task_instance_id']} (template {task_id}, node {node_id}). Please check template and node attributes.")
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
def create_calendar_schedule(tasks: List[Dict[str, Any]]):
    """Create a calendar schedule for the tasks, grouping by month, as a dictionary.
    Includes all months between the earliest and latest task dates, even if no tasks exist in those months."""
    calendar_schedule = {}
    
    if not tasks:
        return calendar_schedule
    
    # Find earliest and latest dates
    task_dates = [datetime.datetime.strptime(task['scheduled_date'], '%Y-%m-%d') for task in tasks]
    earliest_date = min(task_dates)
    latest_date = max(task_dates)
    
    # Create all months between earliest and latest
    current_date = earliest_date.replace(day=1)  # Start at beginning of month
    end_date = latest_date.replace(day=1)
    
    while current_date <= end_date:
        month_key = current_date.strftime('%Y-%m')
        calendar_schedule[month_key] = []
        current_date += relativedelta(months=1)
    
    # Now add tasks to their respective months
    for task in tasks:
        month = datetime.datetime.strptime(task['scheduled_date'], '%Y-%m-%d').strftime('%Y-%m')
        calendar_schedule[month].append(task)
    
    return calendar_schedule

def animate_prioritized_schedule(prioritized_schedule, monthly_budget_time, monthly_budget_money, months_to_schedule):
    """Placeholder for animation function to visualize the prioritized schedule.
    This could use matplotlib or another library to create a Gantt chart or similar visualization."""

    print("Animating prioritized schedule...")

def prioritize_calendar_tasks(calendar_schedule: Dict[str, List[Dict[str, Any]]], monthly_budget_time: float, monthly_budget_money: float, months_to_schedule: int=36) -> Dict[str, List[Dict[str, Any]]]:
    """
    Prioritize tasks in the calendar schedule based on time and money budgets.
    Use the 'node_risk_score' to influence priority.

    First sort all tasks in a month by risk score
    and then select tasks until either the time or money budget is exceeded.

    Tasks that are completed generate a new task into a future month as 'pending' tasks,
    to represent ongoing maintenance.  Use the completed task's attributes to fill in the new task's attributes.

    Tasks that are not completed are pushed to the next month and labeled as 'deferred'.

    We can track how many months a task has been deferred by updating the 'months_deferred' field.

    Use the 'months_to_schedule' parameter to limit how far into the future we schedule tasks.

    Print a summary of the prioritized tasks for each month, including total time and money costs and the number of deferred tasks.

    Parameters:
    - calendar_schedule: The calendar schedule containing tasks grouped by month.
    - monthly_budget_time: The maximum time budget for each month.
    - monthly_budget_money: The maximum money budget for each month.
    - months_to_schedule: The number of months into the future to schedule tasks (default is 36).
    Returns:
    - A dictionary containing the prioritized tasks grouped by month.
    """
    prioritized_schedule = {}
    
    # Get all months and sort them chronologically
    all_months = sorted(calendar_schedule.keys())
    
    # Calculate the cutoff month based on months_to_schedule
    if all_months:
        start_month = datetime.datetime.strptime(all_months[0], '%Y-%m')
        cutoff_month = (start_month + relativedelta(months=months_to_schedule)).strftime('%Y-%m')
    else:
        cutoff_month = None
    
    # Process each month in chronological order
    for index, month in enumerate(all_months):
        if cutoff_month and month > cutoff_month:
            break
            
        print(f"\n--- Processing month {index} {month} ---")
        
        # Get tasks for this month and sort by risk score (descending - highest risk first)
        month_tasks = calendar_schedule[month][:]  # Make a copy
        month_tasks.sort(key=lambda t: t.get('node_risk_score', 0), reverse=True)
        
        # Track budgets for this month
        remaining_time = monthly_budget_time
        remaining_money = monthly_budget_money
        
        completed_tasks = []
        deferred_tasks = []
        
        # Select tasks until budget is exceeded
        for task in month_tasks:
            task_time = task.get('time_cost', 0) or 0
            task_money = task.get('money_cost', 0) or 0
            
            # Check if task fits in remaining budget
            if task_time <= remaining_time and task_money <= remaining_money:
                # Task can be completed
                remaining_time -= task_time
                remaining_money -= task_money
                
                # Mark as completed and add to completed list
                task_copy = task.copy()
                task_copy['status'] = 'completed'
                completed_tasks.append(task_copy)
                
                # Generate future maintenance task
                current_date = datetime.datetime.strptime(task['scheduled_date'], '%Y-%m-%d')
                frequency_months = task.get('recommended_frequency_months', 12)
                next_date = current_date + relativedelta(months=frequency_months)
                next_month = next_date.strftime('%Y-%m')
                
                # Only schedule if within the months_to_schedule limit
                if not cutoff_month or next_month <= cutoff_month:
                    future_task = task.copy()
                    future_task['scheduled_date'] = next_date.strftime('%Y-%m-%d')
                    future_task['last_maintenance_date'] = task['scheduled_date']
                    future_task['status'] = 'pending'
                    future_task['months_deferred'] = 0
                    
                    # Add to appropriate month in calendar_schedule
                    if next_month not in calendar_schedule:
                        calendar_schedule[next_month] = []
                    calendar_schedule[next_month].append(future_task)
                    
            else:
                # Task cannot be completed - defer to next month
                next_month_date = datetime.datetime.strptime(month, '%Y-%m') + relativedelta(months=1)
                next_month = next_month_date.strftime('%Y-%m')
                
                # Only defer if within the months_to_schedule limit
                if not cutoff_month or next_month <= cutoff_month:
                    deferred_task = task.copy()
                    deferred_task['scheduled_date'] = next_month_date.strftime('%Y-%m-%d')
                    deferred_task['status'] = 'deferred'
                    deferred_task['months_deferred'] = deferred_task.get('months_deferred', 0) + 1
                    deferred_tasks.append(deferred_task)
                    
                    # Add to next month in calendar_schedule
                    if next_month not in calendar_schedule:
                        calendar_schedule[next_month] = []
                    calendar_schedule[next_month].append(deferred_task)
        
        # Store the prioritized tasks for this month
        prioritized_schedule[month] = completed_tasks
        
        # Print summary for this month
        total_time_used = monthly_budget_time - remaining_time
        total_money_used = monthly_budget_money - remaining_money
        
        print(f"Completed tasks: {len(completed_tasks)}")
        print(f"Deferred tasks: {len(deferred_tasks)}")
        print(f"Time used: {total_time_used:.1f}/{monthly_budget_time:.1f} hours ({total_time_used/monthly_budget_time*100:.1f}%)")
        print(f"Money used: ${total_money_used:.2f}/${monthly_budget_money:.2f} ({total_money_used/monthly_budget_money*100:.1f}%)")
        
        if deferred_tasks:
            print(f"Deferred task details:")
            for dt in deferred_tasks:
                print(f"  - {dt['task_instance_id']} (months deferred: {dt['months_deferred']})")
    
    animate_prioritized_schedule(prioritized_schedule, monthly_budget_time, monthly_budget_money, months_to_schedule)

    return prioritized_schedule

# Simple test main function
def main():
    import networkx as nx
    import sys
    import os

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
        tasks = generate_maintenance_tasks_from_graph(G, templates)
        print(f"Generated {len(tasks)} maintenance tasks.")
        # Print a sample
        for t in tasks[:5]:
            print(t)
        if len(tasks) > 5:
            print(f"... ({len(tasks)-5} more tasks)")
    except Exception as e:
        print(f"Error generating maintenance tasks: {e}")
        sys.exit(1)

    # Create a calendar schedule for the tasks
    calendar_schedule = create_calendar_schedule(tasks)
    print("Generated calendar schedule for tasks:")
    for month, tasks in calendar_schedule.items():
        print(f"{month}: {len(tasks)} tasks")
        for task in tasks:
            print(f"  - {task['task_instance_id']} ({task['equipment_id']}) - {task['task_type']} on {task['scheduled_date']}")
        
        print(f"Total time cost for {month}: {sum(t['time_cost'] for t in tasks if t['time_cost'] is not None)} hours")
        print(f"Total money cost for {month}: ${sum(t['money_cost'] for t in tasks if t['money_cost'] is not None):.2f}")
        print()

    # Prioritize calendar tasks
    calendar_schedule = prioritize_calendar_tasks(calendar_schedule=calendar_schedule, monthly_budget_time=20, monthly_budget_money=500)

    # Save to CSV
    output_dir = "./maintenance_tasks/"
    filenname = "example_detailed_maintenance_tasks.csv"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output_path = os.path.join(output_dir, filenname)
    print(f"Exporting tasks to: {output_path}")
    export_tasks_to_csv(tasks, output_path)
    print(f"Tasks exported successfully to {output_path}")

if __name__ == "__main__":
    main()
