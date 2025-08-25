# This is a panel python application to view the the maintenance building system graphs, and run simulations.
# We start with just defining the ui and layout
# Actual processes will be stored in separate modules

import panel as pn
import pandas as pd

from helpers.panel.button_callbacks import *

# Create containers for each tab
system_view_container = pn.GridSpec(nrows=5, ncols=3, mode="error")
failure_prediction_container = pn.Column()
maintenance_container = pn.Column()
analytics_container = pn.GridSpec(nrows=5, ncols=4, mode="error")
settings_container = pn.Column()

# Create main tabs page
# Create a stylesheet for the tabs
stylesheet = """
    .bk-tab {
        text-align: left;
    }
"""

# Create main tabs
main_tabs = pn.Tabs(
    ("System View", system_view_container),
    ("Failure Prediction", failure_prediction_container),
    ("Maintenance", maintenance_container),
    ("Analytics", analytics_container),
    ("Settings", settings_container),
    dynamic=True,
    tabs_location="left",
    stylesheets=[stylesheet]
)

# Create main application layout
app = pn.Column(
    pn.pane.Markdown("## MEP Digital Twin\nBuilding Systems Management"),
    main_tabs
)

# Layout the System View
header_row = pn.Row(
    pn.pane.Markdown("### System Network View"),
    pn.widgets.Button(name="Upload Graph", button_type="default", icon="upload", on_click=upload_graph),
    pn.widgets.Button(name="Export Graph", button_type="default", icon="download", on_click=export_graph),
    pn.widgets.Button(name="Reset", button_type="warning", icon="refresh", on_click=reset_graph),
    pn.widgets.Button(name="Run Simulation", button_type="primary", icon="play", on_click=run_simulation),
)

graph_container = pn.pane.Plotly(sizing_mode="scale_width")
equipment_details_container = pn.Column(
    pn.pane.Markdown("### Equipment Details"),
)

system_view_container[0, 0:2 ] = header_row
system_view_container[1:, 0:2 ] = graph_container
system_view_container[:,   2 ] = equipment_details_container

# Layout the Failure Prediction tab
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

# Layout Maintenance Tabs
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

# Layout Analytics
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

# Layout Settings
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

# DEBUG Set default tabs
main_tabs.active = 1

print("Starting Application...")
app.servable()
