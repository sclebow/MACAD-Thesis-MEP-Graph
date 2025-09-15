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

import pandas as pd
import panel as pn
import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
import hashlib
import datetime

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


    # Budget Planning Tab Layout (add scenario parameter controls)
    strategy_select = pn.widgets.RadioButtonGroup(name='Maintenance Strategy', options=['Current', 'Preventive', 'Reactive'], button_type='success')
    # Generate KPI cards for budget planning tab
    kpi_cards_row = update_kpis()

    main_sim_controls_row = pn.Row(
        budget_input,
        horizon_input,
        strategy_select,
        year_range_slider,
        simulate_btn,
        sizing_mode="stretch_width"
    )

    contingency_input = pn.widgets.FloatInput(name='Contingency (%)', value=10.0, step=0.1)
    split_strategy_slider = pn.widgets.FloatSlider(name='Repair vs Replace Preference (%)', start=0, end=100, value=50)
    failure_cost_input = pn.widgets.IntInput(name='Downtime Cost ($/hr)', value=100)
    risk_weight_input = pn.widgets.FloatSlider(name='Risk Weighting (Likelihood vs Consequence)', start=0, end=1, value=0.5)
    outage_depth_input = pn.widgets.IntSlider(name='Outage Propagation Depth (hops)', start=1, end=5, value=2)
    deferment_months_input = pn.widgets.IntSlider(name='Max Months of Deferment', start=0, end=24, value=6)
    deferment_penalty_input = pn.widgets.FloatInput(name='Deferment Penalty Multiplier', value=0.1, step=0.01)
    inflation_input = pn.widgets.FloatInput(name='Annual Inflation/Discount Rate (%)', value=3.0, step=0.1)
    scenario_name_input = pn.widgets.TextInput(name='Scenario Name', placeholder='Enter scenario name...')

    # Only keep one set of scenario controls and one set of manual node overrides in the Scenario Planner accordion
    scenario_planner_accordion = pn.Accordion(
    (
        "Scenario Planner",
        pn.Column(
            # Only one set of scenario controls
            main_sim_controls_row,
            pn.Row(contingency_input, split_strategy_slider),
            pn.Row(failure_cost_input, risk_weight_input, outage_depth_input),
            pn.Row(deferment_months_input, deferment_penalty_input),
            pn.Row(inflation_input, scenario_name_input),
            # Only one set of manual node overrides
            override_ui,
            # Scenario list and comparison
            scenario_list_ui,
            sizing_mode="stretch_width"
        )
    ),
    active=[0],
    sizing_mode="stretch_width"
)

    budget_tab = pn.Column(
        pn.Row(kpi_cards_row, sizing_mode="stretch_width"),
        scenario_planner_accordion,
        pn.Row(
            pn.Column(annual_budget_chart, cost_distribution_pie, sizing_mode="stretch_width"),
            pn.Column(cumulative_cost_area, cost_table, sizing_mode="stretch_width"),
            sizing_mode="stretch_width"
        ),
        pn.Row(recommendations, sizing_mode="stretch_width"),
        sizing_mode="stretch_width"
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

def load_and_validate_data():
    # Load component types
    components = pd.read_csv('tables/component_types.csv')
    print('DEBUG: component_types.csv columns:', list(components.columns))
    print('DEBUG: component_types.csv sample rows:')
    print(components.head())
    # Load maintenance tasks
    tasks = pd.read_csv('tables/example_maintenance_list.csv')
    # Load maintenance logs
    try:
        logs = pd.read_csv('tables/example_maintenance_logs.csv')
    except Exception:
        logs = pd.DataFrame()
    # Validate required fields
    required_component_fields = [
        'criticality', 'replacement_cost', 'repair_factor', 'installation_date',
        'operating_hours', 'expected_lifespan', 'maintenance_frequency', 'risk_score_base', 'propagated_power'
    ]
    missing_fields = [f for f in required_component_fields if f not in components.columns]
    if missing_fields:
        print(f"Warning: Missing fields in component_types.csv: {missing_fields}")
    # Fill missing values or set defaults
    for field in required_component_fields:
        if field in components.columns:
            components[field] = components[field].replace([-1, '', None], np.nan)
            if components[field].isnull().any():
                default = 0 if field != 'criticality' else 1
                components[field] = components[field].fillna(default)
    # Validate maintenance tasks
    required_task_fields = ['task_type', 'recommended_frequency_months', 'money_cost']
    missing_task_fields = [f for f in required_task_fields if f not in tasks.columns]
    if missing_task_fields:
        print(f"Warning: Missing fields in example_maintenance_list.csv: {missing_task_fields}")
    # Fill missing task costs
    if 'money_cost' in tasks.columns:
        tasks['money_cost'] = tasks['money_cost'].replace([-1, '', None], np.nan).fillna(0)
    # Validate logs
    if not logs.empty and 'condition_level' in logs.columns:
        logs['condition_level'] = logs['condition_level'].replace(['', None], np.nan).fillna(1.0)
    return components, tasks, logs

def prepare_simulation_nodes(components, tasks, logs, overrides=None):
    """
    Merge component, task, and log data into a per-node simulation-ready structure.
    Returns a dict of node_id -> node_data.
    Supports manual overrides via the 'overrides' dict: {node_id: {attr: value, ...}}
    """
    nodes = {}
    # Map maintenance tasks by equipment type
    task_map = tasks.groupby('equipment_type').apply(lambda df: df.to_dict('records')).to_dict()
    # Map latest condition from logs
    if not logs.empty and 'equipment_id' in logs.columns:
        latest_log = logs.sort_values('date').groupby('equipment_id').last()['condition_level'].to_dict()
    else:
        latest_log = {}
    for idx, row in components.iterrows():
        node_id = row.get('Identifier', f'node_{idx}')
        node_data = {
            'id': node_id,
            'type': row.get('Type', ''),
            'criticality': float(row.get('criticality', 1)),
            'replacement_cost': float(row.get('replacement_cost', 0)),
            'repair_factor': float(row.get('repair_factor', 0.3)),
            'expected_lifespan': float(row.get('expected_lifespan', 0)),
            'risk_score_base': float(row.get('risk_score_base', 0)),
            # Derived/linked data
            'tasks': task_map.get(row.get('Type', ''), []),
            'condition_level': float(latest_log.get(node_id, 1.0)),
        }
        # Apply manual overrides if present
        if overrides and node_id in overrides:
            for key, value in overrides[node_id].items():
                node_data[key] = value
        # Flag missing critical fields
        for key in ['replacement_cost', 'expected_lifespan', 'criticality']:
            if node_data[key] in [None, 0, '']:
                node_data['data_issue'] = node_data.get('data_issue', []) + [key]
        nodes[node_id] = node_data
    return nodes

def simulate_maintenance(nodes, horizon_months=12, budget_per_month=None, strategy='risk_first'):
    """
    Simulate maintenance, risk, and cost evolution for each node over the time horizon.
    Returns a dict of monthly results per node and overall aggregates.
    """
    monthly_results = {node_id: [] for node_id in nodes}
    for month in range(1, horizon_months + 1):
        for node_id, node in nodes.items():
            # Initialize per-month result
            result = {
                'month': month,
                'action': 'none',
                'RUL': node.get('expected_lifespan', 0),
                'risk': node.get('risk_score_base', 0),
                'cost': 0,
                'condition_level': node.get('condition_level', 1.0),
            }
            # Simple RUL decay (placeholder, replace with rul_helper logic)
            result['RUL'] = max(result['RUL'] - 1, 0)
            # Simple risk calculation (placeholder, replace with node_risk logic)
            result['risk'] = result['risk'] + (1.0 - result['condition_level']) * node.get('criticality', 1)
            # Action selection (placeholder: repair if RUL < 3)
            if result['RUL'] < 3:
                result['action'] = 'repair'
                result['cost'] = node.get('repair_factor', 0.3) * node.get('replacement_cost', 0)
                result['RUL'] = node.get('expected_lifespan', 0)  # Reset RUL after repair
                result['condition_level'] = 1.0
            monthly_results[node_id].append(result)
    # Aggregate results
    aggregates = {
        'total_cost': sum(r['cost'] for node in monthly_results.values() for r in node),
        'actions': sum(1 for node in monthly_results.values() for r in node if r['action'] != 'none'),
    }
    return monthly_results, aggregates

def simulate_maintenance_refined(nodes, horizon_months=12, budget_per_month=1000, strategy='risk_first'):
    """
    Refined simulation: realistic RUL decay, risk calculation, budget constraint, prioritized actions.
    Returns monthly results and aggregates.
    """
    # --- New implementation with all required business rules ---
    from helpers.rul_helper import RULConfig
    premium_factor = 1.3  # For reactive replacement
    deferment_alpha = RULConfig.OVERDUE_IMPACT_MULTIPLIER
    downtime_propagation = 1.2  # Example propagation multiplier

    monthly_results = {node_id: [] for node_id in nodes}
    baseline_risk = {node_id: [] for node_id in nodes}
    plan_risk = {node_id: [] for node_id in nodes}
    for month in range(1, horizon_months + 1):
        candidates = []
        for node_id, node in nodes.items():
            prev_rul = monthly_results[node_id][-1]['RUL'] if monthly_results[node_id] else node.get('expected_lifespan', 0)
            prev_condition = monthly_results[node_id][-1]['condition_level'] if monthly_results[node_id] else node.get('condition_level', 1.0)
            # Baseline risk (no intervention)
            baseline_risk[node_id].append(node.get('risk_score_base', 0) + node.get('criticality', 1) * (1.0 - prev_condition))
            # RUL decay
            rul = max(prev_rul - 1, 0)
            condition = prev_condition
            risk = node.get('risk_score_base', 0) + node.get('criticality', 1) * (1.0 - condition)
            candidates.append({
                'node_id': node_id,
                'rul': rul,
                'risk': risk,
                'criticality': node.get('criticality', 1),
                'replacement_cost': node.get('replacement_cost', 0),
                'repair_factor': node.get('repair_factor', 0.3),
                'condition': condition,
                'downtime_cost': node.get('downtime_cost', 100),
            })
        candidates.sort(key=lambda x: (x['risk'], x['criticality']), reverse=True)
        budget_left = budget_per_month
        for c in candidates:
            action = 'none'
            cost = 0
            rul = c['rul']
            condition = c['condition']
            # If RUL < 3, consider repair/replace/defer
            if rul < 3 and rul > 0:
                repair_cost = c['repair_factor'] * c['replacement_cost']
                replace_cost = c['replacement_cost']
                if budget_left >= repair_cost and repair_cost > 0:
                    action = 'repair'
                    cost = repair_cost
                    rul = nodes[c['node_id']].get('expected_lifespan', 0)
                    condition = 1.0
                elif budget_left >= replace_cost and replace_cost > 0:
                    action = 'replace'
                    cost = replace_cost
                    rul = nodes[c['node_id']].get('expected_lifespan', 0)
                    condition = 1.0
                else:
                    action = 'defer'
                    cost = 0
                    # Deferment penalty: RUL *= (1 - alpha * overdue_factor)
                    overdue_factor = 1  # Could be tracked per node
                    rul = max(rul * (1 - deferment_alpha * overdue_factor), 0)
                    condition = max(condition - 0.1, 0)
            # If RUL <= 0, auto-book failure cost and reactive replacement
            elif rul <= 0:
                action = 'reactive_replace'
                downtime_hours = 8  # Example value
                failure_cost = downtime_hours * c['downtime_cost'] * downtime_propagation
                cost = c['replacement_cost'] * premium_factor + failure_cost
                rul = nodes[c['node_id']].get('expected_lifespan', 0)
                condition = 1.0
            budget_left -= cost
            # Plan risk after action
            plan_risk[c['node_id']].append(c['risk'])
            monthly_results[c['node_id']].append({
                'month': month,
                'action': action,
                'RUL': rul,
                'risk': c['risk'],
                'cost': cost,
                'condition_level': condition,
            })
    # Aggregate results
    aggregates = {
        'total_cost': sum(r['cost'] for node in monthly_results.values() for r in node),
        'actions': sum(1 for node in monthly_results.values() for r in node if r['action'] != 'none'),
        'repairs': sum(1 for node in monthly_results.values() for r in node if r['action'] == 'repair'),
        'replacements': sum(1 for node in monthly_results.values() for r in node if r['action'] == 'replace'),
        'reactive_replacements': sum(1 for node in monthly_results.values() for r in node if r['action'] == 'reactive_replace'),
        'deferrals': sum(1 for node in monthly_results.values() for r in node if r['action'] == 'defer'),
        'risk_reduction': sum(
            sum(baseline_risk[node_id][i] - plan_risk[node_id][i] for i in range(len(baseline_risk[node_id])))
            for node_id in baseline_risk
        ),
    }
    return monthly_results, aggregates

import panel as pn
# Example Panel UI for manual overrides
replacement_cost_input_T01 = pn.widgets.IntInput(name='Replacement Cost (T-01)', value=1000)
criticality_input_T01 = pn.widgets.IntInput(name='Criticality (T-01)', value=5)
repair_factor_input_P01 = pn.widgets.FloatInput(name='Repair Factor (P-01)', value=0.3)
budget_input = pn.widgets.IntInput(name='Budget per Month', value=1000)
horizon_input = pn.widgets.IntSlider(name='Simulation Horizon (Months)', start=1, end=60, value=12)
strategy_select = pn.widgets.Select(name='Strategy', options=['risk_first', 'RUL_first'], value='risk_first')
year_range_slider = pn.widgets.IntRangeSlider(name='Year Range', start=2025, end=2035, value=(2025, 2030))

def run_simulation_with_overrides(event=None):
    overrides = {
        'T-01': {
            'replacement_cost': replacement_cost_input_T01.value,
            'criticality': criticality_input_T01.value
        },
        'P-01': {
            'repair_factor': repair_factor_input_P01.value
        }
    }
    components, tasks, logs = load_and_validate_data()
    nodes = prepare_simulation_nodes(components, tasks, logs, overrides=overrides)
    monthly_results, aggregates = simulate_maintenance_refined(nodes, horizon_months=15, budget_per_month=1000)
    print('Simulation complete. Aggregates:', aggregates)
    # Optionally update UI with results here

simulate_button = pn.widgets.Button(name='Simulate with Overrides')
simulate_button.on_click(run_simulation_with_overrides)

override_ui = pn.Column(
    pn.pane.Markdown('### Manual Node Overrides'),
    replacement_cost_input_T01,
    criticality_input_T01,
    repair_factor_input_P01,
    simulate_button
)

# To serve in Panel app: override_ui.servable()

class Scenario:
    def __init__(self, label, inputs, cache_key, monthly_results, yearly_aggregates, timestamp=None):
        self.label = label
        self.inputs = inputs
        self.cache_key = cache_key
        self.monthly_results = monthly_results
        self.yearly_aggregates = yearly_aggregates
        self.timestamp = timestamp or datetime.datetime.now()

scenario_cache = {}

def generate_cache_key(inputs, graph_version):
    key_str = str(inputs) + str(graph_version)
    return hashlib.md5(key_str.encode()).hexdigest()

def run_scenario(label, inputs, graph_version, run_simulation_func):
    cache_key = generate_cache_key(inputs, graph_version)
    if cache_key in scenario_cache:
        print(f"[CACHE] Loaded scenario '{label}' from cache.")
        update_scenario_list()
        return scenario_cache[cache_key]
    monthly_results, yearly_aggregates = run_simulation_func(**inputs)
    scenario = Scenario(label, inputs, cache_key, monthly_results, yearly_aggregates)
    scenario_cache[cache_key] = scenario
    print(f"[CACHE] Stored scenario '{label}' in cache.")
    update_scenario_list()
    return scenario

# Scenario List UI
scenario_labels = pn.widgets.Select(name='Saved Scenarios', options=[])
scenario_info = pn.pane.Markdown('Select a scenario to view details.')
scenario_label_input = pn.widgets.TextInput(name='Scenario Label', placeholder='Enter label...')
save_scenario_btn = pn.widgets.Button(name='Save Scenario')
compare_select_1 = pn.widgets.Select(name='Compare Scenario 1', options=[])
compare_select_2 = pn.widgets.Select(name='Compare Scenario 2', options=[])
compare_info = pn.pane.Markdown('Select two scenarios to compare.')

# Save scenario with custom label
def save_scenario(event):
    label = scenario_label_input.value
    if not label:
        scenario_info.object = '**Error:** Please enter a label.'
        return
    inputs = {
        'budget_per_month': budget_input.value,
        'horizon_months': horizon_input.value,
        'strategy': strategy_select.value,
        'year_range': year_range_slider.value,
        'overrides': {
            'T-01': {
                'replacement_cost': replacement_cost_input_T01.value,
                'criticality': criticality_input_T01.value
            }
        }
    }
    graph_version = 'v1'
    def dummy_simulation(**kwargs):
        return {}, {}
    scenario = run_scenario(label, inputs, graph_version, dummy_simulation)
    update_scenario_list()
    update_compare_selects()
    scenario_info.object = f"Scenario '{label}' saved."
save_scenario_btn.on_click(save_scenario)

def update_scenario_list():
    options = [s.label for s in scenario_cache.values()]
    scenario_labels.options = options
    compare_select_1.options = options
    compare_select_2.options = options

# Update compare selects
def update_compare_selects():
    options = [s.label for s in scenario_cache.values()]
    compare_select_1.options = options
    compare_select_2.options = options

# Compare two scenarios
def compare_scenarios(event):
    label1 = compare_select_1.value
    label2 = compare_select_2.value
    s1 = next((s for s in scenario_cache.values() if s.label == label1), None)
    s2 = next((s for s in scenario_cache.values() if s.label == label2), None)
    if not s1 or not s2:
        compare_info.object = '**Error:** Select two valid scenarios.'
        return
    info = f"**A/B Comparison**\n\n**{s1.label}**\nYearly Aggregates: {s1.yearly_aggregates}\n\n**{s2.label}**\nYearly Aggregates: {s2.yearly_aggregates}"
    compare_info.object = info
compare_select_1.param.watch(compare_scenarios, 'value')
compare_select_2.param.watch(compare_scenarios, 'value')

scenario_list_ui = pn.Column(
    pn.pane.Markdown('### Scenario List & Comparison'),
    scenario_labels,
    scenario_info,
    pn.Row(scenario_label_input, save_scenario_btn),
    pn.Row(compare_select_1, compare_select_2),
    compare_info
)
# Call update_compare_selects() after each scenario save
