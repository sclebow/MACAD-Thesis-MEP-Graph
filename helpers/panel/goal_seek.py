import panel as pn
from helpers.controllers.graph_controller import GraphController
import copy
import plotly.graph_objs as go
import pandas as pd

def run_budget_goal_seeker(money_budget, hours_budget, num_months, goal, optimization_value, graph_controller: GraphController, number_of_iterations=3, aggressiveness=0.1):
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

    # Retrieve the viewer and results widget from the cache
    budget_goal_seek_viewer = pn.state.cache.get("budget_goal_seek_viewer")
    budget_goal_seek_results = pn.state.cache.get("budget_goal_seek_results")
    results_pane = pn.state.cache.get("results_pane")

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

    results = []
    best_metric_value = None
    if direction == 'maximize':
        best_metric_value = float('-inf')
    else:
        best_metric_value = float('inf')

    input_value = money_budget if optimization_value == 'Money' else hours_budget
    relationship = 'direct'  # Assume direct relationship as default, we will check the relationship as we iterate

    # Run the baseline simulation
    print("Running baseline simulation...")
    graph_controller.monthly_budget_money = money_budget
    graph_controller.monthly_budget_time = hours_budget
    graph_controller.months_to_schedule = num_months
    graph_controller.run_rul_simulation(generate_synthetic_maintenance_logs=True)
    baseline_metric_value = metric_function()
    print(f"Baseline metric value: {baseline_metric_value}")

    if direction == 'maximize':
        if baseline_metric_value > best_metric_value:
            best_metric_value = baseline_metric_value
    else:
        if baseline_metric_value < best_metric_value:
            best_metric_value = baseline_metric_value

    # Adjust the budget based on the initial run
    if direction == 'maximize':
        if baseline_metric_value > best_metric_value:
            relationship = 'direct'
        else:
            relationship = 'inverse'
    else:
        if baseline_metric_value < best_metric_value:
            relationship = 'direct'
        else:
            relationship = 'inverse'

    results.append({
        "money_budget": money_budget,
        "hours_budget": hours_budget,
        "num_months": num_months,
        "goal": goal,
        "optimization_value": optimization_value,
        "iteration": "baseline",
        "metric_value": baseline_metric_value,
        "relationship": relationship,
    })

    # Run the optimization
    for iteration in range(number_of_iterations):
        print()
        print(f"Iteration {iteration + 1}/{number_of_iterations}")

        # Adjust the budget based on the relationship and direction
        adjustment = aggressiveness * input_value
        if relationship == 'direct':
            if direction == 'maximize':
                if baseline_metric_value < best_metric_value:
                    adjustment = -adjustment
            else:  # minimize
                if baseline_metric_value > best_metric_value:
                    adjustment = -adjustment
        else:  # inverse relationship
            adjustment = -adjustment

        if optimization_value == 'Money':
            money_budget = max(0, money_budget + adjustment)
        else:
            hours_budget = max(0, hours_budget + adjustment)

        # Set the budgets in the graph controller
        graph_controller.monthly_budget_money = money_budget
        graph_controller.monthly_budget_time = hours_budget
        graph_controller.months_to_schedule = num_months

        # Run the simulation
        graph_controller.run_rul_simulation(generate_synthetic_maintenance_logs=True)

        # Evaluate the metric
        metric_value = metric_function()
        print(f"Metric value: {metric_value}")

        # Update the best metric value and adjust budgets accordingly
        if direction == 'maximize':
            if metric_value > best_metric_value:
                best_metric_value = metric_value
                relationship = 'direct'
            else:
                relationship = 'inverse'
        else:  # minimize
            if metric_value < best_metric_value:
                best_metric_value = metric_value
                relationship = 'direct'
            else:
                relationship = 'inverse'

        print(f"Updated budget - Money: {money_budget}, Hours: {hours_budget}, Relationship: {relationship}")

        simulation_log = {
            "money_budget": money_budget,
            "hours_budget": hours_budget,
            "num_months": num_months,
            "goal": goal,
            "optimization_value": optimization_value,
            "iteration": iteration + 1,
            "metric_value": metric_value,
            "relationship": relationship
        }

        results.append(simulation_log)

        # Display results in the viewer
        budget_goal_seek_viewer.clear()
        # Create and display the visualization
        fig = create_visualization(results, number_of_iterations)
        budget_goal_seek_viewer.append(pn.pane.Plotly(fig, sizing_mode='stretch_both'))
        
        results_df = pd.DataFrame(results)
        budget_goal_seek_results.value = results_df

    results_pane

    return results

def create_visualization(results, number_of_iterations):
    """
    Create a line graph visualization of the budget goal seeking results.

    Parameters:
        results (list): List of dictionaries containing the results from each iteration.

    Returns:
        plotly.graph_objs.Figure: A Plotly figure visualizing the results.
    """
    import plotly.graph_objs as go

    goal = results[0]['goal']
    optimization_value = results[0]['optimization_value']
    iterations = [res['iteration'] for res in results]

    if optimization_value == 'Money':
        budget_values = [res['money_budget'] for res in results]
        budget_label = 'Money Budget ($)'

    else:
        budget_values = [res['hours_budget'] for res in results]
        budget_label = 'Hours Budget'

    metric_values = [res['metric_value'] for res in results]

    if goal == 'Maximize RUL':
        metric_label = 'Average RUL'
    elif goal == 'Maximize Condition Levels':
        metric_label = 'Average Condition Level'
    elif goal == 'Minimize Average Budget':
        metric_label = f'Average {budget_label}'
    else:
        metric_label = 'Metric'

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=iterations,
        y=budget_values,
        mode='lines+markers',
        name=budget_label,
        line=dict(color='blue')
    ))

    fig.add_trace(go.Scatter(
        x=iterations,
        y=metric_values,
        mode='lines+markers',
        name=metric_label,
        line=dict(color='green'),
        yaxis='y2'
    ))

    fig.update_layout(
        title=f"Budget Goal Seeker Results: {goal}",
        xaxis_title="Iteration",
        yaxis=dict(
            title=budget_label,
            side='left',
            showgrid=False,
            zeroline=False
        ),
        yaxis2=dict(
            title=metric_label,
            overlaying='y',
            side='right',
            showgrid=False,
            zeroline=False
        ),
        legend=dict(x=0.01, y=0.99),
        margin=dict(l=50, r=50, t=50, b=50),
        template='plotly_white',
        height=400
    )

    # Set the x-axis step to 1 since the x values are discrete iterations
    fig.update_xaxes(dtick=1)

    # Set the x-axis range to fit all iterations
    fig.update_xaxes(range=[0.5, number_of_iterations + 0.5])

    # Set the height 
    fig.update_layout(height=400)

    return fig