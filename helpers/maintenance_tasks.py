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
                'notes': template.get('notes'),
                'description': template.get('description'),
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
    """Create an interactive HTML timeline visualization of the prioritized maintenance schedule.
    
    Shows tasks as colored cards organized into four categories:
    - New Completed: Green cards for newly completed tasks
    - New Deferred: Orange cards for newly deferred tasks
    - Deferred Completed: Light green cards for previously deferred tasks that are now completed
    - Deferred Deferred: Red cards for tasks that remain deferred
    
    Saves as an interactive HTML file with timeline slider controls.

    Display a vertical list of cards which represent tasks in each month.
    Each card shows:
    - Task ID
    - Equipment ID
    - Number of months deferred (if applicable)
    - Time cost
    - Money cost
    - Status on current month (completed, deferred)

    The tasks will be organized into two lists:
    - Completed tasks
    - Deferred tasks

    The tasks will be colored based on their status:
    - Completed that are new: green
    - Completed that were deferred: light green
    - Deferred that are new: orange
    - Deferred that were completed: red

    The timeline will have a slider to navigate through months, with play/pause controls.
    
    Animation:
    The timeline will animate the transition of tasks from one month to the next.  When the timeline changes from one month to the next,
    tasks that were deferred last month but are now completed will slide from the deferred list to the completed list.
    Tasks in each column will be sorted by their priority score, with the highest priority tasks at the top.
    From month to month, the tasks will slide to their new positions based on their status and priority.

    """
    print("Creating animated timeline visualization...")
    
    # Collect task data organized by month and category
    month_data = {}
    all_months = sorted(prioritized_schedule.keys())[:-1]  # Exclude the last month if it has no tasks
    
    # Process data for each month
    for index, month in enumerate(all_months):
        month_tasks = prioritized_schedule[month]
        
        # Calculate budget usage for this month
        all_completed = month_tasks['new_completed'] + month_tasks['deferred_completed']
        total_time_used = sum(task.get('time_cost', 0) for task in all_completed)
        total_money_used = sum(task.get('money_cost', 0) for task in all_completed)
        
        month_data[month] = {
            'index': index,
            'budget_used': {
                'time': total_time_used,
                'money': total_money_used
            },
            'tasks': {
                'new_completed': month_tasks['new_completed'],
                'new_deferred': month_tasks['new_deferred'], 
                'deferred_completed': month_tasks['deferred_completed'],
                'deferred_deferred': month_tasks['deferred_deferred']
            }
        }
    
    # Create timeline data structure for JavaScript
    timeline_data = {
        'months': all_months,
        'data': month_data,
        'budget': {
            'time': monthly_budget_time,
            'money': monthly_budget_money
        }
    }
    
    # Generate HTML content
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Maintenance Timeline - {monthly_budget_time}h/${monthly_budget_money}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        
        .timeline-controls {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        
        #play-pause {{
            background: #007ACC;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }}
        
        #play-pause:hover {{
            background: #005a9e;
        }}
        
        #month-slider {{
            flex: 1;
            height: 6px;
            -webkit-appearance: none;
            appearance: none;
            background: #ddd;
            border-radius: 3px;
            outline: none;
        }}
        
        #month-slider::-webkit-slider-thumb {{
            -webkit-appearance: none;
            appearance: none;
            width: 20px;
            height: 20px;
            background: #007ACC;
            border-radius: 50%;
            cursor: pointer;
        }}
        
        #current-month-display {{
            font-weight: bold;
            font-size: 18px;
            color: #333;
            min-width: 80px;
        }}
        
        .timeline-container {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 20px;
        }}
        
        .month-display {{
            text-align: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #eee;
        }}
        
        #month-title {{
            margin: 0 0 10px 0;
            color: #333;
            font-size: 24px;
        }}
        
        .budget-info {{
            display: flex;
            justify-content: center;
            gap: 30px;
            font-size: 14px;
            color: #666;
        }}
        
        .budget-item {{
            background: #f8f9fa;
            padding: 8px 12px;
            border-radius: 4px;
        }}
        
        .task-columns {{
            display: flex;
            gap: 20px;
            min-height: 500px;
        }}
        
        .completed-column, .deferred-column {{
            flex: 1;
            background: #fafafa;
            border-radius: 8px;
            padding: 15px;
        }}
        
        .completed-column h3, .deferred-column h3 {{
            margin: 0 0 15px 0;
            text-align: center;
            padding: 10px;
            border-radius: 4px;
            color: white;
        }}
        
        .completed-column h3 {{
            background: #4CAF50;
        }}
        
        .deferred-column h3 {{
            background: #FF9800;
        }}
        
        .task-list {{
            display: flex;
            flex-direction: column;
            gap: 8px;
            min-height: 400px;
        }}
        
        .task-card {{
            background: white;
            border-radius: 6px;
            padding: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border-left: 4px solid;
            transition: all 0.3s ease;
            cursor: pointer;
            opacity: 1;
            transform: translateY(0);
        }}
        
        .task-card:hover {{
            box-shadow: 0 2px 6px rgba(0,0,0,0.15);
            transform: translateY(-1px);
        }}
        
        .task-card.new-completed {{
            border-left-color: #4CAF50;
            background: #f8fff8;
        }}
        
        .task-card.deferred-completed {{
            border-left-color: #81C784;
            background: #f0f8f0;
        }}
        
        .task-card.new-deferred {{
            border-left-color: #FF9800;
            background: #fff8f0;
        }}
        
        .task-card.deferred-deferred {{
            border-left-color: #F44336;
            background: #fff0f0;
        }}
        
        .task-header {{
            font-weight: bold;
            font-size: 14px;
            margin-bottom: 6px;
            color: #333;
        }}
        
        .task-details {{
            font-size: 12px;
            color: #666;
            line-height: 1.3;
        }}
        
        .task-costs {{
            display: flex;
            justify-content: space-between;
            margin-top: 6px;
            font-size: 11px;
            color: #888;
        }}
        
        .deferred-badge {{
            background: #ff4444;
            color: white;
            padding: 2px 6px;
            border-radius: 10px;
            font-size: 10px;
            font-weight: bold;
            margin-left: 8px;
        }}
        
        .risk-badge {{
            background: #2196F3;
            color: white;
            padding: 2px 6px;
            border-radius: 10px;
            font-size: 10px;
            font-weight: bold;
            margin-left: 8px;
        }}
        
        .task-card.moving {{
            transition: all 0.8s cubic-bezier(0.4, 0, 0.2, 1);
            z-index: 10;
        }}
        
        .task-card.cross-column {{
            transition: all 1s ease-in-out;
            z-index: 15;
        }}
        
        .task-card.fade-in {{
            animation: fadeIn 0.6s ease-in;
        }}
        
        .task-card.fade-out {{
            animation: fadeOut 0.6s ease-out;
        }}
        
        .task-card.slide-enter {{
            animation: slideEnter 0.8s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        
        .task-card.position-change {{
            transition: transform 0.7s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(-30px) scale(0.95); }}
            to {{ opacity: 1; transform: translateY(0) scale(1); }}
        }}
        
        @keyframes fadeOut {{
            from {{ opacity: 1; transform: translateY(0) scale(1); }}
            to {{ opacity: 0; transform: translateY(30px) scale(0.95); }}
        }}
        
        @keyframes slideEnter {{
            from {{ 
                opacity: 0; 
                transform: translateX(-100px) translateY(-20px) scale(0.9); 
            }}
            to {{ 
                opacity: 1; 
                transform: translateX(0) translateY(0) scale(1); 
            }}
        }}
        
        /* Position containers for smooth transitions */
        .task-list {{
            position: relative;
        }}
        
        .task-card.absolute-positioned {{
            position: absolute;
            width: calc(100% - 16px);
        }}
        
        .empty-state {{
            text-align: center;
            color: #999;
            font-style: italic;
            padding: 40px 20px;
        }}
    </style>
