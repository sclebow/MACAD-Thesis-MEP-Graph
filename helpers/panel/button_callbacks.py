# This is a helper function for the button callbacks
import panel as pn
import networkx as nx
import datetime
import base64
import pandas as pd
import pickle

from helpers.controllers import graph_controller
from helpers.controllers.graph_controller import GraphController
from helpers.panel.analytics_viz import _create_enhanced_kpi_card
from helpers.visualization import get_remaining_useful_life_fig, get_risk_distribution_fig, get_equipment_conditions_fig, get_maintenance_costs_fig

def update_system_view_graph_container(graph_controller: GraphController):
    fig = graph_controller.get_visualization_data()
    graph_container = pn.state.cache.get("graph_container")
    graph_container.object = fig

def upload_graph_from_file(file_content, filename, graph_controller):
    """Handle file upload and update graph visualization"""
    print(f"Uploading file: {filename}")
    
    # Load graph using GraphController
    result = graph_controller.load_graph_from_file(file_content)
    
    if result['success']:
        # Update the graph visualization
        update_system_view_graph_container(graph_controller)
        print(f"Graph loaded successfully from {filename}")
    else:
        print(f"Error loading graph: {result.get('error', 'Unknown error')}")
        graph_container = pn.state.cache.get("graph_container")
        graph_container.object = None

def export_graph(event, graph_controller: GraphController):
    app = pn.state.cache.get('app')

    now = datetime.datetime.now()
    now_str = now.strftime("%Y%m%d_%H%M%S")
    filename = f"exported_graph_{now_str}.mepg"

    graph = graph_controller.current_graph[0]

    # Get the graphml representation
    graphml_generator = nx.generate_graphml(graph)

    # print(graphml_generator)

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

def import_data(event, graph_controller):
    print("Import Data button clicked")


