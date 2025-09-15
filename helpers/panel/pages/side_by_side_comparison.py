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

import panel as pn
import pandas as pd
from helpers.controllers.graph_controller import GraphController
import copy
from helpers.panel.analytics_viz import _create_enhanced_kpi_card
from helpers.visualization import get_risk_distribution_fig, get_equipment_conditions_fig, get_maintenance_costs_fig

def layout_side_by_side_comparison(side_by_side_comparison_container, graph_controller: GraphController):
    side_by_side_comparison_container.append(pn.pane.Markdown("### Side-by-Side Comparison"))

    default_money_budget = graph_controller.monthly_budget_money
    default_time_budget = graph_controller.monthly_budget_time
    default_num_months = graph_controller.months_to_schedule

    num_months_input = pn.widgets.IntInput(
            name="Number of Months to Schedule", 
            value=default_num_months, 
            step=1, 
            width=200,
        )
    generate_synthetic_maintenance_logs_input = pn.widgets.Checkbox(
        name="Generate Synthetic Maintenance Logs",
        value=True,
        
    )
    number_of_simulations_input = pn.widgets.IntInput(
        name="Number of Simulations (2-5)",
        value=3,
        step=1,
        start=2,
        end=5,
        width=200,
    )
    container_width_input = pn.widgets.IntInput(
        name="Simulation Container Width",
        value=500,
        step=10,
        width=200,
    )
    run_rul_simulations_button = pn.widgets.Button(
        name="Run RUL Simulations", 
        button_type="primary", 
        icon="play", 
    )
    inputs_container = pn.Row(
        pn.Column(
            pn.pane.Markdown("#### Comparison Settings"),
            num_months_input,
            generate_synthetic_maintenance_logs_input,
            number_of_simulations_input,
            container_width_input,
            run_rul_simulations_button
        )
    )
    side_by_side_comparison_container.append(inputs_container)

    simulation_dicts = []
    simulation_inputs_row = pn.Row(sizing_mode="stretch_width")
    inputs_container.append(simulation_inputs_row)
    
    row_container = pn.Row()
    side_by_side_comparison_container.append(row_container)

    def build_simulation_inputs(number_of_simulations):
        simulation_inputs_row.clear()
        simulation_dicts.clear()
        for simulation_number in range(1, number_of_simulations + 1):
            simulation_input_container = pn.Column(
                width=container_width_input.value,
            )

            simulation_dicts.append({
                "input_container": simulation_input_container,
                "money_budget": default_money_budget + (simulation_number - 1) * 100.0 * 20,  # Offset the default budget for each simulation
                "time_budget": default_time_budget + (simulation_number - 1) * 1 * 20,        # Offset the default
                "results_container": pn.Column(),
            })
            build_simulation_container(
                simulation_container=simulation_input_container, 
                simulation_number=simulation_number,
                default_money_budget=default_money_budget + (simulation_number - 1) * 100.0 * 20,
                default_time_budget=default_time_budget + (simulation_number - 1) * 1 * 20,
                num_months=num_months_input.value,
            )
            simulation_inputs_row.append(simulation_input_container)

    number_of_simulations_input.param.watch(lambda event: build_simulation_inputs(event.new), 'value')
    container_width_input.param.watch(lambda event: build_simulation_inputs(number_of_simulations_input.value), 'value')
    build_simulation_inputs(number_of_simulations_input.value)

    def on_run_simulations(event):
        print("\nRunning Side by Side RUL Simulations...")
        row_container.clear()

        for sim in simulation_dicts:
            graph_controller_copy = copy.deepcopy(graph_controller)

            # Set the budgets for this simulation
            graph_controller_copy.monthly_budget_money = sim["money_budget"]
            graph_controller_copy.monthly_budget_time = sim["time_budget"]
            sim["graph_controller"] = graph_controller_copy

            sim["results_container"].clear()
            sim["input_container"].append(sim["results_container"])
            # row_container.append(sim["results_container"])
            run_simulation_with_params(
                graph_controller=sim["graph_controller"],
                money_budget=sim["money_budget"],
                time_budget=sim["time_budget"],
                num_months=num_months_input.value,
                generate_synthetic_maintenance_logs=generate_synthetic_maintenance_logs_input.value,
                results_container=sim["results_container"],
            )


    run_rul_simulations_button.on_click(on_run_simulations)
    
    return side_by_side_comparison_container

def build_simulation_container(simulation_container, simulation_number: int, default_money_budget: float, default_time_budget: int, num_months: int):
    simulation_container.append(pn.pane.Markdown(f"#### Simulation {simulation_number}"))

    money_step = 100.0
    time_step = 1
    # width = 300

    # Add the budget input widgets
    money_budget_input = pn.widgets.FloatInput(
        name="Money Budget ($)", 
        value=default_money_budget, 
        step=money_step, 
        # width=width
    )
    time_budget_input = pn.widgets.IntInput(
        name="Time Budget (hours)", 
        value=default_time_budget, 
        step=time_step, 
        # width=width
    )
    simulation_container.append(money_budget_input)
    simulation_container.append(time_budget_input)

