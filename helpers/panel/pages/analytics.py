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

def layout_analytics(analytics_container, graph_controller):
    analytics_container.append(
        pn.pane.Markdown("## Analytics Dashboard (Compared to Previous Month)")
    )

    grid = pn.GridSpec(nrows=7, ncols=4, mode="error")
    average_system_health_container = pn.Column(sizing_mode="stretch_both")
    pn.state.cache["average_system_health_container"] = average_system_health_container
    grid[0, 0] = average_system_health_container

    critical_equipment_container = pn.Column(sizing_mode="stretch_both")
    pn.state.cache["critical_equipment_container"] = critical_equipment_container
    grid[0, 1] = critical_equipment_container

    average_rul_container = pn.Column(sizing_mode="stretch_both")
    pn.state.cache["average_rul_container"] = average_rul_container
    grid[0, 2] = average_rul_container

    system_reliability_container = pn.Column(sizing_mode="stretch_both")
    pn.state.cache["system_reliability_container"] = system_reliability_container
    grid[0, 3] = system_reliability_container

    remaining_useful_life_plot = pn.pane.Plotly(sizing_mode="stretch_width")
    remaining_useful_life_container = pn.Column(
        remaining_useful_life_plot
    )
    pn.state.cache["remaining_useful_life_container"] = remaining_useful_life_container
    pn.state.cache["remaining_useful_life_plot"] = remaining_useful_life_plot
    grid[1:4, 0:2] = remaining_useful_life_container

    risk_distribution_plot = pn.pane.Plotly(sizing_mode="stretch_width")
    risk_distribution_container = pn.Column(
        risk_distribution_plot
    )
    pn.state.cache["risk_distribution_container"] = risk_distribution_container
    pn.state.cache["risk_distribution_plot"] = risk_distribution_plot
    grid[1:4, 2:] = risk_distribution_container

    equipment_condition_trends_plot = pn.pane.Plotly(sizing_mode="stretch_width")
    equipment_condition_trends_container = pn.Column(
        equipment_condition_trends_plot
    )
    pn.state.cache["equipment_condition_trends_container"] = equipment_condition_trends_container
    pn.state.cache["equipment_condition_trends_plot"] = equipment_condition_trends_plot
    grid[4:, 0:2] = equipment_condition_trends_container

    maintenance_costs_plot = pn.pane.Plotly(sizing_mode="stretch_width")
    maintenance_costs_container = pn.Column(
        maintenance_costs_plot
    )
    pn.state.cache["maintenance_costs_container"] = maintenance_costs_container
    pn.state.cache["maintenance_costs_plot"] = maintenance_costs_plot
    grid[4:, 2:] = maintenance_costs_container

    analytics_container.append(grid)
