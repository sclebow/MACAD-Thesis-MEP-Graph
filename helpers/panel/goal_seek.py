import panel as pn
from helpers.controllers.graph_controller import GraphController
import copy
import plotly.graph_objs as go
import pandas as pd
import scipy.optimize

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
    graph_controller = copy.deepcopy(graph_controller)
    print(f"Current graph: {graph_controller.current_graph[0]}")

    # Retrieve the viewer and results widget from the cache
    budget_goal_seek_viewer = pn.state.cache.get("budget_goal_seek_viewer")
    budget_goal_seek_results = pn.state.cache.get("budget_goal_seek_results")
    results_pane = pn.state.cache.get("results_pane")

    results_markdown = "Running optimization..."
    results_pane.object = results_markdown

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
        elif optimization_value == 'Hours':
            metric_function = graph_controller.get_average_hours_budget_used
        elif optimization_value == 'Both':
            # For 'Both', default to money budget used (could be extended)
            metric_function = graph_controller.get_average_money_budget_used
        else:
            raise ValueError(f"Unknown optimization value: {optimization_value}")
    else:
        raise ValueError(f"Unknown goal: {goal}")

    results = []
    iteration_log = []  # Store all function evaluations

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

    # Handle optimization for 'Both' case
    if optimization_value == 'Both':
        initial_budgets = [money_budget, hours_budget]
        bounds = [
            (money_budget * (1 - aggressiveness), money_budget * (1 + aggressiveness)),
            (hours_budget * (1 - aggressiveness), hours_budget * (1 + aggressiveness))
        ]
        print(f"Starting optimization with initial budgets: {initial_budgets} and bounds: {bounds}")
        def objective(budgets):
            print()
            mb, hb = budgets
            graph_controller.monthly_budget_money = mb
            graph_controller.monthly_budget_time = hb
            graph_controller.months_to_schedule = num_months
            graph_controller.run_rul_simulation(generate_synthetic_maintenance_logs=True)
            metric_value = metric_function()
            iteration_log.append({
                "money_budget": mb,
                "hours_budget": hb,
                "num_months": num_months,
                "goal": goal,
                "optimization_value": optimization_value,
                "iteration": len(iteration_log)+1,
                "metric_value": metric_value,
                "relationship": "direct",
            })
            budget_goal_seek_viewer.clear()
            partial_results = [results[0]] + iteration_log.copy()
            fig = create_visualization(partial_results, number_of_iterations=number_of_iterations, bounds=bounds)
            budget_goal_seek_viewer.append(pn.pane.Plotly(
                fig, 
                # sizing_mode='scale_both'
                ))

            # Update the results widget with current iteration data
            results_df = pd.DataFrame([results[0]] + iteration_log)
            budget_goal_seek_results.value = results_df

            return -metric_value if direction == 'maximize' else metric_value

        opt_result = scipy.optimize.minimize(
            objective,
            initial_budgets,
            bounds=bounds,
            method='Nelder-Mead',
            options={'maxiter': number_of_iterations, 'maxfev': number_of_iterations}
        )
        optimal_money_budget, optimal_hours_budget = opt_result.x
        graph_controller.monthly_budget_money = optimal_money_budget
        graph_controller.monthly_budget_time = optimal_hours_budget
        graph_controller.months_to_schedule = num_months
        graph_controller.run_rul_simulation(generate_synthetic_maintenance_logs=True)
        optimal_metric_value = metric_function()
        results.append({
            "money_budget": optimal_money_budget,
            "hours_budget": optimal_hours_budget,
            "num_months": num_months,
            "goal": goal,
            "optimization_value": optimization_value,
            "iteration": "optimal",
            "metric_value": optimal_metric_value,
            "relationship": "direct",
        })
        budget_goal_seek_viewer.clear()
        all_results = [results[0]] + iteration_log + [results[1]]
        fig = create_visualization(all_results, number_of_iterations=number_of_iterations, bounds=bounds)
        budget_goal_seek_viewer.append(pn.pane.Plotly(fig))
        results_df = pd.DataFrame(all_results)
        budget_goal_seek_results.value = results_df
        results_markdown = f"""
        ## Budget Goal Seeker Results

        **Optimization complete:** Best {goal} achieved: {optimal_metric_value:.2f} with Money budget {optimal_money_budget:.2f} and Hours budget {optimal_hours_budget:.2f}.

        **Bounds used for optimization:**
        Money: {bounds[0][0]:.2f} to {bounds[0][1]:.2f}
        Hours: {bounds[1][0]:.2f} to {bounds[1][1]:.2f}
        """
        results_pane.object = results_markdown
        return all_results

    # Single variable optimization (Money or Hours)
    if optimization_value == 'Money':
        budget_label = 'money_budget'
        initial_budget = money_budget
    else:
        budget_label = 'hours_budget'
        initial_budget = hours_budget

    def objective(budget):
        print()
        if optimization_value == 'Money':
            graph_controller.monthly_budget_money = budget
            graph_controller.monthly_budget_time = hours_budget
        else:
            graph_controller.monthly_budget_money = money_budget
            graph_controller.monthly_budget_time = budget
        graph_controller.months_to_schedule = num_months
        graph_controller.run_rul_simulation(generate_synthetic_maintenance_logs=True)
        metric_value = metric_function()
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
        budget_goal_seek_viewer.clear()
        partial_results = [results[0]] + iteration_log.copy()
        fig = create_visualization(partial_results, number_of_iterations=number_of_iterations, bounds=bounds)
        budget_goal_seek_viewer.append(pn.pane.Plotly(fig, sizing_mode='stretch_both'))
        return -metric_value if direction == 'maximize' else metric_value

    bounds = (initial_budget * (1 - aggressiveness), initial_budget * (1 + aggressiveness))
    opt_result = scipy.optimize.minimize_scalar(
        objective,
        bounds=bounds,
        method='bounded',
        options={'xatol': 1e-2, 'maxiter': number_of_iterations},
    )

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

    budget_goal_seek_viewer.clear()
    all_results = [results[0]] + iteration_log + [results[1]]
    fig = create_visualization(all_results, number_of_iterations=number_of_iterations, bounds=bounds)
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

