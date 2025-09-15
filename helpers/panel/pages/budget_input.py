# Copyright (C) 2025  Scott Lebow and Krisztian Hajdu

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Author contact:
# Scott Lebow: scott.lebow@student.iaac.net
# Krisztian Hajdu: krisztian.hajdu@students.iaac.net

import panel as pn
from helpers.panel.button_callbacks import save_settings, import_data, export_data, clear_all_data, run_simulation, update_hours_budget, update_money_budget, update_weeks_to_schedule
from helpers.rul_helper import adjust_rul_parameters, get_current_parameters
from helpers.controllers.graph_controller import GraphController
from helpers.rul_helper import HELP_TEXT_DICT

def layout_budget_input(budget_input_container, graph_controller: GraphController, DEFAULT_SIMULATION_PARAMS):

    budget_hours_input = pn.widgets.NumberInput(name="Monthly Budget (Hours)", value=DEFAULT_SIMULATION_PARAMS["budget_hours"], step=1, width=150)
    budget_hours_input.param.watch(lambda event: update_hours_budget(event, graph_controller), "value")
    graph_controller.update_hours_budget(DEFAULT_SIMULATION_PARAMS["budget_hours"])

    budget_money_input = pn.widgets.NumberInput(name="Monthly Budget (Dollars)", value=DEFAULT_SIMULATION_PARAMS["budget_money"], step=100, width=150)
    budget_money_input.param.watch(lambda event: update_money_budget(event, graph_controller), "value")
    graph_controller.update_money_budget(DEFAULT_SIMULATION_PARAMS["budget_money"])

    num_weeks_to_schedule_input = pn.widgets.NumberInput(name="Weeks to Schedule", value=DEFAULT_SIMULATION_PARAMS["weeks_to_schedule"], step=1, width=150)
    num_weeks_to_schedule_input.param.watch(lambda event: update_weeks_to_schedule(event, graph_controller), "value")
    graph_controller.update_weeks_to_schedule(DEFAULT_SIMULATION_PARAMS["weeks_to_schedule"])

    budget_input_container.append(
        pn.Row(
            budget_hours_input,
            pn.widgets.TooltipIcon(value="Set the monthly hour budget for maintenance tasks. This limits how many maintenance activities can be performed each month."),
            budget_money_input,
            pn.widgets.TooltipIcon(value="Set the monthly dollar budget for maintenance tasks. This limits the total cost of maintenance activities each month."),
            num_weeks_to_schedule_input,
            pn.widgets.TooltipIcon(value="Set how many weeks past the current date the maintenance scheduler should plan tasks. The simulation will always simulate between the building's construction date and the current date."),
        ),
    )

    pn.state.cache["header_money_budget_input"] = budget_money_input
    pn.state.cache["header_hours_budget_input"] = budget_hours_input    
    pn.state.cache["header_num_months_input"] = num_weeks_to_schedule_input