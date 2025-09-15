import panel as pn
from helpers.panel.button_callbacks import save_settings, import_data, export_data, clear_all_data, run_simulation, update_hours_budget, update_money_budget, update_weeks_to_schedule
from helpers.rul_helper import adjust_rul_parameters, get_current_parameters
from helpers.controllers.graph_controller import GraphController
from helpers.rul_helper import HELP_TEXT_DICT

def layout_settings(settings_container, graph_controller: GraphController, DEFAULT_SIMULATION_PARAMS):
    pn.state.cache["settings_container"] = settings_container

    settings_header = pn.Row(
        pn.Column(
            pn.pane.Markdown("## ⚙ Application Settings", sizing_mode="stretch_width"),
            pn.pane.Markdown("Configure system preferences and thresholds.  Changing Settings will trigger a simulation update.", sizing_mode="stretch_width")
        ),
    )
    settings_container.append(settings_header)

    settings_row = pn.Row()

    left_column = pn.Column()
    right_column = pn.Column()

    settings_row.append(left_column)
    settings_row.append(right_column)

    settings_container.append(settings_row)

    budget_hours_input = pn.widgets.NumberInput(name="Monthly Budget (Hours)", value=DEFAULT_SIMULATION_PARAMS["budget_hours"], step=1)
    # budget_hours_input.param.watch(lambda event: update_hours_budget(event, graph_controller), "value")
    graph_controller.update_hours_budget(DEFAULT_SIMULATION_PARAMS["budget_hours"])

    budget_money_input = pn.widgets.NumberInput(name="Monthly Budget (Dollars)", value=DEFAULT_SIMULATION_PARAMS["budget_money"], step=100)
    # budget_money_input.param.watch(lambda event: update_money_budget(event, graph_controller), "value")
    graph_controller.update_money_budget(DEFAULT_SIMULATION_PARAMS["budget_money"])

    num_weeks_to_schedule_input = pn.widgets.NumberInput(name="Weeks to Schedule", value=DEFAULT_SIMULATION_PARAMS["weeks_to_schedule"], step=1)
    # num_weeks_to_schedule_input.param.watch(lambda event: update_weeks_to_schedule(event, graph_controller), "value")
    graph_controller.update_weeks_to_schedule(DEFAULT_SIMULATION_PARAMS["weeks_to_schedule"])

    pn.state.cache["settings_money_budget_input"] = budget_money_input
    pn.state.cache["settings_hours_budget_input"] = budget_hours_input
    pn.state.cache["settings_num_months_input"] = num_weeks_to_schedule_input
    header_money_budget_input = pn.state.cache["header_money_budget_input"]
    header_hours_budget_input = pn.state.cache["header_hours_budget_input"]
    header_num_months_input = pn.state.cache["header_num_months_input"]

    # Bidirectional sync for hours budget input
    _syncing_hours = {"active": False}
    def sync_hours_from_settings(event):
        if not _syncing_hours["active"]:
            _syncing_hours["active"] = True
            header_hours_budget_input.value = event.new
            graph_controller.update_hours_budget(event.new)
            _syncing_hours["active"] = False
    def sync_hours_from_header(event):
        if not _syncing_hours["active"]:
            _syncing_hours["active"] = True
            budget_hours_input.value = event.new
            graph_controller.update_hours_budget(event.new)
            _syncing_hours["active"] = False
    budget_hours_input.param.watch(sync_hours_from_settings, "value")
    header_hours_budget_input.param.watch(sync_hours_from_header, "value")

    # Bidirectional sync for money budget input
    _syncing_money = {"active": False}

    def sync_money_from_settings(event):
        if not _syncing_money["active"]:
            _syncing_money["active"] = True
            header_money_budget_input.value = event.new
            graph_controller.update_money_budget(event.new)
            _syncing_money["active"] = False

    def sync_money_from_header(event):
        if not _syncing_money["active"]:
            _syncing_money["active"] = True
            budget_money_input.value = event.new
            graph_controller.update_money_budget(event.new)
            _syncing_money["active"] = False

    budget_money_input.param.watch(sync_money_from_settings, "value")
    header_money_budget_input.param.watch(sync_money_from_header, "value")

    # Bidirectional sync for num months input
    _syncing_months = {"active": False}
    def sync_months_from_settings(event):
        if not _syncing_months["active"]:
            _syncing_months["active"] = True
            header_num_months_input.value = event.new
            graph_controller.update_weeks_to_schedule(event.new)
            _syncing_months["active"] = False

    def sync_months_from_header(event):
        if not _syncing_months["active"]:
            _syncing_months["active"] = True
            num_weeks_to_schedule_input.value = event.new
            graph_controller.update_weeks_to_schedule(event.new)
            _syncing_months["active"] = False

    num_weeks_to_schedule_input.param.watch(sync_months_from_settings, "value")
    header_num_months_input.param.watch(sync_months_from_header, "value")
    
    maintenance_budget_container = pn.Column(
        pn.pane.Markdown("### Maintenance Budget"),
        budget_hours_input,
        pn.pane.Markdown("*Set the monthly hour budget for maintenance tasks. This limits how many maintenance activities can be performed each month.*"),
        budget_money_input,
        pn.pane.Markdown("*Set the monthly dollar budget for maintenance tasks. This limits the total cost of maintenance activities each month.*"),
        num_weeks_to_schedule_input,
        pn.pane.Markdown("*Set how many weeks past the current date the maintenance scheduler should plan tasks. The simulation will always simulate between the building's construction date and the current date.*"),
    )

    right_column.append(maintenance_budget_container)
    # right_column.append(pn.layout.Divider(sizing_mode="stretch_width"))

    left_column.append(
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
                # Also trigger simulation after parameter update
                run_simulation(None, graph_controller)
            input_widget.param.watch(update_param, 'value')
        elif isinstance(value, dict):
            # For dictionaries, the sub-widgets already have their event handlers set up
            pass
        else:
            input_widget.value = value

        column = pn.Column(
            pn.Row(
                pn.pane.Markdown(f"**{param.replace('_', ' ').title()}:**", width=200),
                input_widget,
            )
        )

        help_text = HELP_TEXT_DICT.get(param)
        if help_text:
            help_pane = pn.pane.Markdown(f"*{param.replace('_', ' ').title()}: {help_text}*")
            column = pn.Column(help_pane, column)

        return column

    for param, value in current_params.items():
        input_widget = create_input_widget(param, value)
        if input_widget:
            left_column.append(input_widget)

    # settings_container.append(pn.layout.Divider(sizing_mode="stretch_width"))

    # settings_container.append(
    #     pn.Column(
    #         pn.pane.Markdown("### System Configuration"),
    #         pn.pane.Markdown("**Automatic Backup**"),
    #         pn.pane.Markdown("Automatically backup system data"),
    #         pn.Row(
    #             pn.widgets.Select(
    #                 name="Backup Frequency",
    #                 options=[
    #                     "Daily",
    #                     "Weekly",
    #                     "Monthly"
    #                 ],
    #                 sizing_mode="stretch_width"
    #             ),
    #             pn.widgets.Select(
    #                 name = "Data Retention Period",
    #                 options=[
    #                     "1 Year",
    #                     "2 Years",
    #                     "3 Years"
    #                 ],
    #                 value="2 Years",
    #                 sizing_mode="stretch_width"
    #             ),
    #         )
    #     )
    # )

    # settings_container.append(pn.layout.Divider(sizing_mode="stretch_width"))

    right_column.append(
        pn.Column(
            pn.pane.Markdown("### Data Management"),
            pn.Row(
                # pn.widgets.Button(name="Import Data", button_type="default", on_click=lambda event: import_data(event, graph_controller), icon="upload", sizing_mode="stretch_width"),
                pn.widgets.Button(name="Export Data", button_type="default", on_click=lambda event: export_data(event, graph_controller), icon="download", sizing_mode="stretch_width")
            ),
            # pn.pane.HTML("<span style='color: red;'><h4>Danger Zone:</h4></span>"),
            # pn.pane.Markdown("These actions cannot be undone. Please be careful."),
            # pn.Row(
            #     pn.widgets.Button(name="Clear All Data", button_type="default", on_click=clear_all_data, icon="trash", sizing_mode="stretch_width"),
            #     pn.pane.Markdown("", sizing_mode="stretch_width")
            # )
        )
    )
