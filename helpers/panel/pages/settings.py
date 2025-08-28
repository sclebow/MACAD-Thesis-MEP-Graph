import panel as pn
from helpers.panel.button_callbacks import save_settings, import_data, export_data, clear_all_data

def layout_settings(settings_container, graph_controller):
    settings_header = pn.Row(
        pn.Column(
            pn.pane.Markdown("## ⚙ Application Settings", sizing_mode="stretch_width"),
            pn.pane.Markdown("Configure system preferences and thresholds.", sizing_mode="stretch_width")
        ),
        pn.widgets.Button(name="Save Changes", button_type="primary", on_click=save_settings, align=("center")),
    )
    settings_container.append(settings_header)
    settings_container.append(pn.layout.Divider(sizing_mode="stretch_width"))

    settings_container.append(
        pn.Column(
            pn.pane.Markdown("### Alert Thresholds"),
            pn.Row(
                pn.Column(
                    pn.widgets.IntInput(
                        name="Critical Condition Threshold (%)",
                        value=30,
                        step=1,
                        start=1,
                        end=100,
                        sizing_mode="stretch_width"
                    ),
                    pn.pane.Markdown("Equipment below this condition triggers critical alerts"),
                    pn.widgets.IntInput(
                        name="Low RUL Threshold (months)",
                        value=6,
                        step=1,
                        start=1,
                        end=100,
                        sizing_mode="stretch_width"
                    ),
                    pn.pane.Markdown("Equipment with RUL below this triggers alerts")
                ),
                pn.Column(
                    pn.widgets.IntInput(
                        name="Warning Condition Threshold (%)",
                        value=50,
                        step=1,
                        start=1,
                        end=100,
                        sizing_mode="stretch_width"
                    ),
                    pn.pane.Markdown("Equipment below this condition shows warnings"),
                    pn.widgets.IntInput(
                        name="High Risk Threshold (%)",
                        value=80,
                        step=1,
                        start=1,
                        end=100,
                        sizing_mode="stretch_width"
                    ),
                    pn.pane.Markdown("Equipment below this condition triggers high-risk alerts"),
                )
            )
        )
    )

    settings_container.append(pn.layout.Divider(sizing_mode="stretch_width"))

    settings_container.append(
        pn.Column(
            pn.pane.Markdown("### System Configuration"),
            pn.pane.Markdown("**Automatic Backup**"),
            pn.pane.Markdown("Automatically backup system data"),
            pn.Row(
                pn.widgets.Select(
                    name="Backup Frequency",
                    options=[
                        "Daily",
                        "Weekly",
                        "Monthly"
                    ],
                    sizing_mode="stretch_width"
                ),
                pn.widgets.Select(
                    name = "Data Retention Period",
                    options=[
                        "1 Year",
                        "2 Years",
                        "3 Years"
                    ],
                    value="2 Years",
                    sizing_mode="stretch_width"
                ),
            )
        )
    )

    settings_container.append(pn.layout.Divider(sizing_mode="stretch_width"))

    settings_container.append(
        pn.Column(
            pn.pane.Markdown("### Data Management"),
            pn.Row(
                pn.widgets.Button(name="Import Data", button_type="default", on_click=import_data, icon="upload", sizing_mode="stretch_width"),
                pn.widgets.Button(name="Export Data", button_type="default", on_click=export_data, icon="download", sizing_mode="stretch_width")
            ),
            pn.pane.HTML("<span style='color: red;'><h4>Danger Zone:</h4></span>"),
            pn.pane.Markdown("These actions cannot be undone. Please be careful."),
            pn.Row(
                pn.widgets.Button(name="Clear All Data", button_type="default", on_click=clear_all_data, icon="trash", sizing_mode="stretch_width"),
                pn.pane.Markdown("", sizing_mode="stretch_width")
            )
        )
    )
