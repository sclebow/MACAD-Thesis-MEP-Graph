import panel as pn
import plotly.graph_objects as go

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
    """Create the Analytics Dashboard with KPIs, charts, and equipment status"""
    
    # Add header section
    _create_header_section(analytics_container)
    
    # Create KPI cards row
    _create_kpi_cards_section(analytics_container, graph_controller)
    
    # Create charts grid  
    _create_charts_section(analytics_container, graph_controller)
    
    # Create equipment status summary
    _create_equipment_status_section(analytics_container, graph_controller)

def _create_header_section(analytics_container):
    """Create the header section with title and description"""
    # Note: Headers are typically handled by the main app, so this might be optional
    pass

def _create_kpi_cards_section(analytics_container, graph_controller):
    """Create the KPI cards row - System Health, Critical Equipment, Avg RUL, System Reliability"""
    
    # Create KPI cards with mock data
    system_health_card = _create_kpi_card("System Health", "68%", "📉", "#22c55e")
    critical_equipment_card = _create_kpi_card("Critical Equipment", "3", "🔺", "#ef4444")
    avg_rul_card = _create_kpi_card("Avg. RUL", "18 months", "📉", "#f59e0b")
    system_reliability_card = _create_kpi_card("System Reliability", "87%", "�", "#3b82f6")
    
    # Store references for real-time updates
    pn.state.cache["analytics_system_health"] = system_health_card
    pn.state.cache["analytics_critical_equipment"] = critical_equipment_card
    pn.state.cache["analytics_avg_rul"] = avg_rul_card
    pn.state.cache["analytics_system_reliability"] = system_reliability_card
    
    # Place cards in grid
    analytics_container[0, 0] = system_health_card
    analytics_container[0, 1] = critical_equipment_card
    analytics_container[0, 2] = avg_rul_card
    analytics_container[0, 3] = system_reliability_card

def _create_charts_section(analytics_container, graph_controller):
    """Create the 2x2 charts grid"""
    
    # Store chart containers for real-time updates
    rul_chart_pane = pn.pane.Plotly(_create_rul_bar_chart(), sizing_mode="stretch_width", height=300)
    risk_chart_pane = pn.pane.Plotly(_create_risk_pie_chart(), sizing_mode="stretch_width", height=300)
    condition_trends_pane = pn.pane.Plotly(_create_condition_trends_chart(), sizing_mode="stretch_width", height=300)
    maintenance_costs_pane = pn.pane.Plotly(_create_maintenance_costs_chart(), sizing_mode="stretch_width", height=300)
    
    # Store references for updates
    pn.state.cache["analytics_rul_chart"] = rul_chart_pane
    pn.state.cache["analytics_risk_chart"] = risk_chart_pane
    pn.state.cache["analytics_condition_trends"] = condition_trends_pane
    pn.state.cache["analytics_maintenance_costs"] = maintenance_costs_pane
    
    # Top Left: RUL Bar Chart
    rul_chart_container = pn.Column(
        pn.pane.Markdown("### Remaining Useful Life (Months)"),
        rul_chart_pane
    )
    analytics_container[1, 0:2] = rul_chart_container

    # Top Right: Risk Distribution Pie Chart
    risk_chart_container = pn.Column(
        pn.pane.Markdown("### Risk Distribution"),
        risk_chart_pane
    )
    analytics_container[1, 2:4] = risk_chart_container

    # Bottom Left: Equipment Condition Trends
    condition_trends_container = pn.Column(
        pn.pane.Markdown("### Equipment Condition Trends"),
        condition_trends_pane
    )
    analytics_container[2, 0:2] = condition_trends_container

    # Bottom Right: Maintenance Costs
    maintenance_costs_container = pn.Column(
        pn.pane.Markdown("### Maintenance Costs"),
        maintenance_costs_pane
    )
    analytics_container[2, 2:4] = maintenance_costs_container

def _create_equipment_status_section(analytics_container, graph_controller):
    """Create the equipment status summary section"""
    
    # Equipment Status Summary
    equipment_status_container = pn.Column(
        pn.pane.Markdown("### Equipment Status Summary"),
        pn.Row(
            pn.Column(
                pn.pane.Markdown("**5**", styles={'text-align': 'center', 'font-size': '24px', 'color': '#22c55e'}),
                pn.pane.Markdown("Operational", styles={'text-align': 'center', 'color': '#16a34a'}),
                styles={'background': '#f0fdf4', 'border-radius': '8px', 'padding': '16px', 'text-align': 'center'},
                sizing_mode="stretch_width",
                margin=(5, 5)
            ),
            pn.Column(
                pn.pane.Markdown("**2**", styles={'text-align': 'center', 'font-size': '24px', 'color': '#f59e0b'}),
                pn.pane.Markdown("Warning", styles={'text-align': 'center', 'color': '#d97706'}),
                styles={'background': '#fffbeb', 'border-radius': '8px', 'padding': '16px', 'text-align': 'center'},
                sizing_mode="stretch_width",
                margin=(5, 5)
            ),
            pn.Column(
                pn.pane.Markdown("**1**", styles={'text-align': 'center', 'font-size': '24px', 'color': '#ef4444'}),
                pn.pane.Markdown("Critical", styles={'text-align': 'center', 'color': '#dc2626'}),
                styles={'background': '#fef2f2', 'border-radius': '8px', 'padding': '16px', 'text-align': 'center'},
                sizing_mode="stretch_width",
                margin=(5, 5)
            ),
            sizing_mode="stretch_width"
        ),
        sizing_mode="stretch_width"
    )
    analytics_container[3, 0:4] = equipment_status_container

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
