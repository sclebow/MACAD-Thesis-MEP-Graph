import panel as pn

def layout_maintenance(maintenance_container, graph_controller):
    maintenance_logs_container = pn.Column(
        pn.pane.Markdown("### Maintenance Logs"),
        pn.widgets.DataFrame(sizing_mode="stretch_width"),
    )
    maintenance_schedule_container = pn.Column(
        pn.pane.Markdown("### Maintenance Schedule"),
    )
    maintenance_task_list_container = pn.Column(
        pn.pane.Markdown("### Maintenance Task List"),
        pn.widgets.DataFrame(sizing_mode="stretch_width"),
        
    )
    maintenance_tabs = pn.Tabs(
        ("Maintenance Logs", maintenance_logs_container),
        ("Schedule", maintenance_schedule_container),
        ("Task List", maintenance_task_list_container),
        sizing_mode="stretch_width"
    )
    maintenance_container.append(maintenance_tabs)
