import panel as pn
from helpers.panel.button_callbacks import save_settings, import_data, export_data, clear_all_data, run_simulation
from helpers.rul_helper import adjust_rul_parameters, get_current_parameters

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
        pn.pane.Markdown("### RUL Prediction Parameters", sizing_mode="stretch_width")
    )

    current_params = get_current_parameters()

    def create_input_widget(param, value):
        input_widget = None

        if isinstance(value, float):
            input_widget = pn.widgets.FloatInput(
                step=0.01,
                align="center",
            )
        elif isinstance(value, bool):
            input_widget = pn.widgets.Checkbox(
                align="center",
            )
        elif isinstance(value, int):
            input_widget = pn.widgets.IntInput(
                align="center",
            )
        elif isinstance(value, str):
            input_widget = pn.widgets.TextInput(
                align="center",
            )
        elif isinstance(value, dict):
            input_widget = pn.Column()
            # input_widget.append(pn.pane.Markdown(f"**{param.replace('_', ' ').title()}:**"))
            for key, item in value.items():
                sub_widget = create_input_widget(f"{param}.{key}", item)
                if sub_widget:
                    input_widget.append(sub_widget)
        else:
            print(f"WARNING: No input widget created for parameter {param} of type {type(value)}")
            return None

        if not isinstance(value, list) and not isinstance(value, dict):
            input_widget.value = value
            def update_param(event, param_name=param):
                adjust_rul_parameters(**{param_name: event.new})
            input_widget.param.watch(update_param, 'value')
            # TODO: Allow updating of parts of a dictionary
            input_widget.param.watch(lambda event: run_simulation(None, graph_controller), 'value')
        elif isinstance(value, dict):
            # For dictionaries, the sub-widgets already have their event handlers set up
            pass
        else:
            input_widget.value = value

        row = pn.Row(
            pn.pane.Markdown(f"**{param.replace('_', ' ').title()}:**", width=200),
            input_widget,
        )

        return row

    for param, value in current_params.items():
        input_widget = create_input_widget(param, value)
        if input_widget:
            settings_container.append(input_widget)

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
