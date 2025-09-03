import panel as pn
import plotly.graph_objects as go
from helpers.visualization import (
    get_remaining_useful_life_fig,
    get_risk_distribution_fig,
    get_equipment_conditions_fig,
    get_maintenance_costs_fig,
)
import pandas as pd

def _create_kpi_cards_section(analytics_container, graph_controller):
    """Create the KPI cards row - System Health, Critical Equipment, Avg RUL, System Reliability"""
    
    # Create KPI cards with mock data initially and proper trend indicators
    system_health_card = _create_kpi_card("System Health", "68%", "↘ -5%", "System Health")
    critical_equipment_card = _create_kpi_card("Critical Equipment", "3", "↗ +1", "Critical Equipment")
    avg_rul_card = _create_kpi_card("Avg. RUL", "18 months", "↘ -2 months", "Avg. RUL")
    system_reliability_card = _create_kpi_card("System Reliability", "87%", "↗ +2%", "System Reliability")
    
    # Store references for real-time updates
    pn.state.cache["analytics_system_health"] = system_health_card
    pn.state.cache["analytics_critical_equipment"] = critical_equipment_card
    pn.state.cache["analytics_avg_rul"] = avg_rul_card
    pn.state.cache["analytics_system_reliability"] = system_reliability_card

def layout_analytics(analytics_container, graph_controller):
    """Create Scott's simplified analytics layout within existing GridSpec"""
    # analytics_container is already a GridSpec, so place items directly
    
    # Store grid reference for our KPI card updates  
    pn.state.cache["analytics_container_ref"] = analytics_container
    
    # Create individual containers for each KPI (Scott's approach)
    average_system_health_container = pn.Column()
    pn.state.cache["average_system_health_container"] = average_system_health_container
    analytics_container[0, 0] = average_system_health_container

    critical_equipment_container = pn.Column()
    pn.state.cache["critical_equipment_container"] = critical_equipment_container
    analytics_container[0, 1] = critical_equipment_container

    average_rul_container = pn.Column()
    pn.state.cache["average_rul_container"] = average_rul_container
    analytics_container[0, 2] = average_rul_container

    system_reliability_container = pn.Column(
        pn.pane.Markdown("### System Reliability"),
    )
    pn.state.cache["system_reliability_container"] = system_reliability_container
    analytics_container[0, 3] = system_reliability_container

    # Charts setup
    remaining_useful_life_plot = pn.pane.Plotly(sizing_mode="scale_both")
    remaining_useful_life_container = pn.Column(
        pn.pane.Markdown("### Remaining Useful Life"),
        remaining_useful_life_plot
    )
    pn.state.cache["remaining_useful_life_container"] = remaining_useful_life_container
    pn.state.cache["remaining_useful_life_plot"] = remaining_useful_life_plot
    analytics_container[1:3, 0:2] = remaining_useful_life_container

    risk_distribution_plot = pn.pane.Plotly(sizing_mode="scale_width")
    risk_distribution_container = pn.Column(
        pn.pane.Markdown("### Risk Distribution"),
        risk_distribution_plot
    )
    pn.state.cache["risk_distribution_container"] = risk_distribution_container
    pn.state.cache["risk_distribution_plot"] = risk_distribution_plot
    analytics_container[1:3, 2:] = risk_distribution_container

    equipment_condition_trends_plot = pn.pane.Plotly(sizing_mode="scale_width")
    equipment_condition_trends_container = pn.Column(
        pn.pane.Markdown("### Equipment Condition Trends"),
        equipment_condition_trends_plot
    )
    pn.state.cache["equipment_condition_trends_container"] = equipment_condition_trends_container
    pn.state.cache["equipment_condition_trends_plot"] = equipment_condition_trends_plot
    analytics_container[3:, 0:2] = equipment_condition_trends_container

    maintenance_costs_plot = pn.pane.Plotly(sizing_mode="scale_width")
    maintenance_costs_container = pn.Column(
        pn.pane.Markdown("### Maintenance Costs"),
        maintenance_costs_plot
    )
    pn.state.cache["maintenance_costs_container"] = maintenance_costs_container
    pn.state.cache["maintenance_costs_plot"] = maintenance_costs_plot
    analytics_container[3:, 2:] = maintenance_costs_container

