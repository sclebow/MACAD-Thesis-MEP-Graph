import panel as pn
from helpers.panel.button_callbacks import upload_graph_from_file, export_graph, reset_graph, run_simulation, update_node_details, update_graph_container_visualization
from helpers.controllers.graph_controller import GraphController
from helpers.panel.goal_seek import run_budget_goal_seeker

def layout_budget_goal_seeker(budget_goal_seeker_container, graph_controller: GraphController):
    budget_goal_seeker_container.append(pn.pane.Markdown("### Budget Goal Seeker"))

    # Create inputs for budget and goal
    money_budget_input = pn.widgets.FloatInput(name='Budget ($)', value=graph_controller.monthly_budget_money, step=1000)
    hours_budget_input = pn.widgets.FloatInput(name='Hours Budget', value=graph_controller.monthly_budget_time, step=10)
    num_months_input = pn.widgets.IntInput(name='Number of Months to Schedule', value=60, step=1) # Default to 5 years
    goal_input = pn.widgets.RadioButtonGroup(name='Goals', options=['Maximize RUL', 'Maximize Condition Levels', 'Minimize Average Budget'], value='Maximize RUL')
    optimization_value_input = pn.widgets.RadioButtonGroup(name='Optimization Value', options=['Money', 'Time'], value='Money')

    # Arrange inputs in a form layout
    inputs_form = pn.Column(
        money_budget_input,
        hours_budget_input,
        num_months_input,
        goal_input,
        optimization_value_input,
        sizing_mode='stretch_width',
        # max_width=300,
        # margin=(0, 0, 20, 0)
    )

    # Placeholder for results or status
    results_pane = pn.pane.Markdown("Adjust the budgets and goals, then run the optimization.", sizing_mode='stretch_width')

    # Button to trigger the budget goal seeking process
    run_button = pn.widgets.Button(name="Run Budget Goal Seeker", button_type="primary", icon="play")

    # Container for the entire tab content
    content = pn.Column(
        inputs_form,
        run_button,
        results_pane,
        sizing_mode='stretch_width',
        margin=10
    )

    budget_goal_seek_viewer = pn.Column()
    pn.state.cache["budget_goal_seek_viewer"] = budget_goal_seek_viewer

    # Clear any existing content and add the new layout
    budget_goal_seeker_container.clear()
    budget_goal_seeker_container.append(
        pn.Row(
            content, 
            budget_goal_seek_viewer,
            # sizing_mode='stretch_both',
        )
    )
    
    run_button.on_click(lambda event:
        run_budget_goal_seeker(
            money_budget_input.value,
            hours_budget_input.value,
            num_months_input.value,
            goal_input.value,
            optimization_value_input.value,
            graph_controller
        )
    )