def create_visualization(results, number_of_iterations, bounds=None):
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

    metric_values = [res['metric_value'] for res in results]

    if goal == 'Maximize RUL':
        metric_label = 'Average RUL'
    elif goal == 'Maximize Condition Levels':
        metric_label = 'Average Condition Level'
    elif goal == 'Minimize Average Budget':
        metric_label = 'Average Budget'
    else:
        metric_label = 'Metric'

    from plotly.subplots import make_subplots

    if optimization_value == 'Both':
        money_budget_values = [res['money_budget'] for res in results]
        hours_budget_values = [res['hours_budget'] for res in results]
        metric_values = [res['metric_value'] for res in results]

        # Create a subplot with three y-axes using layout yaxis, yaxis2, yaxis3
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=iterations,
            y=money_budget_values,
            mode='lines+markers',
            name='Money Budget ($)',
            line=dict(color='blue'),
            yaxis='y1'
        ))
        fig.add_trace(go.Scatter(
            x=iterations,
            y=hours_budget_values,
            mode='lines+markers',
            name='Hours Budget',
            line=dict(color='orange'),
            yaxis='y2'
        ))
        fig.add_trace(go.Scatter(
            x=iterations,
            y=metric_values,
            mode='lines+markers',
            name=metric_label,
            line=dict(color='green'),
            yaxis='y3'
        ))

        # Set axis titles
        yaxis_title = 'Money Budget ($)'
        yaxis2_title = 'Hours Budget'
        yaxis3_title = metric_label

        # Set axis ranges if bounds are provided
        yaxis_range = None
        yaxis2_range = None
        if bounds:
            yaxis_range = [bounds[0][0] * 0.8, bounds[0][1] * 1.2]
            yaxis2_range = [bounds[1][0] * 0.8, bounds[1][1] * 1.2]
            metric_delta = max(metric_values) - min(metric_values)
            yaxis3_range = [min(metric_values) - metric_delta * 0.2, max(metric_values) + metric_delta * 0.1]

        # Get the colors from the traces
        yaxis_color = fig.data[0].line.color
        yaxis2_color = fig.data[1].line.color
        yaxis3_color = fig.data[2].line.color

        fig.update_layout(
            title=f"Budget Goal Seeker Results: {goal}",
            xaxis=dict(title="Iteration", domain=[0.15, 0.95]),
            yaxis=dict(
                title=yaxis_title,
                side='left',
                showgrid=False,
                zeroline=False,
                range=yaxis_range,
                position=0.0,
                tickfont=dict(color=yaxis_color),
                # titlefont=dict(color=yaxis_color),
            ),
            yaxis2=dict(
                title=yaxis2_title,
                side='left',
                overlaying='y',
                showgrid=False,
                zeroline=False,
                range=yaxis2_range,
                position=0.15,
                tickfont=dict(color=yaxis2_color),
                # titlefont=dict(color=yaxis2_color),
            ),
            yaxis3=dict(
                title=yaxis3_title,
                side='right',
                overlaying='y',
                showgrid=False,
                zeroline=False,
                range=yaxis3_range,
                tickfont=dict(color=yaxis3_color),
                # titlefont=dict(color=yaxis3_color),
            ),
        )


    elif optimization_value == 'Money':
        budget_values = [res['money_budget'] for res in results]
        metric_values = [res['metric_value'] for res in results]
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(
            x=iterations,
            y=budget_values,
            mode='lines+markers',
            name='Money Budget ($)',
            line=dict(color='blue')
        ), secondary_y=False)
        fig.add_trace(go.Scatter(
            x=iterations,
            y=metric_values,
            mode='lines+markers',
            name=metric_label,
            line=dict(color='green')
        ), secondary_y=True)
        yaxis_title = 'Money Budget ($)'
        yaxis2_title = metric_label

        if bounds:
            yaxis_range = [bounds[0] * 0.8, bounds[1] * 1.2]
            fig.update_layout(yaxis=dict(range=yaxis_range))
    else:
        budget_values = [res['hours_budget'] for res in results]
        metric_values = [res['metric_value'] for res in results]
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(
            x=iterations,
            y=budget_values,
            mode='lines+markers',
            name='Hours Budget',
            line=dict(color='orange')
        ), secondary_y=False)
        fig.add_trace(go.Scatter(
            x=iterations,
            y=metric_values,
            mode='lines+markers',
            name=metric_label,
            line=dict(color='green')
        ), secondary_y=True)
        yaxis_title = 'Hours Budget'
        yaxis2_title = metric_label

        if bounds:
            yaxis_range = [bounds[0] * 0.8, bounds[1] * 1.2]
            fig.update_layout(yaxis=dict(range=yaxis_range))

    # Layout for all cases
    fig.update_layout(
        title=f"Budget Goal Seeker Results: {goal}",
        xaxis_title="Iteration",
        legend=dict(x=0.99, y=0.01, xanchor='right', yanchor='bottom'),
        hovermode='x unified',
    )

    # Set the x-axis step to 1 since the x values are discrete iterations
    fig.update_xaxes(dtick=1)

    # Set the x-axis range to fit all iterations
    fig.update_xaxes(range=[0.5, number_of_iterations + 0.5])

    # Set height 
    fig.update_layout(height=500)

    return fig