# Legacy functions removed - now using Scott's approach + unified analytics pipeline

# Chart Generation Functions

def _create_kpi_card(title, value, trend_value, card_type):
    """Helper function to create a standardized KPI card matching Figma design"""
    
    # Determine trend direction and styling
    if trend_value and isinstance(trend_value, str) and trend_value.replace('+', '').replace('-', '').replace('%', '').replace(' months', '').strip().replace('.', '').isdigit():
        is_positive = '+' in trend_value or (trend_value.startswith('↗') or trend_value.startswith('🔺'))
        trend_color = '#22c55e' if is_positive else '#ef4444'
        trend_icon = '↗' if is_positive else '↘'
    else:
        # Default styling for unclear trends
        trend_color = '#6b7280'
        trend_icon = '→'
        if not trend_value:
            trend_value = "0%"
    
    # Ornamental icons for each card type
    ornamental_icons = {
        'System Health': '💚',
        'Critical Equipment': '⚠️', 
        'Avg. RUL': '⏰',
        'System Reliability': '✅'
    }
    ornamental_icon = ornamental_icons.get(card_type, '📊')
    
    # Card border colors
    border_colors = {
        'System Health': '#22c55e',
        'Critical Equipment': '#ef4444',
        'Avg. RUL': '#f59e0b', 
        'System Reliability': '#3b82f6'
    }
    border_color = border_colors.get(card_type, '#e5e7eb')
    
    # Build a card with a thin colored accent on the left, main content in the center,
    # and an ornamental icon on the right. This matches the Figma layout: large value,
    # small title above, compact trend text below, and a vertical color accent.
    accent = pn.pane.HTML(
        "",
        styles={
            'background': border_color,
            'width': '6px',
            'min-width': '6px',
            'border-radius': '6px 0 0 6px',
            'margin-right': '12px',
            'height': '100%'
        },
        sizing_mode='fixed',
        width=6
    )

    content = pn.Column(
        # Title
        pn.pane.HTML(
            f"<div style='margin:0; padding:0; color:#374151; font-size:12px; font-weight:600; line-height:1.05'>{title}</div>",
            styles={'background': 'transparent'}
        ),
        # Main value (large)
        pn.pane.HTML(
            f"<div style='margin:2px 0 0 0; padding:0; color:#111827; font-size:28px; font-weight:800; line-height:1'>{value}</div>",
            styles={'background': 'transparent'}
        ),
        # Trend (small, subtle)
        pn.pane.HTML(
            f"<div style='margin:4px 0 0 0; padding:0; color:{trend_color}; font-size:11px; font-style:normal; line-height:1'>{trend_icon} {trend_value}</div>",
            styles={'background': 'transparent'}
        ),
        sizing_mode='stretch_width',
        styles={
            'overflow': 'hidden'
        }
    )

    icon_pane = pn.pane.HTML(
        f"<div style='display:flex; align-items:center; justify-content:center; height:100%; font-size:22px'>{ornamental_icon}</div>",
        sizing_mode='fixed',
        width=40
    )

    outer_styles = {
        'background': '#ffffff',
        'border': '1px solid #e5e7eb',
        'border-radius': '12px',
        'padding': '10px',
        'min-height': '80px',
        'box-sizing': 'border-box',
        'display': 'flex',
        'align-items': 'center',
        'overflow': 'hidden'
    }

    # Assemble: accent (fixed), content (flex), icon (fixed)
    return pn.Row(
        accent,
        content,
        icon_pane,
        styles=outer_styles,
        sizing_mode='stretch_width',
        margin=(6, 6)
    )