</head>
<body>
    <div class="timeline-controls">
        <button id="play-pause">▶ Play</button>
        <input type="range" id="month-slider" min="0" max="{len(all_months)-1}" value="0" step="1">
        <span id="current-month-display">{all_months[0] if all_months else 'N/A'}</span>
    </div>
    
    <div class="timeline-container">
        <div class="month-display">
            <div class="budget-info">
                <h2 id="month-title">Month 1: {all_months[0] if all_months else 'No Data'}</h2>
                <div class="budget-item">
                    <strong>Time:</strong> <span id="time-used">0</span>/{monthly_budget_time} hours
                    (<span id="time-percent">0%</span>)
                </div>
                <div class="budget-item">
                    <strong>Money:</strong> $<span id="money-used">0</span>/${monthly_budget_money}
                    (<span id="money-percent">0%</span>)
                </div>
                <div class="budget-item">
                    <strong>Tasks:</strong> <span id="tasks-completed">0</span>/<span id="tasks-total">0</span>
                    (<span id="tasks-percent">0%</span>)
                </div>
            </div>
        </div>
        
        <div class="task-columns">
            <div class="completed-column">
                <h3>✓ Completed Tasks (<span id="completed-count">0</span>)</h3>
                <div id="completed-tasks" class="task-list">
                    <div class="empty-state">No completed tasks</div>
                </div>
            </div>
            <div class="deferred-column">
                <h3>⏸ Deferred Tasks (<span id="deferred-count">0</span>)</h3>
                <div id="deferred-tasks" class="task-list">
                    <div class="empty-state">No deferred tasks</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Timeline data
        const timelineData = {json.dumps(timeline_data, indent=8)};
        
        let currentMonthIndex = 0;
        let isPlaying = false;
        let playInterval = null;
        const animationSpeed = 2000; // ms between months
        
        // DOM elements
        const playPauseBtn = document.getElementById('play-pause');
        const monthSlider = document.getElementById('month-slider');
        const currentMonthDisplay = document.getElementById('current-month-display');
        const monthTitle = document.getElementById('month-title');
        const timeUsed = document.getElementById('time-used');
        const timePercent = document.getElementById('time-percent');
        const moneyUsed = document.getElementById('money-used');
        const moneyPercent = document.getElementById('money-percent');
        const completedTasksList = document.getElementById('completed-tasks');
        const deferredTasksList = document.getElementById('deferred-tasks');
        const completedCount = document.getElementById('completed-count');
        const deferredCount = document.getElementById('deferred-count');
        const tasksCompleted = document.getElementById('tasks-completed');
        const tasksTotal = document.getElementById('tasks-total');
        const tasksPercent = document.getElementById('tasks-percent');
        
        function createTaskCard(task, category) {{
            const card = document.createElement('div');
            card.className = `task-card ${{category}}`;
            card.dataset.taskId = task.task_instance_id;
            
            const monthsDeferred = task.months_deferred || 0;
            const deferredBadge = monthsDeferred > 0 ? 
                `<span class="deferred-badge">${{monthsDeferred}}mo</span>` : '';
            
            const riskScore = task.node_risk_score || 0;
            const riskBadge = `<span class="risk-badge">Risk: ${{riskScore.toFixed(3)}}</span>`;
            
            card.innerHTML = `
                <div class="task-details">
                    <b>Task ID: ${{task.task_instance_id}}${{deferredBadge}}</b> | Type: ${{task.task_type}} | Status: ${{task.status}} | Time: ${{(task.time_cost || 0).toFixed(1)}}h | Cost: ${{(task.money_cost || 0).toFixed(0)}} | ${{riskBadge}}
                </div>
            `;
            
            return card;
        }}
        
        function sortTasksByPriority(tasks) {{
            return tasks.sort((a, b) => {{
                const scoreA = a.node_risk_score || 0;
                const scoreB = b.node_risk_score || 0;
                return scoreB - scoreA; // Higher risk first
            }});
        }}
        
        function renderMonth(monthIndex, animate = true) {{
            if (monthIndex < 0 || monthIndex >= timelineData.months.length) return;
            
            const month = timelineData.months[monthIndex];
            const monthData = timelineData.data[month];
            
            // Update header
            monthTitle.textContent = `Month ${{monthIndex + 1}}: ${{month}}`;
            currentMonthDisplay.textContent = month;
            
            // Update budget info
            const budgetUsed = monthData.budget_used;
            const budget = timelineData.budget;
            
            timeUsed.textContent = budgetUsed.time.toFixed(1);
            timePercent.textContent = ((budgetUsed.time / budget.time) * 100).toFixed(1) + '%';
            moneyUsed.textContent = budgetUsed.money.toFixed(0);
            moneyPercent.textContent = ((budgetUsed.money / budget.money) * 100).toFixed(1) + '%';
            
            // Calculate task completion statistics
            const totalTasksScheduled = (monthData.tasks.new_completed || []).length + 
                                      (monthData.tasks.deferred_completed || []).length +
                                      (monthData.tasks.new_deferred || []).length + 
                                      (monthData.tasks.deferred_deferred || []).length;
            const totalTasksCompleted = (monthData.tasks.new_completed || []).length + 
                                      (monthData.tasks.deferred_completed || []).length;
            
            tasksCompleted.textContent = totalTasksCompleted;
            tasksTotal.textContent = totalTasksScheduled;
            tasksPercent.textContent = totalTasksScheduled > 0 ? 
                ((totalTasksCompleted / totalTasksScheduled) * 100).toFixed(1) + '%' : '0%';
            
            // Prepare task lists
            const completedTasks = [
                ...sortTasksByPriority(monthData.tasks.new_completed || []),
                ...sortTasksByPriority(monthData.tasks.deferred_completed || [])
            ];
            
            const deferredTasks = [
                ...sortTasksByPriority(monthData.tasks.new_deferred || []),
                ...sortTasksByPriority(monthData.tasks.deferred_deferred || [])
            ];
            
            // Clear existing content
            completedTasksList.innerHTML = '';
            deferredTasksList.innerHTML = '';
            
            // Update counters
            completedCount.textContent = completedTasks.length;
            deferredCount.textContent = deferredTasks.length;
            
            // Render completed tasks
            if (completedTasks.length === 0) {{
                completedTasksList.innerHTML = '<div class="empty-state">No completed tasks</div>';
            }} else {{
                completedTasks.forEach((task, index) => {{
                    const category = (monthData.tasks.new_completed || []).includes(task) ? 
                        'new-completed' : 'deferred-completed';
                    const card = createTaskCard(task, category);
                    
                    if (animate) {{
                        card.style.opacity = '0';
                        card.style.transform = 'translateY(-20px)';
                        completedTasksList.appendChild(card);
                        
                        setTimeout(() => {{
                            card.style.transition = 'all 0.3s ease';
                            card.style.opacity = '1';
                            card.style.transform = 'translateY(0)';
                        }}, index * 50);
                    }} else {{
                        completedTasksList.appendChild(card);
                    }}
                }});
            }}
            
            // Render deferred tasks
            if (deferredTasks.length === 0) {{
                deferredTasksList.innerHTML = '<div class="empty-state">No deferred tasks</div>';
            }} else {{
                deferredTasks.forEach((task, index) => {{
                    const category = (monthData.tasks.new_deferred || []).includes(task) ? 
                        'new-deferred' : 'deferred-deferred';
                    const card = createTaskCard(task, category);
                    
                    if (animate) {{
                        card.style.opacity = '0';
                        card.style.transform = 'translateY(-20px)';
                        deferredTasksList.appendChild(card);
                        
                        setTimeout(() => {{
                            card.style.transition = 'all 0.3s ease';
                            card.style.opacity = '1';
                            card.style.transform = 'translateY(0)';
                        }}, index * 50);
                    }} else {{
                        deferredTasksList.appendChild(card);
                    }}
                }});
            }}
        }}
        
        function updateControls() {{
            monthSlider.value = currentMonthIndex;
            playPauseBtn.textContent = isPlaying ? '⏸ Pause' : '▶ Play';
        }}
        
        function play() {{
            if (isPlaying) return;
            
            isPlaying = true;
            updateControls();
            
            playInterval = setInterval(() => {{
                if (currentMonthIndex < timelineData.months.length - 1) {{
                    currentMonthIndex++;
                    renderMonth(currentMonthIndex, true);
                    updateControls();
                }} else {{
                    pause();
                }}
            }}, animationSpeed);
        }}
        
        function pause() {{
            isPlaying = false;
            if (playInterval) {{
                clearInterval(playInterval);
                playInterval = null;
            }}
            updateControls();
        }}
        
        function goToMonth(index) {{
            pause();
            currentMonthIndex = Math.max(0, Math.min(index, timelineData.months.length - 1));
            renderMonth(currentMonthIndex, true);
            updateControls();
        }}
        
        // Event listeners
        playPauseBtn.addEventListener('click', () => {{
            if (isPlaying) {{
                pause();
            }} else {{
                play();
            }}
        }});
        
        monthSlider.addEventListener('input', (e) => {{
            goToMonth(parseInt(e.target.value));
        }});
        
        // Keyboard controls
        document.addEventListener('keydown', (e) => {{
            switch(e.code) {{
                case 'Space':
                    e.preventDefault();
                    if (isPlaying) pause(); else play();
                    break;
                case 'ArrowLeft':
                    e.preventDefault();
                    goToMonth(currentMonthIndex - 1);
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    goToMonth(currentMonthIndex + 1);
                    break;
            }}
        }});
        
        // Initialize
        if (timelineData.months.length > 0) {{
            renderMonth(0, false);
            updateControls();
        }}
    </script>
