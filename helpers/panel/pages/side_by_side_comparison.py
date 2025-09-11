import panel as pn
import pandas as pd
from helpers.controllers.graph_controller import GraphController
import copy

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
            sizing_mode="stretch_width",
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

        # Update the number of months to schedule
        simulation_1_graph_controller.months_to_schedule = num_months_input.value
        simulation_2_graph_controller.months_to_schedule = num_months_input.value

        # Update the budgets from the input widgets
        simulation_1_graph_controller.monthly_budget_money = simulation_1_container[1].value
        simulation_1_graph_controller.monthly_budget_time = simulation_1_container[2].value
        simulation_2_graph_controller.monthly_budget_money = simulation_2_container[1].value
        simulation_2_graph_controller.monthly_budget_time = simulation_2_container[2].value

        print()
        simulation_1_graph_controller.run_rul_simulation(generate_synthetic_maintenance_logs=generate_synthetic_maintenance_logs_input.value)
        print()
        simulation_2_graph_controller.run_rul_simulation(generate_synthetic_maintenance_logs=generate_synthetic_maintenance_logs_input.value)

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