def _create_rul_bar_chart(data=None):
    """Create RUL bar chart with real or mock data"""
    if data and 'top_critical_equipment' in data:
        # Use real data - top 10 critical equipment by RUL
        equipment_data = data['top_critical_equipment'][:10]
        if equipment_data:
            components = [comp['name'] for comp in equipment_data]  # Changed from 'node_id' to 'name'
            rul_months = [comp['rul_months'] for comp in equipment_data]
        else:
            # Fallback if no critical equipment
            components = ['No Critical Equipment']
            rul_months = [0]
    else:
        # Use mock data
        components = ['Main Air Handler', 'Main Panel A', 'Chilled Water Pump', 'Backup Generator', 'Cooling Tower']
        rul_months = [24, 18, 6, 30, 12]
    
    # Color code based on RUL: red < 12, orange < 24, green >= 24
    colors = ['#ef4444' if rul < 12 else '#f59e0b' if rul < 24 else '#22c55e' for rul in rul_months]
    
    fig = go.Figure(data=[
        go.Bar(
            x=components,
            y=rul_months,
            marker_color=colors,
            text=[f'{rul:.1f}' for rul in rul_months],
            textposition='outside'
        )
    ])
    
    fig.update_layout(
        title="",
        xaxis_title="Equipment",
        yaxis_title="Months Remaining",
        showlegend=False,
        margin=dict(l=20, r=20, t=20, b=60),
        height=250
    )
    
    fig.update_xaxes(tickangle=-45)
    
    return fig

def _create_risk_pie_chart(data=None):
    """Create risk distribution pie chart with real or mock data"""
    if data and 'risk_distribution' in data:
        # Use real data
        risk_data = data['risk_distribution']
        labels = [f'{level.title()} Risk' for level in risk_data.keys()]
        values = list(risk_data.values())
    else:
        # Use mock data
        labels = ['Low Risk', 'Medium Risk', 'High Risk']
        values = [60, 25, 15]
    
    # Color mapping for risk levels
    color_map = {
        'Low Risk': '#22c55e',
        'Medium Risk': '#f59e0b', 
        'High Risk': '#ef4444',
        'Critical Risk': '#8e44ad'
    }
    colors = [color_map.get(label, '#6b7280') for label in labels]
    
    fig = go.Figure(data=[
        go.Pie(
            labels=labels,
            values=values,
            marker_colors=colors,
            textinfo='label+percent',
            textposition='outside'
        )
    ])
    
    fig.update_layout(
        title="",
        showlegend=True,
        margin=dict(l=20, r=20, t=20, b=20),
        height=250
    )
    
    return fig

def _create_condition_trends_chart(data=None):
    """Create equipment condition trends line chart with real or mock data"""
    if data and 'equipment_status' in data:
        # Use real data - show current status distribution as a bar chart
        status_data = data['equipment_status']
        categories = list(status_data.keys())
        counts = list(status_data.values())
        
        fig = go.Figure(data=[
            go.Bar(
                x=categories,
                y=counts,
                marker_color=['#22c55e', '#f59e0b', '#ef4444'],
                text=counts,
                textposition='outside'
            )
        ])
        
        fig.update_layout(
            title="",
            xaxis_title="Equipment Status",
            yaxis_title="Count",
            showlegend=False,
            margin=dict(l=20, r=20, t=20, b=20),
            height=250
        )
    else:
        # Use mock trend data
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug']
        hvac = [85, 83, 81, 79, 77, 75, 73, 71]
        electrical = [72, 70, 68, 66, 64, 62, 60, 58]
        plumbing = [65, 62, 58, 55, 52, 48, 45, 42]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=months, y=hvac,
            mode='lines+markers',
            name='HVAC',
            line=dict(color='#22c55e', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=months, y=electrical,
            mode='lines+markers',
            name='Electrical',
            line=dict(color='#f59e0b', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=months, y=plumbing,
            mode='lines+markers',
            name='Plumbing',
            line=dict(color='#ef4444', width=2)
        ))
        
        fig.update_layout(
            title="",
            xaxis_title="Month",
            yaxis_title="Condition %",
            showlegend=True,
            margin=dict(l=20, r=20, t=20, b=20),
            height=250
        )
    
    return fig

