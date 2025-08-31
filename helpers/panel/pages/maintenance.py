import panel as pn
from helpers.panel.button_callbacks import maintenance_task_list_upload, update_hours_budget, update_money_budget, update_weeks_to_schedule, replacement_task_list_upload

def layout_maintenance(maintenance_container, graph_controller):
    maintenance_logs_container = pn.Column(
        pn.pane.Markdown("### Maintenance Logs"),
        pn.widgets.DataFrame(sizing_mode="stretch_width"),
    )
    maintenance_schedule_container = pn.Column(
        pn.pane.Markdown("### Maintenance Schedule"),
        sizing_mode="stretch_both"
    )

    maintenance_task_list_viewer = pn.widgets.DataFrame(sizing_mode="stretch_both", disabled=False)

    maintenance_task_list_input = pn.widgets.FileInput(name="Upload Task List")
    maintenance_task_list_input.param.watch(lambda event: maintenance_task_list_upload(event, graph_controller, maintenance_task_list_viewer), "value")

    # Set a default file
    default_maintenance_file_path = "tables/example_maintenance_list.csv"
    default_maintenance_file = open(default_maintenance_file_path, "rb").read()
    maintenance_task_list_input.value = default_maintenance_file

    maintenance_task_list_container = pn.Column(
        pn.pane.Markdown("### Maintenance Task List"),
        maintenance_task_list_input,
        maintenance_task_list_viewer,
    )

    replacement_task_list_viewer = pn.widgets.DataFrame(sizing_mode="stretch_both", disabled=False, auto_edit=False)

    replacement_task_list_input = pn.widgets.FileInput(name="Upload Replacement Task List")
    replacement_task_list_input.param.watch(lambda event: replacement_task_list_upload(event, graph_controller, replacement_task_list_viewer), "value")

    # Set a default file
    default_replacement_file_path = "tables/example_replacement_types.csv"
    default_replacement_file = open(default_replacement_file_path, "rb").read()
    replacement_task_list_input.value = default_replacement_file

    replacement_task_list_container = pn.Column(
        pn.pane.Markdown("### Replacement Task List"),
        replacement_task_list_input,
        replacement_task_list_viewer,
    )


    budget_hours_input = pn.widgets.NumberInput(name="Monthly Budget (Hours)", value=40, step=1)
    budget_hours_input.param.watch(lambda event: update_hours_budget(event, graph_controller), "value")

    budget_money_input = pn.widgets.NumberInput(name="Monthly Budget (Dollars)", value=10000, step=100)
    budget_money_input.param.watch(lambda event: update_money_budget(event, graph_controller), "value")

    num_weeks_to_schedule_input = pn.widgets.NumberInput(name="Weeks to Schedule", value=360, step=1)
    num_weeks_to_schedule_input.param.watch(lambda event: update_weeks_to_schedule(event, graph_controller), "value")

    maintenance_budget_container = pn.Column(
        pn.pane.Markdown("### Maintenance Budget"),
        budget_hours_input,
        budget_money_input,
        num_weeks_to_schedule_input
    )

    maintenance_tabs = pn.Tabs(
        ("Maintenance Logs", maintenance_logs_container),
        ("Schedule", maintenance_schedule_container),
        ("Maintenance Task List", maintenance_task_list_container),
        ("Replacement Task List", replacement_task_list_container),
        ("Budget", maintenance_budget_container),
        sizing_mode="stretch_width"
    )
    maintenance_container.append(maintenance_tabs)

    maintenance_tabs.active = 3 # Set default tab to "Task List" for debugging