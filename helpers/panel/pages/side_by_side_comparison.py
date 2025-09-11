import panel as pn
import pandas as pd
from helpers.controllers.graph_controller import GraphController
import copy
from helpers.panel.analytics_viz import _create_enhanced_kpi_card

def layout_side_by_side_comparison(side_by_side_comparison_container, graph_controller: GraphController):
    side_by_side_comparison_container.append(pn.pane.Markdown("### Side-by-Side Comparison"))

    default_money_budget = graph_controller.monthly_budget_money
    default_time_budget = graph_controller.monthly_budget_time
    default_num_months = graph_controller.months_to_schedule

    num_months_input = pn.widgets.IntInput(
            name="Number of Months to Schedule", 
            value=default_num_months, 
            step=1, 
        )
    generate_synthetic_maintenance_logs_input = pn.widgets.Checkbox(
        name="Generate Synthetic Maintenance Logs",
        value=True,
    )

    simulation_1_container = pn.Column()
    simulation_2_container = pn.Column()

    build_simulation_container(
        simulation_container=simulation_1_container, 
        simulation_number=1,
        default_money_budget=default_money_budget,
        default_time_budget=default_time_budget,
        num_months=num_months_input.value,
    )
    build_simulation_container(
        simulation_container=simulation_2_container, 
        simulation_number=2,
        default_money_budget=default_money_budget,
        default_time_budget=default_time_budget,
        num_months=num_months_input.value,
    )

    side_by_side_comparison_container.append(
        pn.Row(
            pn.Column(
                pn.pane.Markdown("#### Comparison Settings"),
                num_months_input,
                generate_synthetic_maintenance_logs_input,
            ),
            simulation_1_container,
            simulation_2_container,
            # sizing_mode="stretch_width",
        )
    )

    run_rul_simulations_button = pn.widgets.Button(
        name="Run RUL Simulations", 
        button_type="primary", 
        icon="play", 
    )
    def on_run_simulations(event):
        print("\nRunning Side by Side RUL Simulations...")
        simulation_1_graph_controller = copy.deepcopy(graph_controller)
        simulation_2_graph_controller = copy.deepcopy(graph_controller)

        simulation_1_results_container = pn.Column()
        simulation_2_results_container = pn.Column()

        for index, (sim_container, results_container, graph_ctrl) in enumerate([
            (simulation_1_container, simulation_1_results_container, simulation_1_graph_controller),
            (simulation_2_container, simulation_2_results_container, simulation_2_graph_controller),
        ]):
            index += 1  # To make it 1-based index
            money_budget = sim_container[1].value
            time_budget = sim_container[2].value
            num_months = num_months_input.value
            generate_synthetic_maintenance_logs = generate_synthetic_maintenance_logs_input.value

            results_container.clear()
            results_container.append(pn.pane.Markdown(f"#### Simulation {index} Results"))

            run_simulation_with_params(
                event, 
                graph_controller=graph_ctrl, 
                money_budget=money_budget, 
                time_budget=time_budget, 
                num_months=num_months,
                generate_synthetic_maintenance_logs=generate_synthetic_maintenance_logs,
                results_container=results_container,
            )
        side_by_side_comparison_container.append(
            pn.Row(
                simulation_1_results_container,
                simulation_2_results_container,
                # sizing_mode="stretch_width",
            )
        )

    run_rul_simulations_button.on_click(on_run_simulations)
    side_by_side_comparison_container.append(run_rul_simulations_button)

    return side_by_side_comparison_container

def build_simulation_container(simulation_container, simulation_number: int, default_money_budget: float, default_time_budget: int, num_months: int):
    simulation_container.append(pn.pane.Markdown(f"#### Simulation {simulation_number}"))

    money_step = 100.0
    time_step = 1

    default_money_budget += (simulation_number - 1) * money_step * 20 # Offset the default budget for each simulation
    default_time_budget += (simulation_number - 1) * time_step * 20 # Offset the default

    # Add the budget input widgets
    money_budget_input = pn.widgets.FloatInput(name="Money Budget ($)", value=default_money_budget, step=money_step, align="center")
    time_budget_input = pn.widgets.IntInput(name="Time Budget (hours)", value=default_time_budget, step=time_step, align="center")
    simulation_container.append(money_budget_input)
    simulation_container.append(time_budget_input)

def run_simulation_with_params(event, graph_controller: GraphController, money_budget: float, time_budget: int, num_months: int, generate_synthetic_maintenance_logs: bool, results_container: pn.Column):
    print("\nRunning RUL Simulation with Parameters...")
    # Update the number of months to schedule
    graph_controller.months_to_schedule = num_months

    # Update the budgets from the input widgets
    graph_controller.monthly_budget_money = money_budget
    graph_controller.monthly_budget_time = time_budget

    print()
    graph_controller.run_rul_simulation(generate_synthetic_maintenance_logs=generate_synthetic_maintenance_logs)

    current_date_graph = graph_controller.get_current_date_graph()

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
        if graph is None:
            return 0
        return sum(1 for node in graph.nodes(data=True) if node[1].get("risk_level", False))

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