def _create_maintenance_costs_chart(data=None):
    """Create maintenance costs chart with real or mock data"""
    if data and 'maintenance_costs' in data:
        # Use real data - show as bar chart of cost breakdown
        cost_data = data['maintenance_costs']
        categories = list(cost_data.keys())
        values = list(cost_data.values())
        
        colors = ['#22c55e', '#ef4444', '#f59e0b', '#3b82f6'][:len(categories)]
        
        fig = go.Figure(data=[
            go.Bar(
                x=categories,
                y=values,
                marker_color=colors,
                text=[f'${v:,.0f}' for v in values],
                textposition='outside'
            )
        ])
        
        fig.update_layout(
            title="",
            xaxis_title="Maintenance Type",
            yaxis_title="Cost ($)",
            showlegend=False,
            margin=dict(l=20, r=20, t=20, b=20),
            height=250
        )
    else:
        # Use mock trend data
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug']
        preventive = [5000, 4500, 5200, 4800, 5100, 4900, 5300, 5000]
        corrective = [2000, 3500, 1800, 4200, 2800, 3200, 2500, 6500]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=months, y=preventive,
            fill='tonexty',
            mode='none',
            name='Preventive',
            fillcolor='rgba(34, 197, 94, 0.6)'
        ))
        
        fig.add_trace(go.Scatter(
            x=months, y=corrective,
            fill='tozeroy',
            mode='none',
            name='Corrective',
            fillcolor='rgba(239, 68, 68, 0.6)'
        ))
        
        fig.update_layout(
            title="",
            xaxis_title="Month",
            yaxis_title="Cost ($)",
            showlegend=True,
            margin=dict(l=20, r=20, t=20, b=20),
            height=250
        )
    
    return fig

def update_analytics_from_simulation(graph_controller):
    """Update analytics displays after simulation runs - now with real data integration"""
    print("Analytics dashboard updated from simulation")
    
    # Update KPI cards with real data
    _update_kpi_cards_with_real_data(graph_controller)
    
    # Update charts with real data
    _update_charts_with_real_data(graph_controller)

# ---------------------------------------------------------------------------
# New unified functional analytics pipeline (metrics + KPI + charts)
# ---------------------------------------------------------------------------

