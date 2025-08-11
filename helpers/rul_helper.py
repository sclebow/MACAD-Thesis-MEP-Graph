# Helper functions for Remaining Useful Life (RUL) calculations and graph attribute assignment
import pandas as pd
import networkx as nx
import datetime
from dateutil.relativedelta import relativedelta

# Configuration class for RUL parameters
class RULConfig:
    """
    Centralized configuration for RUL calculation parameters.
    """
    
    # Your existing factors (now configurable)
    TASK_DEFERMENT_FACTOR = 0.04
    OVERDUE_IMPACT_MULTIPLIER = 0.2

    # Equipment lifespan defaults (years)
    DEFAULT_LIFESPANS = {
        'utility_transformer': 35,
        'transformer': 30,
        'switchboard': 25,
        'panelboard': 20,
        'panel': 20,
        'end_load': 15,
        'unknown': 20
    }
    
    # Base failure rates by equipment type (annual probability)
    BASE_FAILURE_RATES = {
        'utility_transformer': 0.015,     # 1.5% annual
        'transformer': 0.020,             # 2.0% annual  
        'switchboard': 0.025,             # 2.5% annual
        'panelboard': 0.030,              # 3.0% annual
        'panel': 0.030,                   # 3.0% annual
        'end_load': 0.050,                # 5.0% annual
        'unknown': 0.025                  # 2.5% default
    }
    
    # Aging factors
    AGING_ACCELERATION_FACTOR = 0.02      # 2% failure rate increase per year
    MAX_AGING_MULTIPLIER = 3.0            # Cap aging impact at 3x
    
    # Condition factors
    DEFAULT_INITIAL_CONDITION = 1.0       # New equipment starts perfect
    MIN_RUL_RATIO = 0.01                  # Minimum 1% of expected lifespan
    
    # Risk thresholds
    CRITICAL_RUL_THRESHOLD_YEARS = 1.0     # < 1 year = CRITICAL
    HIGH_RUL_THRESHOLD_YEARS = 3.0         # < 3 years = HIGH  
    MEDIUM_RUL_THRESHOLD_YEARS = 7.0       # < 7 years = MEDIUM
    
    # Debug settings
    ENABLE_RUL_WARNINGS = True             # Print warnings for low RUL
    ENABLE_DEBUG_OUTPUT = False            # Detailed calculation output

# Helper functions for parameters
def get_equipment_lifespan(equipment_type: str) -> float:
    """Get expected lifespan for equipment type"""
    equipment_type = equipment_type.lower() if equipment_type else 'unknown'
    return RULConfig.DEFAULT_LIFESPANS.get(equipment_type, RULConfig.DEFAULT_LIFESPANS['unknown'])

def get_base_failure_rate(equipment_type: str) -> float:
    """Get annual base failure rate for equipment type"""
    equipment_type = equipment_type.lower() if equipment_type else 'unknown'
    return RULConfig.BASE_FAILURE_RATES.get(equipment_type, RULConfig.BASE_FAILURE_RATES['unknown'])

def calculate_aging_factor(age_years: float) -> float:
    """Calculate aging impact on failure rate"""
    aging_multiplier = 1.0 + (age_years * RULConfig.AGING_ACCELERATION_FACTOR)
    return min(aging_multiplier, RULConfig.MAX_AGING_MULTIPLIER) 

def calculate_remaining_useful_life(graph, current_date):
    """
    Calculate Remaining Useful Life (RUL) for each node using provided formula.
    Returns a dict mapping node to RUL in days.
    """
    rul_dict = {}
    for node, attrs in graph.nodes(data=True):
        # Extract attributes, with defaults if missing
        installation_date = attrs.get('installation_date')
        # installation_date is in YYYY-MM-DD format
        if installation_date is None:
            print(f"Warning: Node {node} has no installation date. Skipping RUL calculation.")
            continue
        installation_date = datetime.datetime.strptime(installation_date, '%Y-%m-%d')

        expected_lifespan_years = attrs.get('expected_lifespan')  # in years, default 10 years
        if attrs.get('expected_lifespan_days') is None:
            attrs['expected_lifespan_days'] = expected_lifespan_years * 365.25  # Convert years to days
        expected_end_date = installation_date + relativedelta(years=expected_lifespan_years)

        expected_lifespan_days = (expected_end_date - installation_date).days

        # Calculate operating days using installation_date and current_date
        operating_days = (current_date - installation_date).days

        # Calculate overdue_factor using tasks_deferred_count
        tasks_deferred_count = attrs.get('tasks_deferred_count', 0)
        overdue_factor = tasks_deferred_count * 0.04  # Example: each deferred task increases factor by 0.1

        # RUL baseline (in days)
        RUL_baseline_days = expected_lifespan_days - operating_days
        # Adjusted RUL
        RUL_adjusted = RUL_baseline_days * (1 - 0.2 * overdue_factor)

        # Ensure RUL is not negative
        RUL_adjusted = max(RUL_adjusted, 0)
        if RUL_adjusted < 30:
            print(f"Warning: Node {node} has critically low RUL of {RUL_adjusted} days.")
        if RUL_adjusted == 0:
            print(f"Alert: Node {node} has reached end of life (RUL = 0 days). Immediate action required.")
        rul_dict[node] = RUL_adjusted
    return rul_dict

def apply_rul_to_graph(graph, current_date=None):
    """
    Apply calculated RUL values to graph nodes as 'remaining_useful_life' attribute.
    Optionally accepts current_date for reproducibility/testing.
    """
    import datetime
    if current_date is None:
        current_date = datetime.datetime.now()
    rul_dict = calculate_remaining_useful_life(graph, current_date)
    for node, rul in rul_dict.items():
        graph.nodes[node]['remaining_useful_life_days'] = rul
        graph.nodes[node]['remaining_useful_life_years'] = rul / 365.25  # Convert days to years
    return graph

def apply_maintenance_log_to_graph(df: pd.DataFrame, graph):
    """
    Updates graph node attributes based on maintenance log DataFrame,
    and triggers a re-computation of RUL.
    
    Expected DataFrame format:
        node_id,last_maintenance_date,operating_hours
    """
    for _, row in df.iterrows():
        node_id = row.get('node_id')
        if node_id in graph.nodes:
            if pd.notna(row.get('last_maintenance_date')):
                graph.nodes[node_id]['last_maintenance_date'] = str(row['last_maintenance_date'])
            if pd.notna(row.get('operating_hours')):
                graph.nodes[node_id]['operating_hours'] = int(row['operating_hours'])

    # Recalculate RUL after graph update
    apply_rul_to_graph(graph)
