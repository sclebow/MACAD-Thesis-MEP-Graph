import panel as pn
from helpers.controllers.graph_controller import GraphController
import copy

def run_budget_goal_seeker(money_budget, hours_budget, num_months, goal, optimization_value, graph_controller: GraphController, number_of_iterations=3):
    """
    Run the budget goal seeking optimization.

    Parameters:
        money_budget (float): Monthly money budget.
        hours_budget (float): Monthly hours budget.
        num_months (int): Number of months to schedule.
        goal (str): Optimization goal, e.g., 'Maximize RUL'.
        optimization_value (str): Specific metric or value to optimize within the goal.
        graph_controller (GraphController): The graph controller instance to update.

    Returns:
        str: Markdown-formatted results or status message.
    """
    # Validate inputs
    money_budget = money_budget
    hours_budget = hours_budget
    num_months = num_months
    if num_months <= 0:
        raise ValueError("Number of months must be positive.")
    if money_budget < 0 or hours_budget < 0:
        raise ValueError("Budgets must be non-negative.")
    if not isinstance(goal, str) or not goal:
        raise ValueError("A valid goal must be specified.")

    # Copy the graph_controller so that we don't modify the other pages' data
    # This is a deep copy to ensure all nested structures are copied
    graph_controller = copy.deepcopy(graph_controller)
    print(f"Current graph: {graph_controller.current_graph[0]}")

    # Retrieve the viewer from the cache
    budget_goal_seek_viewer = pn.state.cache.get("budget_goal_seek_viewer")

    # Get the correct metric function based on the goal and the optimization value
    if goal == 'Maximize RUL':
        metric_function = graph_controller.get_average_RUL_of_simulation
        direction = 'maximize'
    elif goal == 'Maximize Condition':
        metric_function = graph_controller.get_average_condition_level_of_simulation
        direction = 'maximize'
    elif goal == 'Minimize Average Budget':
        direction = 'minimize'
        if optimization_value == 'Money':
            metric_function = graph_controller.get_average_money_budget_used
        elif optimization_value == 'Time':
            metric_function = graph_controller.get_average_hours_budget_used
        else:
            raise ValueError(f"Unknown optimization value: {optimization_value}")
    else:
        raise ValueError(f"Unknown goal: {goal}")

    results = {}
    best_metric_value = None
    if direction == 'maximize':
        best_metric_value = float('-inf')
    else:
        best_metric_value = float('inf')

    input_value = money_budget if optimization_value == 'Money' else hours_budget
    trend = 'decreasing'  # 'increasing' or 'decreasing', default to decreasing

    # Run the optimization
    for iteration in range(number_of_iterations):
        print()
        print(f"Iteration {iteration + 1}/{number_of_iterations}")

        # Set the budgets in the graph controller
        graph_controller.monthly_budget_money = money_budget
        graph_controller.monthly_budget_time = hours_budget
        graph_controller.months_to_schedule = num_months

        # Run the simulation
        graph_controller.run_rul_simulation(generate_synthetic_maintenance_logs=True)

        # Evaluate the metric
        metric_value = metric_function()
        print(f"Metric value: {metric_value}")

        simulation_log = {
            "money_budget": money_budget,
            "hours_budget": hours_budget,
            "num_months": num_months,
            "goal": goal,
            "optimization_value": optimization_value,
            "iteration": iteration + 1,
            "metric_value": None,
            "trend": trend
        }

        results[iteration + 1] = simulation_log
    return results