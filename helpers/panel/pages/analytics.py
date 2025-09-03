import panel as pn

def layout_analytics(analytics_container, graph_controller):
    analytics_container.append(
        pn.pane.Markdown("## Analytics Dashboard (Compared to Previous Month)")
    )

    grid = pn.GridSpec(nrows=5, ncols=4, mode="error")
    average_system_health_container = pn.Column()
    pn.state.cache["average_system_health_container"] = average_system_health_container
    grid[0, 0] = average_system_health_container

    critical_equipment_container = pn.Column()
    pn.state.cache["critical_equipment_container"] = critical_equipment_container
    grid[0, 1] = critical_equipment_container

    average_rul_container = pn.Column()
    pn.state.cache["average_rul_container"] = average_rul_container
    grid[0, 2] = average_rul_container

    system_reliability_container = pn.Column(
        pn.pane.Markdown("### System Reliability"),
    )
    pn.state.cache["system_reliability_container"] = system_reliability_container
    grid[0, 3] = system_reliability_container

    remaining_useful_life_plot = pn.pane.Plotly(sizing_mode="scale_both")
    remaining_useful_life_container = pn.Column(
        pn.pane.Markdown("### Remaining Useful Life"),
        remaining_useful_life_plot
    )
    pn.state.cache["remaining_useful_life_container"] = remaining_useful_life_container
    pn.state.cache["remaining_useful_life_plot"] = remaining_useful_life_plot
    grid[1:3, 0:2] = remaining_useful_life_container

    risk_distribution_plot = pn.pane.Plotly(sizing_mode="scale_width")
    risk_distribution_container = pn.Column(
        pn.pane.Markdown("### Risk Distribution"),
        risk_distribution_plot
    )
    pn.state.cache["risk_distribution_container"] = risk_distribution_container
    pn.state.cache["risk_distribution_plot"] = risk_distribution_plot
    grid[1:3, 2:] = risk_distribution_container

    equipment_condition_trends_container = pn.Column(
        pn.pane.Markdown("### Equipment Condition Trends"),
        pn.pane.Plotly(sizing_mode="scale_width")
    )
    pn.state.cache["equipment_condition_trends_container"] = equipment_condition_trends_container
    grid[3:, 0:2] = equipment_condition_trends_container

    maintenance_costs_container = pn.Column(
        pn.pane.Markdown("### Maintenance Costs"),
        pn.pane.Plotly(sizing_mode="scale_width")
    )
    pn.state.cache["maintenance_costs_container"] = maintenance_costs_container
    grid[3:, 2:] = maintenance_costs_container

    analytics_container.append(grid)
