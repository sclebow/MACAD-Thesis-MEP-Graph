import panel as pn

def layout_analytics(analytics_container, graph_controller):
    average_system_health_container = pn.Column(
        pn.pane.Markdown("### Average System Health"),
    )

    analytics_container[0, 0] = average_system_health_container

    critical_equipment_container = pn.Column(
        pn.pane.Markdown("### Critical Equipment"),
    )
    analytics_container[0, 1] = critical_equipment_container

    average_rul_container = pn.Column(
        pn.pane.Markdown("### Average Remaining Useful Life"),
    )
    analytics_container[0, 2] = average_rul_container

    system_reliability_container = pn.Column(
        pn.pane.Markdown("### System Reliability"),
    )
    analytics_container[0, 3] = system_reliability_container

    remaining_useful_life_container = pn.Column(
        pn.pane.Markdown("### Remaining Useful Life"),
        pn.pane.Plotly(sizing_mode="scale_width")
    )
    analytics_container[1:3, 0:2] = remaining_useful_life_container

    risk_distribution_container = pn.Column(
        pn.pane.Markdown("### Risk Distribution"),
        pn.pane.Plotly(sizing_mode="scale_width")
    )
    analytics_container[1:3, 2:] = risk_distribution_container

    equipment_condition_trends_container = pn.Column(
        pn.pane.Markdown("### Equipment Condition Trends"),
        pn.pane.Plotly(sizing_mode="scale_width")
    )
    analytics_container[3:, 0:2] = equipment_condition_trends_container

    maintenance_costs_container = pn.Column(
        pn.pane.Markdown("### Maintenance Costs"),
        pn.pane.Plotly(sizing_mode="scale_width")
    )
    analytics_container[3:, 2:] = maintenance_costs_container
