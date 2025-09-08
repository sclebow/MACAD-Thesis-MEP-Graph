import pandas as pd
import panel as pn
import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go

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
    task_timeline_container = pn.pane.Plotly(
        sizing_mode="stretch_width"
    )
    pn.state.cache["task_timeline_container"] = task_timeline_container
    failure_timeline_header = pn.Column(
        # failure_timeline_header_markdown,
        task_timeline_container,
        sizing_mode="stretch_both"
    )
    failure_timeline_container = pn.pane.Plotly(
        # sizing_mode="scale_both"
        sizing_mode="stretch_width"
    )
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

    # Multi-year controls
    year_range_slider = pn.widgets.IntRangeSlider(name='Year Range', start=2020, end=2030, value=(2025, 2030))
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
        # Real data integration: aggregate costs from CSVs
        tasks = pd.read_csv('tables/example_maintenance_list.csv')
        logs = pd.read_csv('tables/example_maintenance_logs.csv')
        # Parse year from logs
        logs['year'] = pd.to_datetime(logs['date']).dt.year
        # Aggregate costs by year
        year_min, year_max = year_range_slider.value
        years = list(range(year_min, year_max + 1))
        year_data = []
        for y in years:
            # For demo, use all tasks for each year (replace with real logic if available)
            replacement_tasks = tasks[tasks['task_type'] == 'replacement']
            repair_tasks = tasks[tasks['task_type'] != 'replacement']
            replacement_cost = replacement_tasks['money_cost'].replace(-1, 0).sum()
            repair_cost = repair_tasks['money_cost'].sum()
            savings = replacement_cost - repair_cost
            count = len(tasks)
            year_data.append({
                'year': y,
                'replacement': replacement_cost,
                'repair': repair_cost,
                'savings': savings,
                'count': count
            })
        df = pd.DataFrame(year_data)
        # Type breakdown (aggregate over selected years)
        type_df = tasks.groupby('equipment_type').agg({
            'money_cost': 'sum',
            'task_type': lambda x: (x == 'replacement').sum()
        }).reset_index().rename(columns={'money_cost': 'replacement'})
        repair_tasks = tasks[tasks['task_type'] != 'replacement']
        type_df['repair'] = repair_tasks.groupby('equipment_type')['money_cost'].sum().reindex(type_df['equipment_type']).fillna(0).values
        type_df['savings'] = type_df['replacement'] - type_df['repair']
        type_df['count'] = tasks.groupby('equipment_type').size().values
        # Cumulative data
        cumulative_df = df.copy()
        cumulative_df['cumulativeReplacement'] = cumulative_df['replacement'].cumsum()
        cumulative_df['cumulativeRepair'] = cumulative_df['repair'].cumsum()
        # Optimization (totals for selected years)
        optimization = {
            'totalReplacementCost': df['replacement'].sum(),
            'totalRepairCost': df['repair'].sum(),
            'totalSavings': df['savings'].sum(),
            'criticalTimeframeCount': 2,  # TODO: derive from logs
            'highCertaintyCount': 3,      # TODO: derive from logs
            'averageSavingsPerComponent': df['savings'].sum() / max(df['count'].sum(), 1)
        }
        return {
            'year_data': df,
            'type_data': type_df,
            'cumulative_data': cumulative_df,
            'optimization': optimization
        }

    def kpi_card(label, value):
        return pn.Column(
            pn.pane.Markdown(f"### {label}"),
            pn.pane.Markdown(f"## {value}"),
            sizing_mode="stretch_width"
        )

    def update_kpis():
        sim = get_simulation(year_range_slider.value, budget_input.value)
        opt = sim['optimization']
        return pn.Row(
            _create_enhanced_kpi_card("Total Replacement", f"${opt['totalReplacementCost']//1000}k", None, "Total Replacement", "k"),
            _create_enhanced_kpi_card("Total Repair", f"${opt['totalRepairCost']//1000}k", None, "Total Repair", "k"),
            _create_enhanced_kpi_card("Potential Savings", f"${opt['totalSavings']//1000}k", None, "Potential Savings", "k"),
            _create_enhanced_kpi_card("Critical (12mo)", f"{opt['criticalTimeframeCount']}", None, "Critical (12mo)", "")
        )

    def annual_budget_chart():
        import plotly.graph_objects as go
        sim = get_simulation(year_range_slider.value, budget_input.value)
        df = sim['year_data']
        fig = go.Figure()
        fig.add_bar(x=df['year'], y=df['replacement'], name='Replacement', marker_color='#ef4444')
        fig.add_bar(x=df['year'], y=df['repair'], name='Repair', marker_color='#22c55e')
        fig.update_layout(barmode='group', title='Annual Budget Forecast', xaxis_title='Year', yaxis_title='Cost ($)')
        return pn.Column(
            pn.pane.Markdown('### Annual Budget Forecast'),
            pn.pane.Plotly(fig, config={'responsive': True})
        )

    def cost_distribution_pie():
        import plotly.graph_objects as go
        sim = get_simulation(year_range_slider.value, budget_input.value)
        df = sim['type_data']
        fig = go.Figure(go.Pie(labels=df['equipment_type'], values=df['replacement'], hole=0.3))
        fig.update_layout(title='Cost Distribution by Type')
        return pn.Column(
            pn.pane.Markdown('### Cost Distribution by Type'),
            pn.pane.Plotly(fig, config={'responsive': True})
        )

    def cumulative_cost_area():
        import plotly.graph_objects as go
        sim = get_simulation(year_range_slider.value, budget_input.value)
        df = sim['cumulative_data']
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['year'], y=df['cumulativeReplacement'], fill='tozeroy', name='Cumulative Replacement', line_color='#ef4444'))
        fig.add_trace(go.Scatter(x=df['year'], y=df['cumulativeRepair'], fill='tozeroy', name='Cumulative Repair', line_color='#22c55e'))
        fig.update_layout(title='Cumulative Cost Analysis', xaxis_title='Year', yaxis_title='Cumulative Cost ($)')
        return pn.Column(
            pn.pane.Markdown('### Cumulative Cost Analysis'),
            pn.pane.Plotly(fig, config={'responsive': True})
        )

    def recommendations():
        sim = get_simulation(year_range_slider.value, budget_input.value)
        opt = sim['optimization']
        return pn.Column(
            pn.pane.Markdown("### Optimization Recommendations"),
            pn.pane.Markdown(f"- High Priority: {opt['highCertaintyCount']} components need preventive maintenance."),
            pn.pane.Markdown(f"- Immediate Action: {opt['criticalTimeframeCount']} components require attention within 12 months."),
            pn.pane.Markdown(f"- Cost Savings: Repair-first strategy could save ${opt['totalSavings']//1000}k."),
        )

    def cost_table():
        sim = get_simulation(year_range_slider.value, budget_input.value)
        df = sim['type_data']
        return pn.Column(
            pn.pane.Markdown('### Cost Summary by System Type'),
            pn.widgets.DataFrame(df, width=800)
        )


    budget_grid = pn.GridSpec(ncols=2, nrows=2, sizing_mode='stretch_both')
    budget_grid[0, 0] = pn.bind(annual_budget_chart)
    budget_grid[0, 1] = pn.bind(cost_distribution_pie)
    budget_grid[1, 0] = pn.bind(cumulative_cost_area)
    budget_grid[1, 1] = pn.bind(recommendations)
    
    budget_tab = pn.Column(
        pn.Row(year_range_slider, budget_input, simulate_btn),
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
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['month'], y=df['lifespan'], mode='lines', name='Lifespan', line_color='#3b82f6'))
        fig.update_layout(title='Lifespan Over Time', xaxis_title='Month', yaxis_title='Lifespan')
        return pn.pane.Plotly(fig, config={'responsive': True})

    def condition_chart():
        sim = get_lifecycle_sim(timeframe_input.value, strategy_select.value)
        df = sim['projection']
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['month'], y=df['condition'], mode='lines', name='Condition', line_color='#22c55e'))
        fig.update_layout(title='Condition Over Time', xaxis_title='Month', yaxis_title='Condition')
        return pn.pane.Plotly(fig, config={'responsive': True})

    def risk_chart():
        sim = get_lifecycle_sim(timeframe_input.value, strategy_select.value)
        df = sim['projection']
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['month'], y=df['risk'], mode='lines', name='Risk', line_color='#ef4444'))
        fig.update_layout(title='Risk Over Time', xaxis_title='Month', yaxis_title='Risk')
        return pn.pane.Plotly(fig, config={'responsive': True})

    def scenario_comparison():
        sim_current = get_lifecycle_sim(timeframe_input.value, 'Current')
        sim_preventive = get_lifecycle_sim(timeframe_input.value, 'Preventive')
        df_c = sim_current['projection']
        df_p = sim_preventive['projection']
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_c['month'], y=df_c['lifespan'], mode='lines', name='Current', line_color='#3b82f6'))
        fig.add_trace(go.Scatter(x=df_p['month'], y=df_p['lifespan'], mode='lines', name='Preventive', line_color='#f59e0b'))
        fig.update_layout(title='Scenario Comparison: Lifespan', xaxis_title='Month', yaxis_title='Lifespan')
        return pn.pane.Plotly(fig, config={'responsive': True})

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