def compute_analytics_metrics(graph_controller):
    """Return dict of current + previous month metrics and deltas.

    Metrics:
      system_health (%), critical_equipment (count), avg_rul_months (float), system_reliability (%).
    Deltas are current - previous (same units). If previous missing -> delta 0.
    """
    metrics = {
        'system_health': 0.0,
        'system_health_prev': None,
        'system_health_delta': 0.0,
        'critical_equipment': 0,
        'critical_equipment_prev': None,
        'critical_equipment_delta': 0,
        'avg_rul_months': 0.0,
        'avg_rul_months_prev': None,
        'avg_rul_months_delta': 0.0,
        'system_reliability': 0.0,
        'system_reliability_prev': None,
        'system_reliability_delta': 0.0,
    }
    if not graph_controller:
        return metrics

    current_graph = graph_controller.get_current_date_graph()
    prev_graph = None
    try:
        prev_graph = graph_controller.get_previous_month_graph()
    except Exception:
        prev_graph = None

    def _extract_stats(g):
        if g is None:
            return {
                'system_health': 0.0,
                'critical_equipment': 0,
                'avg_rul_months': 0.0,
                'system_reliability': 0.0,
                'total_nodes': 0,
                'critical_nodes': 0,
            }
        node_conditions = [attrs.get('current_condition') for _, attrs in g.nodes(data=True) if 'current_condition' in attrs]
        # Normalize if stored 0-1 vs 0-100
        if node_conditions:
            avg_cond = sum(node_conditions)/len(node_conditions)
            if avg_cond <= 1.0:
                avg_cond *= 100.0
        else:
            avg_cond = 0.0
        critical_nodes = [n for n, a in g.nodes(data=True) if a.get('risk_level') == 'CRITICAL']
        rul_months_vals = []
        for _, a in g.nodes(data=True):
            if 'remaining_useful_life_days' in a:
                try:
                    rul_months_vals.append(a.get('remaining_useful_life_days', 0)/30.44)
                except Exception:
                    pass
        avg_rul = sum(rul_months_vals)/len(rul_months_vals) if rul_months_vals else 0.0
        total_nodes = g.number_of_nodes()
        reliability = ((total_nodes - len(critical_nodes))/total_nodes)*100 if total_nodes else 0.0
        return {
            'system_health': avg_cond,
            'critical_equipment': len(critical_nodes),
            'avg_rul_months': avg_rul,
            'system_reliability': reliability,
            'total_nodes': total_nodes,
            'critical_nodes': len(critical_nodes),
        }

    cur = _extract_stats(current_graph)
    prev = _extract_stats(prev_graph) if prev_graph is not None else None

    metrics['system_health'] = cur['system_health']
    if prev is not None:
        metrics['system_health_prev'] = prev['system_health']
        metrics['system_health_delta'] = cur['system_health'] - prev['system_health']
    metrics['critical_equipment'] = cur['critical_equipment']
    if prev is not None:
        metrics['critical_equipment_prev'] = prev['critical_equipment']
        metrics['critical_equipment_delta'] = cur['critical_equipment'] - prev['critical_equipment']
    metrics['avg_rul_months'] = cur['avg_rul_months']
    if prev is not None:
        metrics['avg_rul_months_prev'] = prev['avg_rul_months']
        metrics['avg_rul_months_delta'] = cur['avg_rul_months'] - prev['avg_rul_months']
    metrics['system_reliability'] = cur['system_reliability']
    if prev is not None:
        metrics['system_reliability_prev'] = prev['system_reliability']
        metrics['system_reliability_delta'] = cur['system_reliability'] - prev['system_reliability']

    pn.state.cache['analytics_metrics'] = metrics
    return metrics

def _format_delta(value, suffix='', precision=1):
    """Return formatted delta string with sign and unit suffix."""
    sign = '+' if value > 0 else ''
    fmt = f"{sign}{value:.{precision}f}{suffix}" if isinstance(value, (int, float)) else '0'
    return fmt

