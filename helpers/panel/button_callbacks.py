# This is a helper function for the button callbacks
import panel as pn
import networkx as nx
import datetime
import base64
import pandas as pd

from helpers.controllers.graph_controller import GraphController

def upload_graph_from_file(file_content, filename, graph_controller, graph_container):
    """Handle file upload and update graph visualization"""
    print(f"Uploading file: {filename}")
    
    # Load graph using GraphController
    result = graph_controller.load_graph_from_file(file_content)
    
    if result['success']:
        # Update the graph visualization
        fig = graph_controller.get_visualization_data()
        graph_container.object = fig
        print(f"Graph loaded successfully from {filename}")
    else:
        print(f"Error loading graph: {result.get('error', 'Unknown error')}")
        graph_container.object = None

def export_graph(event, graph_controller: GraphController, app):
    now = datetime.datetime.now()
    now_str = now.strftime("%Y%m%d_%H%M%S")
    filename = f"exported_graph_{now_str}.mepg"

    graph = graph_controller.current_graph[0]

    # Get the graphml representation
    graphml_generator = nx.generate_graphml(graph)

    print(graphml_generator)

    lines = []

    for line in graphml_generator:
        lines.append(line)

    file_string = "\n".join(lines)

    # Encode the file content
    file_bytes = file_string.encode('utf-8')
    b64_content = base64.b64encode(file_bytes).decode('utf-8')
    
    # Create download HTML
    download_html = f"""
    <script>
    var element = document.createElement('a');
    element.setAttribute('href', 'data:text/plain;charset=utf-8;base64,{b64_content}');
    element.setAttribute('download', '{filename}');
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
    </script>
    """
    
    # Display the download HTML (this triggers the download)
    download_pane = pn.pane.HTML(download_html)
    
    # You can add this to a temporary container or use a notification
    print(f"Exporting graph as {filename}")
    app.append(download_pane)

def reset_graph(event, graph_controller):
    # Reset the panel application
    pn.state.location.reload = False
    pn.state.location.reload = True

def failure_timeline_reset_view(event):
    print("Failure Timeline Reset View button clicked")

def failure_timeline_zoom_in(event):
    print("Failure Timeline Zoom In button clicked")

def failure_timeline_zoom_out(event):
    print("Failure Timeline Zoom Out button clicked")

def export_failure_schedule(event):
    print("Export Failure Schedule button clicked")

def export_annual_budget_forecast(event):
    print("Export Annual Budget Forecast button clicked")

def reset_lifecycle_analysis_controls(event):
    print("Reset Lifecycle Analysis Controls button clicked")

def run_lifecycle_analysis_simulation(event):
    print("Run Lifecycle Analysis Simulation button clicked")

def save_settings(event):
    print("Save Settings button clicked")

def import_data(event):
    print("Import Data button clicked")

def export_data(event):
    print("Export Data button clicked")

def clear_all_data(event):
    print("Clear All Data button clicked")

# Function to handle node clicks
def update_node_details(graph_controller, graph_container, equipment_details_container):
    """Update node details based on selection"""
    current_graph = graph_controller.current_graph[0] if graph_controller.current_graph[0] else None

    click_data = graph_container.click_data
    # print(f"Click data: {click_data}")
    
    if 'points' in click_data and len(click_data['points']) > 0:
        point = click_data['points'][0]
        display_name = point.get('text', '')
        
        # Find the node ID that matches this display name
        node_id = None
        use_full_names = graph_controller.view_settings.get('use_full_names', False)
        
        for n_id, attrs in current_graph.nodes(data=True):
            if use_full_names:
                node_display = attrs.get('full_name', n_id)
            else:
                node_display = str(n_id)
            
            if str(node_display) == str(display_name):
                node_id = n_id
                break
        
        # if node_id and node_id in current_graph.nodes:
        node_attrs = current_graph.nodes[node_id]
        
        markdown_lines = []
        markdown_lines.append(f"### Equipment Details: {display_name}")
        markdown_lines.append("---")

        # Display attributes
        for key, value in node_attrs.items():
            if key not in ['x', 'y', 'z']:
                formatted_key = key.replace('_', ' ').title()
                markdown_lines.append(f"**{formatted_key}:** {value}")

        # Add coordinates
        coords = []
        for coord in ['x', 'y', 'z']:
            if coord in node_attrs:
                coords.append(f"{coord.upper()}: {node_attrs[coord]}")

        markdown_lines.extend([
            "---",
            "**Location:**",
            ", ".join(coords)
        ])
        markdown_strings = "\n\n".join(markdown_lines)
        print(markdown_strings)
        markdown_pane = pn.pane.Markdown(markdown_strings)
        equipment_details_container.clear()
        equipment_details_container.extend([markdown_pane])
        print(f"Updated details for: {node_id}")