def export_data(event, graph_controller):
    print("Export Data button clicked")
    data_dict = graph_controller.export_data()

    # Prepare Pickle file content
    pickle_bytes = pickle.dumps(data_dict)
    b64_content = base64.b64encode(pickle_bytes).decode('utf-8')
    filename = f"exported_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"

    # Create download HTML
    download_html = f"""
    <script>
    var element = document.createElement('a');
    element.setAttribute('href', 'data:application/octet-stream;base64,{b64_content}');
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
    print(f"Exporting data as {filename}")

    settings_container = pn.state.cache.get('settings_container')
    settings_container.append(download_pane)

def clear_all_data(event):
    print("Clear All Data button clicked")

# Function to handle node clicks
def update_node_details(graph_controller, graph_container, equipment_details_container):
    """Update node details based on selection"""
    current_graph = graph_controller.current_graph[0] if graph_controller.current_graph[0] else None

    click_data = graph_container.click_data
    
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
        markdown_pane = pn.pane.Markdown(markdown_strings)
        equipment_details_container.clear()
        equipment_details_container.extend([markdown_pane])
        
def update_graph_container_visualization(event, graph_controller: GraphController, visualization_type_dict, graph_container):
    graph_controller.update_visualization_type(visualization_type_dict[event.new])
    graph_container.object = graph_controller.get_visualization_data()

def maintenance_log_upload(event, graph_controller: GraphController):
    # Read byte content from the uploaded file
    file_content = event.new  # event.new is already bytes

    graph_controller.upload_maintenance_logs(file_content)

    maintenance_log_viewer = pn.state.cache["maintenance_logs_viewer"]
    df_logs = graph_controller.get_maintenance_logs_df()
    maintenance_log_viewer.value = df_logs

    pn.state.cache["generate_synthetic_maintenance_logs"] = False # Disable synthetic log generation after upload

def maintenance_task_list_upload(event, graph_controller: GraphController, maintenance_task_list_viewer):
    # Read byte content from the uploaded file
    file_content = event.new  # event.new is already bytes

    graph_controller.upload_maintenance_task_list(file_content)
    df = graph_controller.get_maintenance_task_list_df()
    maintenance_task_list_viewer.value = df

def update_hours_budget(event, graph_controller: GraphController):
    graph_controller.update_hours_budget(event.new)

    run_simulation(None, graph_controller)

def update_money_budget(event, graph_controller: GraphController):
    graph_controller.update_money_budget(event.new)

    run_simulation(None, graph_controller)

def update_weeks_to_schedule(event, graph_controller: GraphController):
    graph_controller.update_weeks_to_schedule(event.new)

    run_simulation(None, graph_controller)

def replacement_task_list_upload(event, graph_controller: GraphController, replacement_task_list_viewer):
    # Read byte content from the uploaded file
    file_content = event.new  # event.new is already bytes

    graph_controller.upload_replacement_task_list(file_content)
    df = graph_controller.get_replacement_task_list_df()
    replacement_task_list_viewer.value = df

def update_app_status(message: str):
    app_status_container = pn.state.cache['app_status_container']
    app_status_container.clear()
    app_status_container.append(pn.pane.Markdown(f"### Dashboard Status:", align="center"))
    app_status_container.append(pn.pane.Markdown(f"{message}", align="center"))

def run_simulation(event, graph_controller: GraphController):
    print("\nRunning simulation...")

    update_app_status("Updating System View...")
    generated_graph_viewer = pn.state.cache["generated_graph_viewer"]
    generated_graph_viewer.object = graph_controller.get_visualization_data()

    generated_graph_viewer_3d = pn.state.cache["generated_graph_viewer_3d"]
    generated_graph_viewer_3d.object = graph_controller.get_visualization_data(viz_type='3d')

    update_app_status("Running RUL Simulation... Please wait.")
    graph_controller.run_rul_simulation(generate_synthetic_maintenance_logs=pn.state.cache["generate_synthetic_maintenance_logs"])

    # Get the schedule maintenance_schedule_container from pn.state.cache
    maintenance_schedule_container = pn.state.cache['maintenance_schedule_container']

    # Get the schedule from cache
    schedule = graph_controller.prioritized_schedule
    
    update_app_status("RUL Simulation Completed, Updating Dashboard...")
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
    update_app_status("Updating Summary Statistics and Visualizations...")
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

    # Process executed and not executed replacement tasks
    replacement_task_viewer = pn.widgets.DataFrame(sizing_mode="stretch_both", disabled=False, auto_edit=False, show_index=False)
    replacement_tasks = []
    for month, record in schedule.items():
        # print(f"Record keys for month {month}: {list(record.keys())}")
        for task in record['replacement_tasks_executed']:
            # print(f"Month {month} has executed replacement task: {task}")
            task_copy = dict(task)
            task_copy['month'] = str(month)
            task_copy['status'] = 'executed'
            replacement_tasks.append(task_copy)
        # print(f"Month {month} has {len(record['replacement_tasks_not_executed'])} deferred replacement tasks.")
        for task in record['replacement_tasks_not_executed']:
            task_copy = dict(task)
            task_copy['month'] = str(month)
            task_copy['status'] = 'deferred'
            replacement_tasks.append(task_copy)
    replacement_task_viewer.value = pd.DataFrame(replacement_tasks)
    
    # Create tabs for different views
    results_panel = pn.Tabs(
        ("Task Details", pn.widgets.DataFrame(tasks_df, sizing_mode="stretch_both")),
        ("Monthly Summary", pn.widgets.DataFrame(summary_df, sizing_mode="stretch_both")),
        ("Replacement Tasks", replacement_task_viewer),
        sizing_mode="stretch_both"
    )

    # DEBUG: Set default tab to Replacement Tasks for debugging
    results_panel.active = 0

    # Update the budget viewer
    maintenance_budget_viewer = pn.state.cache.get("maintenance_budget_viewer")
    budget_df = graph_controller.get_budget_overview_df()
    maintenance_budget_viewer.value = budget_df

    # Update the budget markdown summary
    maintenance_budget_markdown_summary = pn.state.cache.get("maintenance_budget_markdown_summary")
    maintenance_budget_markdown_summary_str_list = []
    
    total_money_budget_spent_to_date = budget_df[budget_df['Month'] <= str(graph_controller.current_date.to_period('M'))]['Used Money'].sum()
    maintenance_budget_markdown_summary_str_list.append(f"**Total Money Budget Spent to Date**: ${total_money_budget_spent_to_date:,.2f}")

    total_hours_budget_spent_to_date = budget_df[budget_df['Month'] <= str(graph_controller.current_date.to_period('M'))]['Used Hours'].sum()
    maintenance_budget_markdown_summary_str_list.append(f"**Total Hours Budget Spent to Date**: {total_hours_budget_spent_to_date:,.2f}")

    average_monthly_money_budget = budget_df['Used Money'].mean()
    maintenance_budget_markdown_summary_str_list.append(f"**Average Monthly Money Used (Full Schedule)**: ${average_monthly_money_budget:,.2f}")

    average_monthly_hours_budget = budget_df['Used Hours'].mean()
    maintenance_budget_markdown_summary_str_list.append(f"**Average Monthly Hours Used (Full Schedule)**: {average_monthly_hours_budget:,.2f}")

    maintenance_budget_markdown_summary.object = "\n\n".join(maintenance_budget_markdown_summary_str_list)

    maintenance_schedule_container.clear()
    maintenance_schedule_container.sizing_mode = "stretch_both"
    maintenance_schedule_container.append(pn.pane.Markdown("### Simulation Results"))
    maintenance_schedule_container.append(results_panel)

    maintenance_log_viewer = pn.state.cache.get("maintenance_logs_viewer")
    df_logs = graph_controller.get_maintenance_logs_df()
    maintenance_log_viewer.value = df_logs

    # Update the failure timeline container
    update_app_status("Updating Failure Timeline...")
    task_timeline_container = pn.state.cache.get("task_timeline_container")
    fig = graph_controller.get_bar_chart_figure()
    task_timeline_container.object = fig

    # Update the system_health_container
    update_app_status("Updating System Health Overview...")
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
    update_app_status("Updating Critical Component Overview...")
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
    update_app_status("Updating Next 12 Months Overview...")
    next_12_months_container = pn.state.cache.get("next_12_months_container")
    next_12_months_data = graph_controller.get_next_12_months_data()
    next_12_months_container.clear()
    next_12_months_list = []
    next_12_months_list.append("### Next 12 Months Overview")
    for month, data_dict in next_12_months_data.items():
        expected_tasks_for_month = data_dict.get('executed_tasks')
        deferred_tasks_for_month = data_dict.get('deferred_tasks')
        next_12_months_list.append(f"**{month}**:")
        next_12_months_list.append(f"- **Expected Executed Tasks**: {len(expected_tasks_for_month)}")
        if len(expected_tasks_for_month) > 0:
            next_12_months_list.append(f"- **Most Critical Expected Task**: {expected_tasks_for_month[0].get('task_instance_id')}")
        next_12_months_list.append(f"- **Deferred Tasks**: {len(deferred_tasks_for_month)}")
        if len(deferred_tasks_for_month) > 0:
            next_12_months_list.append(f"- **Most Critical Deferred Task**: {deferred_tasks_for_month[0].get('task_instance_id')}")

    next_12_months_container.append(pn.pane.Markdown("\n\n".join(next_12_months_list)))

    # Update the cost_forecast_container
    update_app_status("Updating Cost Forecast Overview...")
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
    update_app_status("Creating Failure Timeline Figure...")
    failure_timeline_fig, node_dict = graph_controller.get_current_date_failure_timeline_figure()
    failure_timeline_container = pn.state.cache.get("failure_timeline_container")
    failure_timeline_container.object = failure_timeline_fig

    # Update the failure schedule
    update_app_status("Updating Failure Schedule...")
    failure_schedule_dataframe = pn.state.cache.get("failure_schedule_dataframe")
    df = pd.DataFrame.from_dict(node_dict, orient="index")
    failure_schedule_dataframe.value = df
    # Update the average system health
    average_system_health_container = pn.state.cache.get("average_system_health_container")
    average_system_health_container.clear()
    
    # Get previous month graph
    update_app_status("Updating KPI Cards...")
    previous_month_graph = graph_controller.get_previous_month_graph()
    def get_average_condition(graph):
        node_conditions = []
        for node_id, attrs in graph.nodes(data=True):
            if 'current_condition' in attrs:
                node_conditions.append(attrs.get('current_condition'))
        total_number_of_nodes = len(node_conditions)
        average_condition = sum(node_conditions) / total_number_of_nodes if total_number_of_nodes > 0 else 0

        return average_condition, total_number_of_nodes
    previous_month_average_condition, previous_month_total_nodes = get_average_condition(previous_month_graph)

    condition_change = previous_month_average_condition - average_condition
    average_system_health_container.append(        
        _create_enhanced_kpi_card(
            title="Average System Health",
            value=f"{average_condition:.0%}",
            trend=condition_change,
            metric_type="System Health",
            unit="%"
        )
    )

    critical_equipment_container = pn.state.cache.get("critical_equipment_container")
    critical_equipment_container.clear()
    def get_number_of_critical_equipment(graph):
        critical_nodes = [n for n, attrs in graph.nodes(data=True) if attrs.get('risk_level') == 'CRITICAL']
        return len(critical_nodes)

    number_of_current_critical_equipment = get_number_of_critical_equipment(current_date_graph)
    number_of_previous_critical_equipment = get_number_of_critical_equipment(previous_month_graph)
    change_in_critical_equipment = number_of_previous_critical_equipment - number_of_current_critical_equipment

    critical_equipment_container.append(
        _create_enhanced_kpi_card(
            title="Critical Equipment",
            value=str(number_of_current_critical_equipment),
            trend=change_in_critical_equipment,
            metric_type="Critical Equipment",
            unit=""
        )
    )

    average_rul_container = pn.state.cache.get("average_rul_container")
    average_rul_container.clear()

    def get_average_remaining_useful_life_days(graph):
        if graph is None:
            return 0
        return sum(node[1].get("remaining_useful_life_days", 0) for node in graph.nodes(data=True)) / len(graph.nodes)

    current_month_average_rul_days = get_average_remaining_useful_life_days(current_date_graph)
    current_month_average_rul_months = current_month_average_rul_days / 30  # Convert days to months
    previous_month_average_rul_days = get_average_remaining_useful_life_days(previous_month_graph)
    previous_month_average_rul_months = previous_month_average_rul_days / 30  # Convert days to months
    change_in_average_rul_days = previous_month_average_rul_days - current_month_average_rul_days
    change_in_average_rul_months = previous_month_average_rul_months - current_month_average_rul_months

    average_rul_container.append(
        _create_enhanced_kpi_card(
            title="Average RUL (Months)",
            value=f"{current_month_average_rul_months:.1f}",
            trend=change_in_average_rul_months,
            metric_type="Avg. RUL",
            unit="months"
        )
    )

    system_reliability_container = pn.state.cache.get("system_reliability_container")
    system_reliability_container.clear()

    def get_system_reliability(graph):
        # Calculate system reliability as percentage of non-critical nodes
        total_nodes = graph.number_of_nodes()
        critical_nodes = [n for n, attrs in graph.nodes(data=True) if attrs.get('risk_level') == 'CRITICAL']
        reliability = ((total_nodes - len(critical_nodes)) / total_nodes) if total_nodes else 0.0
        return reliability

    current_month_system_reliability = get_system_reliability(current_date_graph)
    previous_month_system_reliability = get_system_reliability(previous_month_graph)
    change_in_system_reliability = previous_month_system_reliability - current_month_system_reliability

    system_reliability_container.append(
        _create_enhanced_kpi_card(
            title="System Reliability",
            value=f"{current_month_system_reliability:.1%}",
            trend=change_in_system_reliability,
            metric_type="System Reliability",
            unit='%'
        )
    )

    remaining_useful_life_plot = pn.state.cache.get("remaining_useful_life_plot")

    # # Get graphs between last three months and next six months
    # update_app_status("Updating Analytics Visualizations...")
    # graphs = [
    #     graph_controller.get_future_month_graph(i) for i in range(-3, 7)
    # ]
    # periods = [(pd.Timestamp(graph_controller.current_date) + pd.DateOffset(months=i)).to_period('M') for i in range(-3, 7)]

    # Get all graphs and periods for better trend analysis
    update_app_status("Updating Analytics Visualizations...")
    graphs = []
    periods = list(graph_controller.prioritized_schedule.keys())
    for period in periods:
        graph = graph_controller.prioritized_schedule[period].get('graph')
        graphs.append(graph)

    fig = get_remaining_useful_life_fig(current_date_graph)
    remaining_useful_life_plot.object = fig

    risk_distribution_plot = pn.state.cache.get("risk_distribution_plot")

    fig = get_risk_distribution_fig(current_date_graph)
    risk_distribution_plot.object = fig

    equipment_condition_trends_plot = pn.state.cache.get("equipment_condition_trends_plot")
    fig = get_equipment_conditions_fig(graphs, periods, current_date=graph_controller.current_date)
    equipment_condition_trends_plot.object = fig

    maintenance_costs_plot = pn.state.cache.get("maintenance_costs_plot")
    fig = get_maintenance_costs_fig(prioritized_schedule=graph_controller.prioritized_schedule, current_date=graph_controller.current_date)
    maintenance_costs_plot.object = fig

    # Update the condition level viewer
    update_app_status("Updating Condition Level Viewer...")
    condition_level_viewer = pn.state.cache["condition_level_viewer"]
    df_condition = graph_controller.get_current_condition_level_df()
    condition_level_viewer.value = df_condition

    update_app_status("Dashboard Update Complete.")

def update_current_date(date, graph_controller: GraphController):
    print(f"Updating current date to {date}")
    graph_controller.current_date = date
    run_simulation(None, graph_controller)

def update_failure_component_details(graph_controller: GraphController, failure_timeline_container):
    component_details_container = pn.state.cache["component_details_container"]

    component_details_container.clear()
    selected_failure = failure_timeline_container.click_data
    if selected_failure:
        component_details_str_list = []
        y = selected_failure.get('points')[0].get('y')
        hover = selected_failure.get('points')[0].get('hovertext')
        component_details_str_list.append(f"### Component Details for {y}")
        component_details_str_list.append(hover)
        component_details_container.append(pn.pane.Markdown("\n\n".join(component_details_str_list)))

def generate_graph(event, graph_controller: GraphController, graph_args, save_graph_file: bool = False):
    """Generate and display a custom graph based on user inputs"""

    graph_controller.generate_new_graph(building_params=graph_args)

    update_system_view_graph_container(graph_controller)
    run_simulation(None, graph_controller)

    # DEBUG: Save the generated graph to a file
    if save_graph_file:
        export_graph(None, graph_controller)

