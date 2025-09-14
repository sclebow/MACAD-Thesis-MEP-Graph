import panel as pn
from helpers.panel.button_callbacks import upload_graph_from_file, export_graph, reset_graph, run_simulation, update_node_details, update_graph_container_visualization
from helpers.controllers.graph_controller import GraphController
from helpers.panel.goal_seek import run_budget_goal_seeker

def layout_budget_goal_seeker(budget_goal_seeker_container, graph_controller: GraphController):
    budget_goal_seeker_container.append(pn.pane.Markdown("### Budget Goal Seeker"))

    # Create inputs for budget and goal
    money_budget_input = pn.widgets.FloatInput(name='Starting Budget ($)', value=graph_controller.monthly_budget_money, step=1000)
    hours_budget_input = pn.widgets.FloatInput(name='Starting Hours Budget', value=graph_controller.monthly_budget_time, step=10)
    num_months_input = pn.widgets.IntInput(name='Number of Months to Schedule', value=60, step=1) # Default to 5 years
    goal_input = pn.widgets.RadioButtonGroup(name='Goals', options=['Maximize RUL', 'Maximize Condition Levels', 'Minimize Average Budget'], value='Maximize Condition Levels', orientation='vertical', align="center")
    optimization_value_input = pn.widgets.RadioButtonGroup(name='Optimization Value', options=['Money', 'Hours', 'Both'], value='Both', align="center")
    number_of_iterations_input = pn.widgets.IntInput(name='Number of Iterations', value=10, step=1)
    percentage_bounds = pn.widgets.FloatInput(name='Percentage Bounds', value=0.5, step=0.05, start=0.0)

    min_money_bound = max(0.0, (1 - percentage_bounds.value) * money_budget_input.value)
    max_money_bound = (1 + percentage_bounds.value) * money_budget_input.value
    min_hours_bound = max(0.0, (1 - percentage_bounds.value) * hours_budget_input.value)
    max_hours_bound = (1 + percentage_bounds.value) * hours_budget_input.value
    
    bounds_markdown = pn.pane.Markdown(sizing_mode='stretch_width')
    # Update bounds when percentage or budgets change
    def update_bounds(event):
        nonlocal min_money_bound, max_money_bound, min_hours_bound, max_hours_bound
        min_money_bound = max(0.0, (1 - percentage_bounds.value) * money_budget_input.value)
        max_money_bound = (1 + percentage_bounds.value) * money_budget_input.value
        min_hours_bound = max(0.0, (1 - percentage_bounds.value) * hours_budget_input.value)
        max_hours_bound = (1 + percentage_bounds.value) * hours_budget_input.value
        if optimization_value_input.value == 'Money':
            bounds_markdown.object = f"**Money Bounds:** ${min_money_bound:,.2f} - ${max_money_bound:,.2f}"
        elif optimization_value_input.value == 'Hours':
            bounds_markdown.object = f"**Hours Bounds:** {min_hours_bound:,.2f} - {max_hours_bound:,.2f}"
        else:
            bounds_markdown.object = f"**Money Bounds:** ${min_money_bound:,.2f} - ${max_money_bound:,.2f}  \n**Hours Bounds:** {min_hours_bound:,.2f} - {max_hours_bound:,.2f}"

    percentage_bounds.param.watch(update_bounds, 'value')
    money_budget_input.param.watch(update_bounds, 'value')
    hours_budget_input.param.watch(update_bounds, 'value')
    optimization_value_input.param.watch(update_bounds, 'value')

    # Initialize bounds display
    update_bounds(None)

    # Arrange inputs in a form layout
    inputs_form = pn.Column(
        pn.pane.Markdown("### Input Parameters"),
        money_budget_input,
        hours_budget_input,
        num_months_input,
        pn.Row(
            pn.pane.Markdown("Goal Metric:", width=80, align="center"),
            goal_input,
        ),
        pn.Row(
            pn.pane.Markdown("Optimize Budget By:", width=80, align="center"),
            optimization_value_input,
        ),
        number_of_iterations_input,
        percentage_bounds,
        bounds_markdown,
        # sizing_mode='stretch_width',
        max_width=130,
        # margin=(0, 0, 20, 0)
    )

    # Placeholder for results or status
    results_pane = pn.pane.Markdown("Adjust the budgets and goals, then run the optimization.", sizing_mode='stretch_width')
    pn.state.cache["results_pane"] = results_pane

    # Button to trigger the budget goal seeking process
    run_button = pn.widgets.Button(name="Run Budget Goal Seeker", button_type="primary", icon="play")

    # Container for the entire tab content
    content = pn.Column(
        inputs_form,
        run_button,
        results_pane,
        # sizing_mode='stretch_width',
        width=300,
        # margin=10
    )

    budget_goal_seek_viewer = pn.pane.Plotly(
            sizing_mode='stretch_width'
        )
    pn.state.cache["budget_goal_seek_viewer"] = budget_goal_seek_viewer

    # budget_goal_seek_viewer.append(pn.pane.Markdown("### Budget Goal Seeker Results"))

    budget_goal_seek_results = pn.widgets.DataFrame(sizing_mode="stretch_both", disabled=False, show_index=False, auto_edit=False)
    pn.state.cache["budget_goal_seek_results"] = budget_goal_seek_results
 
    # Clear any existing content and add the new layout
    budget_goal_seeker_container.clear()
    budget_goal_seeker_container.append(
        pn.Row(
            content, 
            budget_goal_seek_viewer,
            budget_goal_seek_results,
            sizing_mode='stretch_both',
        )
    )
    
    run_button.on_click(lambda event:
        run_budget_goal_seeker(
            money_budget_input.value,
            hours_budget_input.value,
            num_months_input.value,
            goal_input.value,
            optimization_value_input.value,
            graph_controller,
            number_of_iterations_input.value,
            percentage_bounds.value
        )
    )