def update_graph_container_visualization(event, graph_controller: GraphController, visualization_type_dict, graph_container):
    graph_controller.update_visualization_type(visualization_type_dict[event.new])
    graph_container.object = graph_controller.get_visualization_data()

def maintenance_task_list_upload(event, graph_controller: GraphController, maintenance_task_list_viewer):
    print("Task List Uploaded")
    # Read byte content from the uploaded file
    file_content = event.new  # event.new is already bytes

    graph_controller.upload_maintenance_task_list(file_content)
    df = graph_controller.get_maintenance_task_list_df()
    maintenance_task_list_viewer.value = df

def update_hours_budget(event, graph_controller: GraphController):
    graph_controller.update_hours_budget(event.new)

def update_money_budget(event, graph_controller: GraphController):
    graph_controller.update_money_budget(event.new)

def update_weeks_to_schedule(event, graph_controller: GraphController):
    graph_controller.update_weeks_to_schedule(event.new)

def replacement_task_list_upload(event, graph_controller: GraphController, replacement_task_list_viewer):
    print("Replacement Task List Uploaded")
    # Read byte content from the uploaded file
    file_content = event.new  # event.new is already bytes

    graph_controller.upload_replacement_task_list(file_content)
    df = graph_controller.get_replacement_task_list_df()
    replacement_task_list_viewer.value = df

