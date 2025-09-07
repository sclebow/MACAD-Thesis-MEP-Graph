import pandas as pd
import panel as pn
import matplotlib.pyplot as plt
import numpy as np

from helpers.panel.button_callbacks import failure_timeline_reset_view, failure_timeline_zoom_in, failure_timeline_zoom_out, export_failure_schedule, export_annual_budget_forecast, reset_lifecycle_analysis_controls, run_lifecycle_analysis_simulation, update_failure_component_details
from helpers.panel.analytics_viz import _create_enhanced_kpi_card

def layout_failure_prediction(failure_prediction_container, graph_controller):
    main_dashboard_container = pn.GridSpec(nrows=8, ncols=4, mode="error")
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
        # sizing_mode="stretch_both"
    )
    pn.state.cache["system_health_container"] = system_health_container
    critical_component_container = pn.Column(
        pn.pane.Markdown("### Critical Component Overview"),
        # sizing_mode="stretch_both"
    )
    pn.state.cache["critical_component_container"] = critical_component_container
    next_12_months_container = pn.Column(
        pn.pane.Markdown("### Next 12 Months Overview"),
        # sizing_mode="stretch_both"
    )
    pn.state.cache["next_12_months_container"] = next_12_months_container
    cost_forecast_container = pn.Column(
        pn.pane.Markdown("### Cost Forecast"),
        # sizing_mode="stretch_both"
    )
    pn.state.cache["cost_forecast_container"] = cost_forecast_container
    failure_timeline_header_markdown = pn.pane.Markdown("### Failure Timeline")
    pn.state.cache["failure_timeline_header_markdown"] = failure_timeline_header_markdown
    task_timeline_container = pn.pane.Plotly(sizing_mode="stretch_width")
    pn.state.cache["task_timeline_container"] = task_timeline_container
    failure_timeline_header = pn.Column(
        pn.Row(
            failure_timeline_header_markdown,
            pn.widgets.Button(name="Reset View", button_type="default", icon="refresh", on_click=failure_timeline_reset_view),
            pn.widgets.Button(button_type="default", icon="zoom-in", on_click=failure_timeline_zoom_in),
            pn.widgets.Button(button_type="default", icon="zoom-out", on_click=failure_timeline_zoom_out),
        ),
        task_timeline_container,
        sizing_mode="stretch_both"
    )
    failure_timeline_container = pn.pane.Plotly(sizing_mode="scale_both")
    pn.state.cache["failure_timeline_container"] = failure_timeline_container
    failure_timeline_container.param.watch(lambda event: update_failure_component_details(graph_controller, failure_timeline_container), 'click_data')
    component_details_container = pn.Column(
        pn.pane.Markdown("### Component Details"),
        sizing_mode="stretch_both"
    )
    pn.state.cache["component_details_container"] = component_details_container

    main_dashboard_container[0:, 0] = pn.Column(
        system_health_container,
        critical_component_container,
        next_12_months_container,
        cost_forecast_container
    )
    main_dashboard_container[0, 1:3] = failure_timeline_header
    main_dashboard_container[1:, 1:] = failure_timeline_container
    main_dashboard_container[0, 3] = component_details_container

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
    failure_schedule_dataframe = pn.widgets.DataFrame(blank_df, sizing_mode="stretch_both")
    pn.state.cache["failure_schedule_dataframe"] = failure_schedule_dataframe
    failure_schedule_container.append(failure_schedule_dataframe)
    
    # Budget Planning Tab #
    year_slider = pn.widgets.IntSlider(name='Year', start=2025, end=2030, value=2025)
    budget_input = pn.widgets.IntInput(name='Budget ($)', value=100000)
    simulate_btn = pn.widgets.Button(name='Simulate', button_type='primary')

    simulation_cache = {}

    def get_simulation(year, budget):
        key = (year, budget)
        if key in simulation_cache:
            return simulation_cache[key]
        # TODO: Replace with your actual simulation logic
        result = run_simulation(year, budget)
        simulation_cache[key] = result
        return result

    def run_simulation(year, budget):
        # Dummy simulation logic; replace with your own
        df = pd.DataFrame({
            'year': [year],
            'replacement': [120000],
            'repair': [80000],
            'savings': [40000],
            'count': [5]
        })
        return {'year_data': df, 'type_data': df, 'cumulative_data': df, 'optimization': {
            'totalReplacementCost': 120000,
            'totalRepairCost': 80000,
            'totalSavings': 40000,
            'criticalTimeframeCount': 2,
            'highCertaintyCount': 3,
            'averageSavingsPerComponent': 8000
        }}

    def kpi_card(label, value):
        return pn.Column(
            pn.pane.Markdown(f"### {label}"),
            pn.pane.Markdown(f"## {value}"),
            sizing_mode="stretch_width"
        )

    def update_kpis():
        sim = get_simulation(year_slider.value, budget_input.value)
        opt = sim['optimization']
        return pn.Row(
            _create_enhanced_kpi_card("Total Replacement", f"${opt['totalReplacementCost']//1000}k", None, "Total Replacement", "k"),
            _create_enhanced_kpi_card("Total Repair", f"${opt['totalRepairCost']//1000}k", None, "Total Repair", "k"),
            _create_enhanced_kpi_card("Potential Savings", f"${opt['totalSavings']//1000}k", None, "Potential Savings", "k"),
            _create_enhanced_kpi_card("Critical (12mo)", f"{opt['criticalTimeframeCount']}", None, "Critical (12mo)", "")
        )

    def annual_budget_chart():
        sim = get_simulation(year_slider.value, budget_input.value)
        df = sim['year_data']
        fig, ax = plt.subplots()
        df.plot.bar(x='year', y=['replacement', 'repair'], ax=ax)
        return pn.pane.Matplotlib(fig, tight=True)

    def cost_distribution_pie():
        sim = get_simulation(year_slider.value, budget_input.value)
        df = sim['type_data']
        fig, ax = plt.subplots()
        df.set_index('year')[['replacement']].plot.pie(ax=ax, subplots=True)
        return pn.pane.Matplotlib(fig, tight=True)

    def cumulative_cost_area():
        sim = get_simulation(year_slider.value, budget_input.value)
        df = sim['cumulative_data']
        fig, ax = plt.subplots()
        df.plot.area(x='year', y=['replacement', 'repair'], ax=ax)
        return pn.pane.Matplotlib(fig, tight=True)

    def recommendations():
        sim = get_simulation(year_slider.value, budget_input.value)
        opt = sim['optimization']
        return pn.Column(
            pn.pane.Markdown("### Optimization Recommendations"),
            pn.pane.Markdown(f"- High Priority: {opt['highCertaintyCount']} components need preventive maintenance."),
            pn.pane.Markdown(f"- Immediate Action: {opt['criticalTimeframeCount']} components require attention within 12 months."),
            pn.pane.Markdown(f"- Cost Savings: Repair-first strategy could save ${opt['totalSavings']//1000}k."),
        )

    def cost_table():
        sim = get_simulation(year_slider.value, budget_input.value)
        df = sim['type_data']
        return pn.widgets.DataFrame(df, width=800)


    budget_grid = pn.GridSpec(ncols=2, nrows=2, sizing_mode='stretch_both')
    budget_grid[0, 0] = pn.bind(annual_budget_chart)
    budget_grid[0, 1] = pn.bind(cost_distribution_pie)
    budget_grid[1, 0] = pn.bind(cumulative_cost_area)
    budget_grid[1, 1] = pn.bind(recommendations)
    
    budget_tab = pn.Column(
        pn.Row(year_slider, budget_input, simulate_btn),
        pn.bind(update_kpis),
        budget_grid,
        pn.bind(cost_table)
    )

    budget_planning_container[0:, 0:] = budget_tab
    
    # Lifecycle Analysis Tab Implementation #
    import numpy as np

    timeframe_input = pn.widgets.IntSlider(name='Timeframe (months)', start=1, end=60, value=12)
    strategy_select = pn.widgets.RadioButtonGroup(name='Maintenance Strategy', options=['Current', 'Preventive', 'Reactive'], button_type='success')
    compare_btn = pn.widgets.Button(name='Compare Scenarios', button_type='primary')

    lifecycle_cache = {}

    def get_lifecycle_sim(timeframe, strategy):
        key = (timeframe, strategy)
        if key in lifecycle_cache:
            return lifecycle_cache[key]
        # TODO: Replace with your actual simulation logic
        result = run_lifecycle_simulation(timeframe, strategy)
        lifecycle_cache[key] = result
        return result

    def run_lifecycle_simulation(timeframe, strategy):
        # Dummy simulation logic; replace with your own
        df = pd.DataFrame({
            'month': list(range(1, timeframe+1)),
            'lifespan': np.linspace(10, 10+timeframe, timeframe),
            'condition': np.linspace(80, 90, timeframe),
            'risk': np.linspace(20, 10, timeframe)
        })
        return {'projection': df, 'kpis': {
            'lifespan_extension': timeframe,
            'condition_improvement': 10,
            'risk_reduction': 10
        }}

    def lifecycle_kpis():
        sim = get_lifecycle_sim(timeframe_input.value, strategy_select.value)
        kpis = sim['kpis']
        return pn.Row(
            _create_enhanced_kpi_card("Lifespan Extension", f"{kpis['lifespan_extension']} mo", None, "Lifespan Extension", "mo"),
            _create_enhanced_kpi_card("Condition Improvement", f"{kpis['condition_improvement']}%", None, "Condition Improvement", "%"),
            _create_enhanced_kpi_card("Risk Reduction", f"{kpis['risk_reduction']}%", None, "Risk Reduction", "%")
        )

    def lifespan_chart():
        sim = get_lifecycle_sim(timeframe_input.value, strategy_select.value)
        df = sim['projection']
        fig, ax = plt.subplots()
        ax.plot(df['month'], df['lifespan'], label='Lifespan')
        ax.set_xlabel('Month')
        ax.set_ylabel('Lifespan')
        ax.legend()
        return pn.pane.Matplotlib(fig, tight=True)

    def condition_chart():
        sim = get_lifecycle_sim(timeframe_input.value, strategy_select.value)
        df = sim['projection']
        fig, ax = plt.subplots()
        ax.plot(df['month'], df['condition'], label='Condition', color='green')
        ax.set_xlabel('Month')
        ax.set_ylabel('Condition')
        ax.legend()
        return pn.pane.Matplotlib(fig, tight=True)

    def risk_chart():
        sim = get_lifecycle_sim(timeframe_input.value, strategy_select.value)
        df = sim['projection']
        fig, ax = plt.subplots()
        ax.plot(df['month'], df['risk'], label='Risk', color='red')
        ax.set_xlabel('Month')
        ax.set_ylabel('Risk')
        ax.legend()
        return pn.pane.Matplotlib(fig, tight=True)

    def scenario_comparison():
        sim_current = get_lifecycle_sim(timeframe_input.value, 'Current')
        sim_preventive = get_lifecycle_sim(timeframe_input.value, 'Preventive')
        df_c = sim_current['projection']
        df_p = sim_preventive['projection']
        fig, ax = plt.subplots()
        ax.plot(df_c['month'], df_c['lifespan'], label='Current')
        ax.plot(df_p['month'], df_p['lifespan'], label='Preventive')
        ax.set_xlabel('Month')
        ax.set_ylabel('Lifespan')
        ax.legend()
        return pn.pane.Matplotlib(fig, tight=True)

    lifecycle_tab = pn.Column(
        pn.Row(timeframe_input, strategy_select, compare_btn),
        pn.bind(lifecycle_kpis),
        pn.Row(
            pn.bind(lifespan_chart),
            pn.bind(condition_chart),
            pn.bind(risk_chart)
        ),
        pn.pane.Markdown("#### Scenario Comparison"),
        pn.bind(scenario_comparison)
    )

    lifecycle_analysis_container[0:, 0:] = lifecycle_tab

"""life_cycle_analysis_selector = pn.widgets.Select(
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
    lifecycle_analysis_container[3:, 2:] = replacement_timing_optimization_container"""
