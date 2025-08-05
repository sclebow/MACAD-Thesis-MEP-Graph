import os
import json

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
    all_months = sorted(prioritized_schedule.keys())
    
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

