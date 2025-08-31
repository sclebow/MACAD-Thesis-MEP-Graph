import panel as pn
from helpers.panel.button_callbacks import task_list_upload, update_hours_budget, update_money_budget

def layout_maintenance(maintenance_container, graph_controller):
    maintenance_logs_container = pn.Column(
        pn.pane.Markdown("### Maintenance Logs"),
        pn.widgets.DataFrame(sizing_mode="stretch_width"),
    )
    maintenance_schedule_container = pn.Column(
        pn.pane.Markdown("### Maintenance Schedule"),
        sizing_mode="stretch_both"
    )
    
    task_list_viewer = pn.widgets.DataFrame(sizing_mode="stretch_both")
    
    task_list_input = pn.widgets.FileInput(name="Upload Task List")
    task_list_input.param.watch(lambda event: task_list_upload(event, graph_controller, task_list_viewer), "value")

    # Set a default file
    default_file_path = "tables/example_maintenance_list.csv"
    default_file = open(default_file_path, "rb").read()
    task_list_input.value = default_file

    maintenance_task_list_container = pn.Column(
        pn.pane.Markdown("### Maintenance Task List"),
        task_list_input,
        task_list_viewer,
    )

    budget_hours_input = pn.widgets.NumberInput(name="Monthly Budget (Hours)", value=40, step=1)
    budget_hours_input.param.watch(lambda event: update_hours_budget(event, graph_controller), "value")

    budget_money_input = pn.widgets.NumberInput(name="Monthly Budget (Dollars)", value=10000, step=100)
    budget_money_input.param.watch(lambda event: update_money_budget(event, graph_controller), "value")

    maintenance_budget_container = pn.Column(
        pn.pane.Markdown("### Maintenance Budget"),
        budget_hours_input,
        budget_money_input
    )

    maintenance_tabs = pn.Tabs(
        ("Maintenance Logs", maintenance_logs_container),
        ("Schedule", maintenance_schedule_container),
        ("Task List", maintenance_task_list_container),
        ("Budget", maintenance_budget_container),
        sizing_mode="stretch_width"
    )
    maintenance_container.append(maintenance_tabs)

    maintenance_tabs.active = 2 # Set default tab to "Task List" for debugging