def update_kpi_cards(metrics):
    """Update Scott's individual KPI containers with computed metrics."""
    def trend_string(delta, unit):
        if delta == 0 or delta is None:
            return '0'
        arrow = '↗' if delta > 0 else '↘'
        if unit == 'months':
            return f"{arrow} {delta:+.1f} m"
        return f"{arrow} {delta:+.1f}{unit}"

    # System Health container
    sh_container = pn.state.cache.get("average_system_health_container")
    if sh_container is not None:
        sh_container.clear()
        sh_val = f"{metrics['system_health']:.1f}%"
        sh_prev = f"{metrics['system_health_prev']:.1f}%" if metrics['system_health_prev'] is not None else "N/A"
        sh_delta = metrics['system_health_delta']
        sh_container.append(pn.pane.Markdown(
            f"### Average System Health Change\n\n"
            f"**Current Month**: {sh_val}\n\n"
            f"**Previous Month**: {sh_prev}\n\n"
            f"**Change**: {trend_string(sh_delta, '%')}"
        ))

    # Critical Equipment container
    ce_container = pn.state.cache.get("critical_equipment_container")
    if ce_container is not None:
        ce_container.clear()
        ce_val = metrics['critical_equipment']
        ce_prev = metrics['critical_equipment_prev'] if metrics['critical_equipment_prev'] is not None else "N/A"
        ce_delta = metrics['critical_equipment_delta']
        ce_container.append(pn.pane.Markdown(
            f"### Critical Equipment\n\n"
            f"**Current Month**: {ce_val}\n\n"
            f"**Previous Month**: {ce_prev}\n\n"
            f"**Change**: {trend_string(ce_delta, '')}"
        ))

    # Average RUL container
    rul_container = pn.state.cache.get("average_rul_container")
    if rul_container is not None:
        rul_container.clear()
        rul_val = f"{metrics['avg_rul_months']:.1f} months"
        rul_prev = f"{metrics['avg_rul_months_prev']:.1f} months" if metrics['avg_rul_months_prev'] is not None else "N/A"
        rul_delta = metrics['avg_rul_months_delta']
        rul_container.append(pn.pane.Markdown(
            f"### Average Remaining Useful Life\n\n"
            f"**Current Month**: {rul_val}\n\n"
            f"**Previous Month**: {rul_prev}\n\n"
            f"**Change**: {trend_string(rul_delta, ' months')}"
        ))

    # System Reliability container already has header, just add content
    rel_container = pn.state.cache.get("system_reliability_container")
    if rel_container is not None:
        # Remove everything except the header
        if len(rel_container) > 1:
            rel_container[:] = rel_container[:1]
        rel_val = f"{metrics['system_reliability']:.1f}%"
        rel_prev = f"{metrics['system_reliability_prev']:.1f}%" if metrics['system_reliability_prev'] is not None else "N/A"
        rel_delta = metrics['system_reliability_delta']
        rel_container.append(pn.pane.Markdown(
            f"**Current Month**: {rel_val}\n\n"
            f"**Previous Month**: {rel_prev}\n\n"
            f"**Change**: {trend_string(rel_delta, '%')}"
        ))

    # Store for legacy compatibility
    pn.state.cache['analytics_metrics'] = metrics

def update_analytics_charts(graph_controller):
    """Update chart panes using visualization helpers if present."""
    try:
        current_graph = graph_controller.get_current_date_graph()
    except Exception:
        return
    # Remaining Useful Life
    rul_plot = pn.state.cache.get('remaining_useful_life_plot')
    if rul_plot is not None:
        try:
            rul_plot.object = get_remaining_useful_life_fig(current_graph)
        except Exception:
            pass
    # Risk Distribution
    risk_plot = pn.state.cache.get('risk_distribution_plot')
    if risk_plot is not None:
        try:
            risk_plot.object = get_risk_distribution_fig(current_graph)
        except Exception:
            pass
    # Condition Trends
    cond_plot = pn.state.cache.get('equipment_condition_trends_plot')
    if cond_plot is not None:
        try:
            # Build period series for last 3 / next 6 months
            periods = [(pd.Timestamp(graph_controller.current_date) + pd.DateOffset(months=i)).to_period('M') for i in range(-3,7)]
            graphs = [graph_controller.get_future_month_graph(i) for i in range(-3,7)]
            cond_plot.object = get_equipment_conditions_fig(graphs, periods, current_date=graph_controller.current_date)
        except Exception:
            pass
    # Maintenance Costs
    maint_plot = pn.state.cache.get('maintenance_costs_plot')
    if maint_plot is not None:
        try:
            maint_plot.object = get_maintenance_costs_fig(prioritized_schedule=graph_controller.prioritized_schedule, current_date=graph_controller.current_date)
        except Exception:
            pass

def update_analytics(graph_controller):
    """Public orchestrator: compute metrics, update KPI cards, then charts."""
    metrics = compute_analytics_metrics(graph_controller)
    update_kpi_cards(metrics)
    update_analytics_charts(graph_controller)
    print("Analytics updated (unified pipeline)")