</body>
</html>"""
    
    # Save to file
    output_dir = "./maintenance_tasks/"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    filename = f"maintenance_timeline_budget_{monthly_budget_time}h_{monthly_budget_money}usd.html"
    output_path = os.path.join(output_dir, filename)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Interactive timeline saved to: {output_path}")
    print("Open the HTML file in a web browser to view the animation.")
    print("Controls: Use the slider, play/pause buttons, or arrow keys (←/→) and spacebar to navigate.")

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
        month_tasks.sort(key=lambda t: t.get('node_risk_score'), reverse=True)

        # Track budgets for this month
        remaining_time = monthly_budget_time
        remaining_money = monthly_budget_money

        # Four categories
        new_completed = []
        new_deferred = []
        deferred_completed = []
        deferred_deferred = []

        # Select tasks until budget is exceeded
        for task in month_tasks:
            task_time = task.get('time_cost') or 0
            task_money = task.get('money_cost') or 0
            is_deferred = task.get('months_deferred', 0) > 0

            # Check if task fits in remaining budget
            if task_time <= remaining_time and task_money <= remaining_money:
                # Task can be completed
                remaining_time -= task_time
                remaining_money -= task_money

                # Mark as completed and add to appropriate list
                task_copy = task.copy()
                task_copy['status'] = 'completed'
                if is_deferred:
                    deferred_completed.append(task_copy)
                else:
                    new_completed.append(task_copy)

                # Generate future maintenance task
                current_date = datetime.datetime.strptime(task['scheduled_date'], '%Y-%m-%d')
                frequency_months = task.get('recommended_frequency_months')
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
                    if is_deferred:
                        deferred_deferred.append(deferred_task)
                    else:
                        new_deferred.append(deferred_task)

                    # Add to next month in calendar_schedule
                    if next_month not in calendar_schedule:
                        calendar_schedule[next_month] = []
                    calendar_schedule[next_month].append(deferred_task)

        # Store the prioritized tasks for this month in four categories
        prioritized_schedule[month] = {
            'new_completed': new_completed,
            'new_deferred': new_deferred,
            'deferred_completed': deferred_completed,
            'deferred_deferred': deferred_deferred
        }

        # Print summary for this month
        total_time_used = monthly_budget_time - remaining_time
        total_money_used = monthly_budget_money - remaining_money

        print(f"New completed tasks: {len(new_completed)}")
        print(f"New deferred tasks: {len(new_deferred)}")
        print(f"Deferred completed tasks: {len(deferred_completed)}")
        print(f"Deferred deferred tasks: {len(deferred_deferred)}")
        print(f"Time used: {total_time_used:.1f}/{monthly_budget_time:.1f} hours ({total_time_used/monthly_budget_time*100:.1f}%)")
        print(f"Money used: ${total_money_used:.2f}/${monthly_budget_money:.2f} ({total_money_used/monthly_budget_money*100:.1f}%)")

        if new_deferred or deferred_deferred:
            print(f"Deferred task details:")
            for dt in new_deferred + deferred_deferred:
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
    calendar_schedule = prioritize_calendar_tasks(calendar_schedule=calendar_schedule, monthly_budget_time=10, monthly_budget_money=100)

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
