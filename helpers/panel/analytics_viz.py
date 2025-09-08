import panel as pn
import plotly.graph_objects as go
import pandas as pd

def _create_enhanced_kpi_card(title, value, trend, metric_type, unit):
    """Create an enhanced styled KPI card with improved visual design."""
    def trend_string(delta, unit):
        if delta == 0 or delta is None:
            return '→ 0'
        arrow = '↗' if delta > 0 else '↘'
        return f"{arrow} {delta:+.3f} {unit}"
    trend = trend_string(trend, unit)
    
    # Color scheme based on metric type
    accent_colors = {
        "System Health": "#22c55e",  # Green
        "Critical Equipment": "#ef4444",  # Red  
        "Avg. RUL": "#3b82f6",  # Blue
        "System Reliability": "#8b5cf6",  # Purple
        "Total Replacement": "#ef4444",   # Red
        "Total Repair": "#22c55e",        # Green
        "Potential Savings": "#10b981",   # Emerald
        "Critical (12mo)": "#f59e0b",     # Amber/Orange
        "Budget": "#f59e0b",              # Amber
        "Savings": "#10b981",             # Emerald
        "Risk": "#ef4444",                # Red        
        "Lifespan Extension": "#3b82f6",
        "Condition Improvement": "#22c55e",
        "Risk Reduction": "#ef4444",
        "Lifespan": "#3b82f6",
        "Condition": "#22c55e"
    }
    
    accent_color = accent_colors.get(metric_type, "#6b7280")
    
    # Icon based on metric type with better visual representation
    icons = {
        "System Health": "🟢",
        "Critical Equipment": "🔴", 
        "Avg. RUL": "🔧",
        "System Reliability": "🛡️",
        "Total Replacement": "💸",
        "Total Repair": "🛠️",
        "Potential Savings": "💰",
        "Critical (12mo)": "⚠️",
        "Budget": "💰",
        "Savings": "💸",
        "Risk": "⚠️",
        "Lifespan Extension": "⏳",
        "Condition Improvement": "🟩",
        "Risk Reduction": "🔻",
        "Lifespan": "⏳",
        "Condition": "🟩"
    }
    
    icon = icons.get(metric_type, "📊")
    
    # Determine trend color based on trend direction
    trend_color = "#22c55e" if "↗" in trend else "#ef4444" if "↘" in trend else "#64748b"
    
    card_html = f"""
    <div style="
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        margin: 6px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        position: relative;
        overflow: hidden;
        min-height: 120px;
        transition: all 0.3s ease;
    ">
        <!-- Accent bar -->
        <div style="
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: {accent_color};
            box-shadow: 2px 0 4px rgba(0,0,0,0.1);
        "></div>
        
        <!-- Background pattern -->
        <div style="
            position: absolute;
            top: -10px;
            right: -10px;
            width: 40px;
            height: 40px;
            background: {accent_color};
            opacity: 0.05;
            border-radius: 50%;
        "></div>
        
        <!-- Header with icon -->
        <div style="
            display: flex;
            align-items: center;
            margin-bottom: 12px;
            margin-left: 8px;
        ">
            <span style="font-size: 20px; margin-right: 10px;">{icon}</span>
            <h3 style="
                margin: 0;
                font-size: 13px;
                font-weight: 600;
                color: #64748b;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            ">{title}</h3>
        </div>
        
        <!-- Value -->
        <div style="
            margin-left: 8px;
            margin-bottom: 8px;
        ">
            <span style="
                font-size: 32px;
                font-weight: 700;
                color: #1e293b;
                line-height: 1;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            ">{value}</span>
        </div>
        
        <!-- Trend with enhanced styling -->
        <div style="
            margin-left: 8px;
            font-size: 13px;
            color: {trend_color};
            font-weight: 600;
            padding: 2px 6px;
            background: rgba(255, 255, 255, 0.8);
            border-radius: 4px;
            display: inline-block;
            border: 1px solid {trend_color}22;
        ">{trend}</div>
    </div>
    """
    
    return pn.pane.HTML(card_html, sizing_mode="stretch_width", height=140)