def _update_kpi_cards_with_real_data(graph_controller):
    """Update KPI cards with real data from graph controller"""
    if not graph_controller or not hasattr(graph_controller, 'prioritized_schedule'):
        return
        
    current_date_graph = graph_controller.get_current_date_graph()
    if not current_date_graph:
        return
    
    # Calculate real KPI values
    kpi_data = _calculate_real_kpi_data(current_date_graph, graph_controller)
    
    # Update stored KPI card components with real data
    if "analytics_system_health" in pn.state.cache:
        health_value = f"{kpi_data['system_health']:.1f}%"
        # Calculate trend (mock for now - could be based on historical data)
        trend = "↘ -5%" if kpi_data['system_health'] < 50 else "↗ +2%"
        # Recreate card with real data
        pn.state.cache["analytics_system_health"][:] = [_create_kpi_card("System Health", health_value, trend, "System Health")]
        
    if "analytics_critical_equipment" in pn.state.cache:
        critical_count = kpi_data['critical_count']
        trend = "↗ +1" if critical_count > 10 else "↘ -2"
        pn.state.cache["analytics_critical_equipment"][:] = [_create_kpi_card("Critical Equipment", str(critical_count), trend, "Critical Equipment")]
        
    if "analytics_avg_rul" in pn.state.cache:
        avg_rul = f"{kpi_data['avg_rul_months']:.1f} months"
        trend = "↘ -2 months" if kpi_data['avg_rul_months'] < 60 else "↗ +1 month"
        pn.state.cache["analytics_avg_rul"][:] = [_create_kpi_card("Avg. RUL", avg_rul, trend, "Avg. RUL")]
        
    if "analytics_system_reliability" in pn.state.cache:
        reliability = f"{kpi_data['system_reliability']:.1f}%"
        trend = "↗ +2%" if kpi_data['system_reliability'] > 75 else "↘ -1%"
        pn.state.cache["analytics_system_reliability"][:] = [_create_kpi_card("System Reliability", reliability, trend, "System Reliability")]
    
    print(f"KPI cards updated with real data: {kpi_data}")

def _update_charts_with_real_data(graph_controller):
    """Update charts with real data from graph controller"""
    if not graph_controller or not hasattr(graph_controller, 'prioritized_schedule'):
        return
        
    current_date_graph = graph_controller.get_current_date_graph()
    if not current_date_graph:
        return
    
    # Calculate real chart data
    chart_data = _calculate_real_chart_data(current_date_graph, graph_controller)
    
    # Update stored chart components with real data
    if "analytics_rul_chart" in pn.state.cache:
        pn.state.cache["analytics_rul_chart"].object = _create_rul_bar_chart(chart_data)
        
    if "analytics_risk_chart" in pn.state.cache:
        pn.state.cache["analytics_risk_chart"].object = _create_risk_pie_chart(chart_data)
        
    if "analytics_condition_trends" in pn.state.cache:
        pn.state.cache["analytics_condition_trends"].object = _create_condition_trends_chart(chart_data)
        
    if "analytics_maintenance_costs" in pn.state.cache:
        pn.state.cache["analytics_maintenance_costs"].object = _create_maintenance_costs_chart(chart_data)
    
    print(f"Charts updated with real data: {len(chart_data)} data sets")

def _calculate_real_kpi_data(current_date_graph, graph_controller):
    """Calculate real KPI values from graph data"""
    
    # System Health: Average of all current_condition values
    node_conditions = []
    for node_id, attrs in current_date_graph.nodes(data=True):
        if 'current_condition' in attrs:
            node_conditions.append(attrs.get('current_condition'))
    
    system_health = (sum(node_conditions) / len(node_conditions)) if node_conditions else 0
    
    # Critical Equipment: Count of nodes with CRITICAL risk level
    critical_nodes = [node for node, attrs in current_date_graph.nodes(data=True) 
                     if attrs.get('risk_level') == 'CRITICAL']
    critical_count = len(critical_nodes)
    
    # Average RUL: Mean of remaining_useful_life_days converted to months
    rul_values = []
    for node_id, attrs in current_date_graph.nodes(data=True):
        if 'remaining_useful_life_days' in attrs:
            rul_days = attrs.get('remaining_useful_life_days', 0)
            rul_months = rul_days / 30.44  # Convert days to months
            rul_values.append(rul_months)
    
    avg_rul_months = (sum(rul_values) / len(rul_values)) if rul_values else 0
    
    # System Reliability: Based on percentage of non-critical components
    total_nodes = len(current_date_graph.nodes())
    reliability = ((total_nodes - critical_count) / total_nodes * 100) if total_nodes > 0 else 0
    
    return {
        'system_health': system_health,
        'critical_count': critical_count,
        'avg_rul_months': avg_rul_months,
        'system_reliability': reliability
    }

