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

    import scipy.optimize

    # Copy the graph_controller so that we don't modify the other pages' data
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
    elif goal == 'Maximize Condition Levels':
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
    iteration_log = []  # Store all function evaluations

    # Define the budget variable to optimize
    if optimization_value == 'Money':
        budget_label = 'money_budget'
        initial_budget = money_budget
    else:
        budget_label = 'hours_budget'
        initial_budget = hours_budget

    # Define the objective function for scipy.optimize
    def objective(budget):
        # Set the budgets in the graph controller
        if optimization_value == 'Money':
            graph_controller.monthly_budget_money = budget
            graph_controller.monthly_budget_time = hours_budget
        else:
            graph_controller.monthly_budget_money = money_budget
            graph_controller.monthly_budget_time = budget
        graph_controller.months_to_schedule = num_months
        graph_controller.run_rul_simulation(generate_synthetic_maintenance_logs=True)
        metric_value = metric_function()
        # Log every function evaluation
        iteration_log.append({
            "money_budget": graph_controller.monthly_budget_money,
            "hours_budget": graph_controller.monthly_budget_time,
            "num_months": num_months,
            "goal": goal,
            "optimization_value": optimization_value,
            "iteration": len(iteration_log)+1,
            "metric_value": metric_value,
            "relationship": "direct",
        })
        # Live update the viewer with current progress
        budget_goal_seek_viewer.clear()
        # Show baseline + current log
        partial_results = [results[0]] + iteration_log.copy()
        fig = create_visualization(partial_results, len(partial_results))
        budget_goal_seek_viewer.append(pn.pane.Plotly(fig, sizing_mode='stretch_both'))
        # For maximization, return negative metric (since minimize_scalar minimizes)
        return -metric_value if direction == 'maximize' else metric_value

    # Run baseline simulation
    graph_controller.monthly_budget_money = money_budget
    graph_controller.monthly_budget_time = hours_budget
    graph_controller.months_to_schedule = num_months
    graph_controller.run_rul_simulation(generate_synthetic_maintenance_logs=True)
    baseline_metric_value = metric_function()
    results.append({
        "money_budget": money_budget,
        "hours_budget": hours_budget,
        "num_months": num_months,
        "goal": goal,
        "optimization_value": optimization_value,
        "iteration": "baseline",
        "metric_value": baseline_metric_value,
        "relationship": "direct",
    })

    # Define bounds for the budget variable based on the aggressiveness
    bounds = (initial_budget * (1 - aggressiveness), initial_budget * (1 + aggressiveness))
    # Run optimization using scipy.optimize.minimize_scalar
    opt_result = scipy.optimize.minimize_scalar(
        objective,
        bounds=bounds,
        method='bounded',
        options={'xatol': 1e-2, 'maxiter': number_of_iterations},
    )

    # Run simulation at optimal budget and collect results
    optimal_budget = opt_result.x
    if optimization_value == 'Money':
        graph_controller.monthly_budget_money = optimal_budget
        graph_controller.monthly_budget_time = hours_budget
    else:
        graph_controller.monthly_budget_money = money_budget
        graph_controller.monthly_budget_time = optimal_budget
    graph_controller.months_to_schedule = num_months
    graph_controller.run_rul_simulation(generate_synthetic_maintenance_logs=True)
    optimal_metric_value = metric_function()

    results.append({
        "money_budget": graph_controller.monthly_budget_money,
        "hours_budget": graph_controller.monthly_budget_time,
        "num_months": num_months,
        "goal": goal,
        "optimization_value": optimization_value,
        "iteration": "optimal",
        "metric_value": optimal_metric_value,
        "relationship": "direct",
    })

    # Display results in the viewer
    budget_goal_seek_viewer.clear()
    # Visualize all iterations from scipy.optimize
    all_results = [results[0]] + iteration_log + [results[1]]
    fig = create_visualization(all_results, len(all_results))
    budget_goal_seek_viewer.append(pn.pane.Plotly(fig, sizing_mode='stretch_both'))
    results_df = pd.DataFrame(all_results)
    budget_goal_seek_results.value = results_df

    results_markdown = f"""
    ## Budget Goal Seeker Results

    **Optimization complete:** Best {goal} achieved: {optimal_metric_value:.2f} with a {optimization_value} budget of {optimal_budget:.2f}.

    **Bounds used for optimization:** {bounds[0]:.2f} to {bounds[1]:.2f}
    """

    results_pane.object = results_markdown
    return all_results

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

    # Set the legend to the bottom right
    fig.update_layout(legend=dict(x=0.99, y=0.01, xanchor='right', yanchor='bottom'))

    return fig