def run_simulation(event, graph_controller: GraphController):
    graph_controller.run_rul_simulation()

    # Get the schedule maintenance_schedule_container from pn.state.cache
    maintenance_schedule_container = pn.state.cache['maintenance_schedule_container']

    # Get the schedule from cache
    schedule = graph_controller.prioritized_schedule
    
    # Convert the prioritized schedule to a DataFrame for display
    all_tasks = []
    for month, record in schedule.items():
        # Add executed tasks with month info
        for task in record['executed_tasks']:
            task_copy = dict(task)
            task_copy['month'] = str(month)
            task_copy['status'] = 'executed'
            all_tasks.append(task_copy)
        
        # Add deferred tasks with month info
        for task in record['deferred_tasks']:
            task_copy = dict(task)
            task_copy['month'] = str(month)
            task_copy['status'] = 'deferred'
            all_tasks.append(task_copy)
    
    tasks_df = pd.DataFrame(all_tasks)
    # Sort by month and priority for better readability
    tasks_df = tasks_df.sort_values(['month', 'priority'])
    
    # Create summary statistics
    summary_stats = []
    for month, record in schedule.items():
        executed_count = len(record['executed_tasks'])
        deferred_count = len(record['deferred_tasks'])
        time_used = record['time_budget'] - sum(t['time_cost'] for t in record['executed_tasks'])
        money_used = record['money_budget'] - sum(t['money_cost'] for t in record['executed_tasks'])
        
        summary_stats.append({
            'month': str(month),
            'executed_tasks': executed_count,
            'deferred_tasks': deferred_count,
            'time_remaining': time_used,
            'money_remaining': money_used
        })
    
    summary_df = pd.DataFrame(summary_stats)
    
    # Create tabs for different views
    results_panel = pn.Tabs(
        ("Task Details", pn.widgets.DataFrame(tasks_df, sizing_mode="stretch_width", height=400)),
        ("Monthly Summary", pn.widgets.DataFrame(summary_df, sizing_mode="stretch_width", height=400)),
        sizing_mode="stretch_width"
    )
    
    maintenance_schedule_container.clear()
    maintenance_schedule_container.append(pn.pane.Markdown("### Simulation Results"))
    maintenance_schedule_container.append(results_panel)

    # Update the failure timeline container
    task_timeline_container = pn.state.cache.get("task_timeline_container")
    fig = graph_controller.get_bar_chart_figure()
    task_timeline_container.object = fig

    # Update the system_health_container
    system_health_container = pn.state.cache.get("system_health_container")
    system_health_container.clear()
    system_health_str_list = []
    system_health_str_list.append("### System Health Overview")

    current_date_graph = graph_controller.get_current_date_graph()

    node_conditions = []
    for node_id, attrs in current_date_graph.nodes(data=True):
        if 'current_condition' in attrs:
            node_conditions.append(attrs.get('current_condition'))
    total_number_of_nodes = len(node_conditions)
    average_condition = sum(node_conditions) / total_number_of_nodes if total_number_of_nodes > 0 else 0

    system_health_str_list.append(f"**Average Condition**: {average_condition:.0%}")
    system_health_str_list.append(f"**Total Number of Nodes**: {total_number_of_nodes}")

    node_risk_levels = []
    for node_id, attrs in current_date_graph.nodes(data=True):
        if 'risk_level' in attrs:
            node_risk_levels.append(attrs.get('risk_level'))
    unique_risk_levels = set(node_risk_levels)

    risk_str_list = []
    for risk_level in unique_risk_levels:
        risk_str_list.append(f"**{risk_level}**: {node_risk_levels.count(risk_level)}")

    risk_str = " | ".join(risk_str_list)
    system_health_str_list.append(f"**Risk Levels**: {risk_str}")

    system_health_container.append(pn.pane.Markdown("\n\n".join(system_health_str_list)))

    # Update the critical_component_container
    critical_component_container = pn.state.cache.get("critical_component_container")
    critical_component_container.clear()
    critical_component_list = []
    critical_component_list.append("### Critical Component Overview")

    critical_nodes = [node for node, attrs in current_date_graph.nodes(data=True) if attrs.get('risk_level') == 'CRITICAL']
    critical_component_list.append(f"**Critical Components**: {len(critical_nodes)}")
    for node in critical_nodes:
        critical_component_list.append(f"1. {node}")
    critical_component_container.append(pn.pane.Markdown("\n\n".join(critical_component_list)))

    # Update the next_12_months_container
    next_12_months_container = pn.state.cache.get("next_12_months_container")
    next_12_months_data = graph_controller.get_next_12_months_data()
    next_12_months_container.clear()
    next_12_months_list = []
    next_12_months_list.append("### Next 12 Months Overview")
    for month, data_dict in next_12_months_data.items():
        expected_tasks_for_month = data_dict.get('executed_tasks')
        deferred_tasks_for_month = data_dict.get('deferred_tasks')
        # Convert DataFrame to list of dicts
        # tasks_scheduled_for_month = tasks_scheduled_for_month.to_dict(orient='records')
        # print(f"Month: {month}, Tasks: {tasks_scheduled_for_month}")
        next_12_months_list.append(f"**{month}**:")
        next_12_months_list.append(f"- **Expected Executed Tasks**: {len(expected_tasks_for_month)}")
        if len(expected_tasks_for_month) > 0:
            next_12_months_list.append(f"- **Most Critical Expected Task**: {expected_tasks_for_month[0].get('task_instance_id')}")
        next_12_months_list.append(f"- **Deferred Tasks**: {len(deferred_tasks_for_month)}")
        if len(deferred_tasks_for_month) > 0:
            next_12_months_list.append(f"- **Most Critical Deferred Task**: {deferred_tasks_for_month[0].get('task_instance_id')}")

    next_12_months_container.append(pn.pane.Markdown("\n\n".join(next_12_months_list)))

    # Update the cost_forecast_container
    cost_forecast_container = pn.state.cache.get("cost_forecast_container")
    cost_forecast_container.clear()
    cost_forecast_str_list = []

    next_12_months_money_cost = 0
    next_12_months_time_cost = 0
    for month, data_dict in next_12_months_data.items():
        tasks_scheduled_for_month = data_dict.get('executed_tasks', [])
        for task in tasks_scheduled_for_month:
            money_cost = task.get('money_cost')
            time_cost = task.get('time_cost')
            next_12_months_money_cost += money_cost
            next_12_months_time_cost += time_cost

    cost_forecast_str_list.append(f"### Cost Forecast Overview")
    cost_forecast_str_list.append(f"**Total Expected Money Cost for Next 12 Months**: \\${next_12_months_money_cost}")
    cost_forecast_str_list.append(f"**Total Expected Time Cost for Next 12 Months**: {next_12_months_time_cost} hours")
    cost_forecast_container.append(pn.pane.Markdown("\n\n".join(cost_forecast_str_list)))

    # Create the failure timeline figure
    failure_timeline_fig, node_dict = graph_controller.get_current_date_failure_timeline_figure()
    failure_timeline_container = pn.state.cache.get("failure_timeline_container")
    # from helpers.visualization import _generate_2d_graph_figure
    # failure_timeline_container.object = _generate_2d_graph_figure(current_date_graph)
    failure_timeline_container.object = failure_timeline_fig

    # Update the failure schedule
    failure_schedule_dataframe = pn.state.cache.get("failure_schedule_dataframe")
    df = pd.DataFrame.from_dict(node_dict, orient="index")
    failure_schedule_dataframe.value = df

def update_current_date(event, graph_controller: GraphController):
    print("Current date updated to:", event.new)
    graph_controller.current_date = event.new

    # Update the simulation
    run_simulation(None, graph_controller)

def update_failure_component_details(graph_controller: GraphController, failure_timeline_container):
    component_details_container = pn.state.cache["component_details_container"]

    component_details_container.clear()
    selected_failure = failure_timeline_container.click_data
    if selected_failure:
        component_details_str_list = []
        # print(selected_failure.get('points')[0].get('hovertext'))
        y = selected_failure.get('points')[0].get('y')
        hover = selected_failure.get('points')[0].get('hovertext')
        component_details_str_list.append(f"### Component Details for {y}")
        component_details_str_list.append(hover)
        component_details_container.append(pn.pane.Markdown("\n\n".join(component_details_str_list)))