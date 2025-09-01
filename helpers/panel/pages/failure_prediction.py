import pandas as pd
import panel as pn

from helpers.panel.button_callbacks import failure_timeline_reset_view, failure_timeline_zoom_in, failure_timeline_zoom_out, export_failure_schedule, export_annual_budget_forecast, reset_lifecycle_analysis_controls, run_lifecycle_analysis_simulation

def layout_failure_prediction(failure_prediction_container, graph_controller):
    main_dashboard_container = pn.GridSpec(nrows=5, ncols=4, mode="error")
    failure_schedule_container = pn.Column()
    budget_planning_container = pn.GridSpec(nrows=5, ncols=4, mode="error")
    lifecycle_analysis_container = pn.GridSpec(nrows=5, ncols=4, mode="error")

    failure_tabs = pn.layout.Tabs(
        ("Main Dashboard", main_dashboard_container),
        ("Failure Schedule", failure_schedule_container),
        ("Budget Planning", budget_planning_container),
        ("Lifecycle Analysis", lifecycle_analysis_container),
        sizing_mode="stretch_width",
    )

    failure_prediction_container.append(failure_tabs)

    system_health_container = pn.Column(
        pn.pane.Markdown("### System Health Overview"),
    )
    critical_component_container = pn.Column(
        pn.pane.Markdown("### Critical Component Overview"),
    )
    next_12_months_container = pn.Column(
        pn.pane.Markdown("### Next 12 Months Overview"),
    )
    cost_forecast_container = pn.Column(
        pn.pane.Markdown("### Cost Forecast"),
    )
    failure_timeline_header_markdown = pn.pane.Markdown("### Failure Timeline")
    failure_timeline_header = pn.Row(
        failure_timeline_header_markdown,
        pn.widgets.Button(name="Reset View", button_type="default", icon="refresh", on_click=failure_timeline_reset_view),
        pn.widgets.Button(button_type="default", icon="zoom-in", on_click=failure_timeline_zoom_in),
        pn.widgets.Button(button_type="default", icon="zoom-out", on_click=failure_timeline_zoom_out),
    )
    failure_timeline_container = pn.pane.Plotly(sizing_mode="scale_width")
    pn.state.cache["failure_timeline_container"] = failure_timeline_container
    component_details_container = pn.Column(
        pn.pane.Markdown("### Component Details"),
    )

    main_dashboard_container[0:1, 0] = system_health_container
    main_dashboard_container[1:3, 0] = critical_component_container
    main_dashboard_container[3:4, 0] = next_12_months_container
    main_dashboard_container[4:, 0] = cost_forecast_container
    main_dashboard_container[0, 1:2] = failure_timeline_header
    main_dashboard_container[1:, 1:2] = failure_timeline_container
    main_dashboard_container[:, 3] = component_details_container

    failure_schedule_container.append(
        pn.Row(
            pn.pane.Markdown("### Failure Schedule View"),
            pn.widgets.Button(name="Export CSV", button_type="default", icon="download", on_click=export_failure_schedule),
        )
    )

    search_box = pn.widgets.TextInput(placeholder="Search...", sizing_mode="stretch_width")
    failure_schedule_container.append(search_box)

    df_headers = ["Equipment", "Type", "Failure Date", "Cause", "Certainty", "Cost", "Time Until"]
    blank_df = pd.DataFrame(columns=df_headers)
    failure_schedule_dataframe = pn.widgets.DataFrame(blank_df, sizing_mode="stretch_width")
    failure_schedule_container.append(failure_schedule_dataframe)

    total_replacement_container = pn.Column(
        pn.pane.Markdown("### Total Replacement")
    )
    total_repair_container = pn.Column(
        pn.pane.Markdown("### Total Repair")
    )
    potential_savings_container = pn.Column(
        pn.pane.Markdown("### Potential Savings")
    )
    critical_12_months_container = pn.Column(
        pn.pane.Markdown("### Critical 12 Months")
    )
    annual_budget_forecast_container = pn.Column(
        pn.Row(
            pn.pane.Markdown("### Annual Budget Forecast"),
            pn.widgets.Button(name="Export", button_type="default", icon="download", on_click=export_annual_budget_forecast)
        ),
        pn.pane.Plotly(sizing_mode="scale_width")
    )
    cumulative_cost_analysis_container = pn.Column(
        pn.pane.Markdown("### Cumulative Cost Analysis"),
        pn.pane.Plotly(sizing_mode="scale_width")
    )
    cost_distribution_by_type_container = pn.Column(
        pn.pane.Markdown("### Cost Distribution by Type"),
        pn.pane.Plotly(sizing_mode="scale_width")
    )
    budget_optimization_container = pn.Column(
        pn.pane.Markdown("### Budget Optimization"),
    )

    budget_planning_container[0, 0] = total_replacement_container
    budget_planning_container[0, 1] = total_repair_container
    budget_planning_container[0, 2] = potential_savings_container
    budget_planning_container[0, 3] = critical_12_months_container
    budget_planning_container[1:3, 0:2] = annual_budget_forecast_container
    budget_planning_container[3:, 0:2] = cumulative_cost_analysis_container
    budget_planning_container[1:3, 2:] = cost_distribution_by_type_container
    budget_planning_container[3:, 2:] = budget_optimization_container

    life_cycle_analysis_selector = pn.widgets.Select(
        options=["Option 1", "Option 2", "Option 3"],
        value="Option 1",
        sizing_mode="stretch_width"
    )
    scenario_components = pn.Row(
        pn.Column(
            pn.pane.Markdown("### Scenario A"),
            pn.Row(
                pn.Column(
                    pn.widgets.FloatSlider(name="Maintenance Frequency", start=0, end=100, step=1, value=50, sizing_mode="stretch_width"),
                    pn.widgets.FloatSlider(name="Usage Intensity", start=0, end=100, step=1, value=50, sizing_mode="stretch_width"),
                ),
                pn.Column(
                    pn.widgets.FloatSlider(name="Environment", start=0, end=100, step=1, value=50, sizing_mode="stretch_width"),
                    pn.widgets.FloatSlider(name="Quality Factor", start=0, end=100, step=1, value=50, sizing_mode="stretch_width"),
                )
            )
        ),
        pn.Column(
            pn.pane.Markdown("### Scenario B"),
            pn.Row(
                pn.Column(
                    pn.widgets.FloatSlider(name="Maintenance Frequency", start=0, end=100, step=1, value=50, sizing_mode="stretch_width"),
                    pn.widgets.FloatSlider(name="Usage Intensity", start=0, end=100, step=1, value=50, sizing_mode="stretch_width"),
                ),
                pn.Column(
                    pn.widgets.FloatSlider(name="Environment", start=0, end=100, step=1, value=50, sizing_mode="stretch_width"),
                    pn.widgets.FloatSlider(name="Quality Factor", start=0, end=100, step=1, value=50, sizing_mode="stretch_width"),
                )
            )
        ),
    )
    scenario_accordian = pn.Accordion(
        ("Scenario Comparison", scenario_components),
        sizing_mode="stretch_width"
    )
    lifecycle_analysis_controls_container = pn.Column(
        pn.pane.Markdown("### Lifecycle Analysis Controls"),
        pn.Row(
            life_cycle_analysis_selector,
            pn.widgets.Button(name="Reset", button_type="default", icon="refresh", on_click=reset_lifecycle_analysis_controls),
            pn.widgets.Button(name="Simulate", button_type="default", icon="play", on_click=run_lifecycle_analysis_simulation),
        ),
        scenario_accordian
    )
    lifecycle_analysis_container[0, :] = lifecycle_analysis_controls_container

    equipment_degradation_curve_container = pn.Column(
        pn.pane.Markdown("### Equipment Degradation Curve"),
        pn.pane.Plotly(sizing_mode="scale_width")
    )
    lifecycle_analysis_container[1:3, :2] = equipment_degradation_curve_container

    maintenance_strategy_impact_container = pn.Column(
        pn.pane.Markdown("### Maintenance Strategy Impact"),
        pn.pane.Plotly(sizing_mode="scale_width")
    )
    lifecycle_analysis_container[1:3, 2:] = maintenance_strategy_impact_container

    maintenance_strategy_comparison_container = pn.Column(
        pn.pane.Markdown("### Maintenance Strategy Comparison"),
    )
    lifecycle_analysis_container[3:, :2] = maintenance_strategy_comparison_container

    replacement_timing_optimization_container = pn.Column(
        pn.pane.Markdown("### Replacement Timing Optimization"),
    )
    lifecycle_analysis_container[3:, 2:] = replacement_timing_optimization_container