def _calculate_real_chart_data(current_date_graph, graph_controller):
    """Calculate real chart data from graph and simulation results"""
    
    # RUL Bar Chart Data: Get components with lowest RUL
    rul_components = []
    for node_id, attrs in current_date_graph.nodes(data=True):
        if 'remaining_useful_life_days' in attrs:
            rul_days = attrs.get('remaining_useful_life_days', 0)
            rul_months = rul_days / 30.44
            component_name = attrs.get('full_name', node_id)
            rul_components.append({
                'name': component_name,
                'rul_months': rul_months,
                'type': attrs.get('type', 'Unknown')
            })
    
    # Sort by RUL and take top 10 most critical
    rul_components.sort(key=lambda x: x['rul_months'])
    top_critical_components = rul_components[:10]
    
    # Risk Distribution Data: Count by risk levels
    risk_counts = {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0, 'CRITICAL': 0}
    for node_id, attrs in current_date_graph.nodes(data=True):
        risk_level = attrs.get('risk_level', 'LOW')
        if risk_level in risk_counts:
            risk_counts[risk_level] += 1
    
    total_components = sum(risk_counts.values())
    risk_distribution = {}
    if total_components > 0:
        risk_distribution = {
            'Low Risk': (risk_counts['LOW'] / total_components) * 100,
            'Medium Risk': ((risk_counts['MEDIUM'] + risk_counts['HIGH']) / total_components) * 100,
            'High Risk': (risk_counts['CRITICAL'] / total_components) * 100
        }
    
    # Equipment Status Data
    equipment_status = {
        'operational': risk_counts['LOW'],
        'warning': risk_counts['MEDIUM'] + risk_counts['HIGH'], 
        'critical': risk_counts['CRITICAL']
    }
    
    # Maintenance Costs: Extract from simulation results
    maintenance_costs = _extract_maintenance_costs_from_simulation(graph_controller)
    
    return {
        'top_critical_equipment': top_critical_components,  # Changed key name to match chart function
        'risk_distribution': risk_distribution,
        'equipment_status': equipment_status,
        'maintenance_costs': maintenance_costs
    }

def _extract_maintenance_costs_from_simulation(graph_controller):
    """Extract maintenance cost data from simulation results"""
    if not graph_controller.prioritized_schedule:
        return {'Preventive': 0, 'Corrective': 0, 'Emergency': 0, 'Planned': 0}
    
    # Get next 12 months data
    next_12_months = graph_controller.get_next_12_months_data()
    
    total_preventive = 0
    total_corrective = 0
    total_emergency = 0
    total_planned = 0
    
    for month, data in next_12_months.items():
        if data:
            executed_tasks = data.get('executed_tasks', [])
            
            for task in executed_tasks:
                cost = task.get('money_cost', 0)
                task_type = task.get('type', 'unknown')
                
                # Categorize costs based on task properties
                if task_type == 'emergency' or task.get('priority', 0) > 8:
                    total_emergency += cost
                elif task.get('frequency', 0) > 0:  # Regular maintenance
                    total_preventive += cost
                elif task.get('scheduled', False):
                    total_planned += cost
                else:
                    total_corrective += cost
    
    return {
        'Preventive': total_preventive,
        'Corrective': total_corrective, 
        'Emergency': total_emergency,
        'Planned': total_planned
    }