def run_simulation_with_params(graph_controller: GraphController, money_budget: float, time_budget: int, num_months: int, generate_synthetic_maintenance_logs: bool, results_container: pn.Column):
    print("\nRunning RUL Simulation with Parameters...")
    # Update the number of months to schedule
    graph_controller.months_to_schedule = num_months

    # Update the budgets from the input widgets
    graph_controller.monthly_budget_money = money_budget
    graph_controller.monthly_budget_time = time_budget

    print()
    graph_controller.run_rul_simulation(generate_synthetic_maintenance_logs=generate_synthetic_maintenance_logs)
    current_date_graph = graph_controller.get_current_date_graph()

    results_container.append(pn.pane.Markdown("### Budget Summary:"))

    budget_df = graph_controller.get_budget_overview_df()

    # Update the budget markdown summary
    maintenance_budget_markdown_summary_str_list = []
    
    total_money_budget_spent_to_date = budget_df[budget_df['Month'] <= str(graph_controller.current_date.to_period('M'))]['Used Money'].sum()
    maintenance_budget_markdown_summary_str_list.append(f"**Total Money Budget Spent to Date**: ${total_money_budget_spent_to_date:,.2f}")

    total_hours_budget_spent_to_date = budget_df[budget_df['Month'] <= str(graph_controller.current_date.to_period('M'))]['Used Hours'].sum()
    maintenance_budget_markdown_summary_str_list.append(f"**Total Hours Budget Spent to Date**: {total_hours_budget_spent_to_date:,.2f}")

    total_money_budget_full_schedule = budget_df['Used Money'].sum()
    maintenance_budget_markdown_summary_str_list.append(f"**Total Money Budget (Full Schedule)**: ${total_money_budget_full_schedule:,.2f}")

    total_hours_budget_full_schedule = budget_df['Used Hours'].sum()
    maintenance_budget_markdown_summary_str_list.append(f"**Total Hours Budget (Full Schedule)**: {total_hours_budget_full_schedule:,.2f}")

    average_monthly_money_budget = budget_df['Used Money'].mean()
    maintenance_budget_markdown_summary_str_list.append(f"**Average Monthly Money Used (Full Schedule)**: ${average_monthly_money_budget:,.2f}")

    average_monthly_hours_budget = budget_df['Used Hours'].mean()
    maintenance_budget_markdown_summary_str_list.append(f"**Average Monthly Hours Used (Full Schedule)**: {average_monthly_hours_budget:,.2f}")

    maintenance_budget_markdown_summary = pn.pane.Markdown("\n\n".join(maintenance_budget_markdown_summary_str_list))

    results_container.append(maintenance_budget_markdown_summary)

    results_container.append(pn.pane.Markdown("### Full Simulation Graph Visualizations:"))

    # Add the task status bar chart
    fig = graph_controller.get_bar_chart_figure()
    results_container.append(fig)

    # Add the risk level distribution pie chart
    risk_level_pie_chart = get_risk_distribution_fig(current_date_graph)
    results_container.append(risk_level_pie_chart)

    # Add the average remaining useful life graph
    graphs = []
    periods = list(graph_controller.prioritized_schedule.keys())
    for period in periods:
        graph = graph_controller.prioritized_schedule[period].get('graph')
        graphs.append(graph)
    
    average_rul_line_chart = get_equipment_conditions_fig(
        graphs=graphs,
        periods=periods,
        current_date=graph_controller.current_date,
    )
    results_container.append(average_rul_line_chart)

    # Add the monthly budget and time information
    fig = get_maintenance_costs_fig(
        prioritized_schedule=graph_controller.prioritized_schedule,
        current_date=graph_controller.current_date,
    )
    results_container.append(fig)

    results_container.append(pn.pane.Markdown("### Current Date Metrics:"))

    node_conditions = []
    for node_id, attrs in current_date_graph.nodes(data=True):
        if 'current_condition' in attrs:
            node_conditions.append(attrs.get('current_condition'))
    total_number_of_nodes = len(node_conditions)
    average_condition = sum(node_conditions) / total_number_of_nodes if total_number_of_nodes > 0 else 0

    # Get previous month graph
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
    results_container.append(        
        _create_enhanced_kpi_card(
            title="Average System Health",
            value=f"{average_condition:.0%}",
            trend=condition_change,
            metric_type="System Health",
            unit="%"
        )
    )

    def get_number_of_critical_equipment(graph):
        critical_nodes = [n for n, attrs in graph.nodes(data=True) if attrs.get('risk_level') == 'CRITICAL']
        return len(critical_nodes)

    number_of_current_critical_equipment = get_number_of_critical_equipment(current_date_graph)
    number_of_previous_critical_equipment = get_number_of_critical_equipment(previous_month_graph)
    change_in_critical_equipment = number_of_previous_critical_equipment - number_of_current_critical_equipment

    results_container.append(
        _create_enhanced_kpi_card(
            title="Critical Equipment",
            value=str(number_of_current_critical_equipment),
            trend=change_in_critical_equipment,
            metric_type="Critical Equipment",
            unit=""
        )
    )

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

    results_container.append(
        _create_enhanced_kpi_card(
            title="Average RUL (Months)",
            value=f"{current_month_average_rul_months:.1f}",
            trend=change_in_average_rul_months,
            metric_type="Avg. RUL",
            unit="months"
        )
    )

    def get_system_reliability(graph):
        # Calculate system reliability as percentage of non-critical nodes
        total_nodes = graph.number_of_nodes()
        critical_nodes = [n for n, attrs in graph.nodes(data=True) if attrs.get('risk_level') == 'CRITICAL']
        reliability = ((total_nodes - len(critical_nodes)) / total_nodes) if total_nodes else 0.0
        return reliability

    current_month_system_reliability = get_system_reliability(current_date_graph)
    previous_month_system_reliability = get_system_reliability(previous_month_graph)
    change_in_system_reliability = previous_month_system_reliability - current_month_system_reliability

    results_container.append(
        _create_enhanced_kpi_card(
            title="System Reliability",
            value=f"{current_month_system_reliability:.1%}",
            trend=change_in_system_reliability,
            metric_type="System Reliability",
            unit='%'
        )
    )
