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
    best_metric_value = None

    input_value = money_budget if optimization_value == 'Money' else hours_budget
    relationship = 'direct'  # Assume direct relationship as default, we will check the relationship as we iterate

    # Run the baseline simulation
    print("Running baseline simulation...")
    graph_controller.monthly_budget_money = money_budget
    graph_controller.monthly_budget_time = hours_budget
    graph_controller.months_to_schedule = num_months
    graph_controller.run_rul_simulation(generate_synthetic_maintenance_logs=True)
    metric_value = metric_function()
    # print(f"Baseline metric value: {baseline_metric_value}")

    # # DEBUG: Hardcode a baseline metric value for testing
    # baseline_metric_value = input_value * -2 # pretend the metric is directly proportional to the

    best_metric_value = metric_value

    results.append({
        "money_budget": money_budget,
        "hours_budget": hours_budget,
        "num_months": num_months,
        "goal": goal,
        "optimization_value": optimization_value,
        "iteration": "baseline",
        "metric_value": metric_value,
        "relationship": relationship,
    })

    # Run the optimization
    for iteration in range(number_of_iterations):
        print()
        print(f"Iteration {iteration + 1}/{number_of_iterations}")

        # Store last iteration's input value and metric value for comparison
        last_input_value = input_value
        last_metric_value = metric_value 

        # Adjust the budget based on the relationship and direction
        if relationship == 'direct':
            if direction == 'maximize':
                input_value *= (1 + aggressiveness) # increase budget to increase metric
                print(f"Increasing budget to increase metric")
            else:  # minimize
                input_value *= (1 - aggressiveness) # decrease budget to decrease metric
                print(f"Decreasing budget to decrease metric")
        else:  # inverse relationship
            if direction == 'maximize':
                input_value *= (1 - aggressiveness) # decrease budget to increase metric
                print(f"Decreasing budget to increase metric (inverse relationship)")
            else:  # minimize
                input_value *= (1 + aggressiveness) # increase budget to decrease metric
                print(f"Increasing budget to decrease metric (inverse relationship)")

        # Ensure budgets are non-negative and update the appropriate budget
        if optimization_value == 'Money':
            money_budget = max(0, input_value)
        else:
            hours_budget = max(0, input_value)

        # Set the budgets in the graph controller
        graph_controller.monthly_budget_money = money_budget
        graph_controller.monthly_budget_time = hours_budget
        graph_controller.months_to_schedule = num_months

        # Run the simulation
        graph_controller.run_rul_simulation(generate_synthetic_maintenance_logs=True)

        # Evaluate the metric
        metric_value = metric_function()
        print(f"Metric value: {metric_value}")

        # # DEBUG: Hardcode a direct relationship for testing
        # metric_value = input_value * -2 # pretend the metric is directly proportional to the budget

        # Update the best metric value and adjust budgets accordingly
        if direction == 'maximize':
            if metric_value > best_metric_value:
                best_metric_value = metric_value # higher is better
        else:  # minimize
            if metric_value < best_metric_value:
                best_metric_value = metric_value # lower is better

        # Determine the relationship based on changes in input and metric
        print(f"Last input value: {last_input_value}, Current input value: {input_value}, Increased: {input_value > last_input_value}")
        print(f"Last metric value: {last_metric_value}, Current metric value: {metric_value}, Increased: {metric_value > last_metric_value}")

        if relationship == 'direct':
            # We expect both to move in the same direction
            if (input_value > last_input_value and metric_value < last_metric_value) or (input_value < last_input_value and metric_value > last_metric_value):
                relationship = 'inverse'
                print("Detected inverse relationship")
            else:
                print("Relationship remains direct")
        else:  # currently inverse
            # We expect them to move in opposite directions
            if (input_value > last_input_value and metric_value > last_metric_value) or (input_value < last_input_value and metric_value < last_metric_value):
                relationship = 'direct'
                print("Detected direct relationship")
            else:
                print("Relationship remains inverse")

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

    if direction == 'maximize':
        # Find the entry with the maximum metric value
        best_entry = max(results, key=lambda x: x['metric_value'])

        # Find the input value that produced the best metric value
        best_input_value = best_entry['money_budget'] if optimization_value == 'Money' else best_entry['hours_budget']
    else:
        # Find the entry with the minimum metric value
        best_entry = min(results, key=lambda x: x['metric_value'])
        # Find the input value that produced the best metric value
        best_input_value = best_entry['money_budget'] if optimization_value == 'Money' else best_entry['hours_budget']

    results_markdown = f"""
    ## Budget Goal Seeker Results

    Optimization complete. Best {goal} achieved: {best_entry['metric_value']:.2f} with a {optimization_value} budget of {best_input_value:.2f}.
    """

    results_pane.object = results_markdown
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