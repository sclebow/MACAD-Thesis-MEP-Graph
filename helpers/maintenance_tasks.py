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
    import datetime
    from dateutil.relativedelta import relativedelta

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
            # Parse installation_date to datetime
            if isinstance(installation_date, int):
                install_dt = datetime.date(installation_date, 1, 1)
            elif isinstance(installation_date, str):
                try:
                    # Try YYYY-MM-DD
                    install_dt = datetime.datetime.strptime(installation_date, "%Y-%m-%d").date()
                except Exception:
                    try:
                        # Try YYYY
                        install_dt = datetime.date(int(installation_date), 1, 1)
                    except Exception:
                        raise ValueError(f"Could not parse installation_date '{installation_date}' for node {node_id}")
            else:
                raise ValueError(f"Missing or invalid installation_date for node {node_id}")

            # Determine frequency (months)
            freq_months = template['recommended_frequency_months']
            if freq_months == -1:
                # Use node's expected_lifespan
                node_lifespan = attrs.get('expected_lifespan')
                if node_lifespan is None:
                    raise ValueError(f"expected_lifespan missing for node {node_id} but required by template {task_id}")
                freq_months = int(node_lifespan)
            if freq_months > 0:
                scheduled_dt = install_dt + relativedelta(months=int(freq_months))
                scheduled_date = scheduled_dt.isoformat()
            else:
                scheduled_date = install_dt.isoformat()

            # Determine money_cost
            money_cost = template['money_cost']
            if money_cost == -1:
                node_replacement_cost = attrs.get('replacement_cost')
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
            }
            # Check for any None values in required fields
            for k in ['recommended_frequency_months', 'default_priority', 'time_cost', 'money_cost']:
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
    # TODO: Implement CSV writing logic
    ...

# Placeholder: Update task status
def update_task_status(tasks: List[Dict[str, Any]], task_id: str, new_status: str):
    """Update the status of a specific task (if tracking template status, e.g., for review/approval)."""
    # TODO: Implement status update logic
    ...

# Additional helper functions can be added as needed

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
    graph_file = "./graph_outputs/generated_graph_20250727_220854.mepg"
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

        # Save to CSV
        output_dir = "./maintenance_tasks/"
        filenname = "example_detailed_maintenance_tasks.csv"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        output_path = os.path.join(output_dir, filenname)
        print(f"Exporting tasks to: {output_path}")
        export_tasks_to_csv(tasks, output_path)
        print(f"Tasks exported successfully to {output_path}")
    except Exception as e:
        print(f"Error generating maintenance tasks: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
