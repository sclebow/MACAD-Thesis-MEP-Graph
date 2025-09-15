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
from helpers.panel.button_callbacks import maintenance_task_list_upload, replacement_task_list_upload, maintenance_log_upload

def layout_maintenance(maintenance_container, graph_controller):

    condition_level_viewer = pn.widgets.DataFrame(sizing_mode="stretch_both", disabled=False, auto_edit=False, show_index=False)
    print("Setting condition_level_viewer in cache")
    pn.state.cache["condition_level_viewer"] = condition_level_viewer
    condition_level_container = pn.Column(
        pn.pane.Markdown("### Current Date: Condition Levels of Equipment"),
        condition_level_viewer,
    )

    maintenance_logs_viewer = pn.widgets.DataFrame(sizing_mode="stretch_both", disabled=False, auto_edit=False, show_index=False)
    pn.state.cache["maintenance_logs_viewer"] = maintenance_logs_viewer
    maintenance_logs_container = pn.Column(
        pn.pane.Markdown("### Maintenance Logs"),
        maintenance_logs_viewer
    )

    maintenance_and_condition_grid_container = pn.GridSpec(nrows=1, ncols=2)
    maintenance_and_condition_grid_container[0, 0  ] = condition_level_container
    maintenance_and_condition_grid_container[0, 1: ] = maintenance_logs_container

    maintenance_and_condition_container = pn.Column()
    maintenance_logs_file_input = pn.widgets.FileInput(name="Upload Maintenance Logs")
    maintenance_logs_file_input.param.watch(lambda event: maintenance_log_upload(event, graph_controller), "value")
    
    # Set default values for synthetic logs generation
    pn.state.cache["generate_synthetic_maintenance_logs"] = True

    maintenance_and_condition_container.append(
        pn.Row(
            pn.pane.Markdown("### Upload Maintenance Logs: "),
            maintenance_logs_file_input,
        ),
    )
    maintenance_and_condition_container.append(
        maintenance_and_condition_grid_container
    )

    maintenance_schedule_container = pn.Column(
        pn.pane.Markdown("### Maintenance Schedule"),
        sizing_mode="stretch_both"
    )

    pn.state.cache["maintenance_schedule_container"] = maintenance_schedule_container

    maintenance_task_list_viewer = pn.widgets.DataFrame(sizing_mode="stretch_both", disabled=False, show_index=False, auto_edit=False)

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
        sizing_mode="stretch_both"
    )

    replacement_task_list_viewer = pn.widgets.DataFrame(sizing_mode="stretch_both", disabled=False, auto_edit=False, show_index=False)

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
        sizing_mode="stretch_both"
    )

    maintenance_budget_viewer = pn.widgets.DataFrame(sizing_mode="stretch_both", disabled=False, auto_edit=False, show_index=False)
    pn.state.cache["maintenance_budget_viewer"] = maintenance_budget_viewer

    maintenance_budget_markdown_summary = pn.pane.Markdown()
    pn.state.cache["maintenance_budget_markdown_summary"] = maintenance_budget_markdown_summary
    maintenance_budget_container = pn.Column(
        pn.pane.Markdown("### Used vs. Remaining Budget"),
        maintenance_budget_markdown_summary,
        maintenance_budget_viewer,
        sizing_mode="stretch_both"
    )

    maintenance_tabs = pn.Tabs(
        ("Maintenance Task List", maintenance_task_list_container),
        ("Replacement Task List", replacement_task_list_container),
        ("Budget Summary", maintenance_budget_container),
        ("Maintenance Logs & Condition Levels", maintenance_and_condition_container),
        ("Simulation Schedule", maintenance_schedule_container),
        sizing_mode="stretch_width"
    )
    maintenance_container.append(maintenance_tabs)

    # maintenance_tabs.active = 1 # DEBUG: Set default tab for debugging