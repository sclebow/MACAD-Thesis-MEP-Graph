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
    REPLACEMENT_THRESHOLD = "HIGH"         # Risk state for replacement, if set to None, accelerated replacement will not be simulated
    
    # Debug settings
    ENABLE_RUL_WARNINGS = False             # Print warnings for low RUL
    ENABLE_DEBUG_OUTPUT = False            # Detailed calculation output
    IGNORE_UTILITY_TRANSFORMERS = True      # Ignore utility transformers in RUL calculations
    IGNORE_END_LOADS = True                 # Ignore end loads in RUL calculations

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
        if RULConfig.IGNORE_UTILITY_TRANSFORMERS and attrs.get('type') == 'utility_transformer':
            continue
        if RULConfig.IGNORE_END_LOADS and attrs.get('type') == 'end_load':
            continue

        # Extract attributes, with defaults if missing
        installation_date = attrs.get('installation_date')
        # installation_date is in YYYY-MM-DD format 
        if installation_date is None:
            print(f"Warning: Node {node} has no installation date. Skipping RUL calculation.")
            continue
        installation_date = datetime.datetime.strptime(installation_date, '%Y-%m-%d')

        expected_lifespan_years = attrs.get('expected_lifespan') or get_equipment_lifespan(attrs.get('type', 'unknown'))
        if attrs.get('expected_lifespan_days') is None:
            attrs['expected_lifespan_days'] = expected_lifespan_years * 365.25  # Convert years to days
        expected_end_date = installation_date + relativedelta(years=expected_lifespan_years)

        expected_lifespan_days = (expected_end_date - installation_date).days

        # Calculate operating days using installation_date and current_date
        operating_days = (current_date - installation_date).days

        # Calculate overdue_factor using tasks_deferred_count
        tasks_deferred_count = attrs.get('tasks_deferred_count')
        overdue_factor = tasks_deferred_count * RULConfig.TASK_DEFERMENT_FACTOR

        # RUL baseline (in days)
        RUL_baseline_days = expected_lifespan_days - operating_days
        
        # Adjusted RUL
        RUL_with_overdue = RUL_baseline_days * (1 - RULConfig.OVERDUE_IMPACT_MULTIPLIER * overdue_factor)

        # Add equipment age factor
        age_years = (current_date - installation_date).days / 365.25
        aging_factor = calculate_aging_factor(age_years)

        # Add condition factor  
        current_condition = attrs.get('current_condition', RULConfig.DEFAULT_INITIAL_CONDITION)
        condition_factor = 0.5 + (current_condition * 0.5)  # Range: 0.5 to 1.0

        # Apply all factors
        RUL_with_condition = RUL_with_overdue * condition_factor
        RUL_adjusted = RUL_with_condition / aging_factor

        # Store additional tracking info for analysis
        attrs['age_years'] = age_years
        attrs['current_condition'] = current_condition
        attrs['aging_factor'] = aging_factor
        attrs['condition_factor'] = condition_factor

        # Ensure RUL is not negative
        RUL_adjusted = max(RUL_adjusted, 0)

        # Calculate failure probability for risk assessment
        equipment_type = attrs.get('type', 'unknown')
        base_failure_rate = get_base_failure_rate(equipment_type)
        annual_failure_probability = base_failure_rate * aging_factor * (2.0 - current_condition)
        annual_failure_probability = min(annual_failure_probability, 0.95)

        # Store enhanced metrics for analysis
        attrs['annual_failure_probability'] = annual_failure_probability
        attrs['base_failure_rate'] = base_failure_rate
        attrs['risk_level'] = _assess_risk_level(RUL_adjusted / 365.25, current_condition)
        if 'replacement_required' in attrs:
            if not attrs['replacement_required']:
                attrs['replacement_required'] = attrs['risk_level'] == RULConfig.REPLACEMENT_THRESHOLD
        else:
            attrs['replacement_required'] = attrs['risk_level'] == RULConfig.REPLACEMENT_THRESHOLD

        # Enhanced warnings using configurable thresholds
        if RULConfig.ENABLE_RUL_WARNINGS:
            rul_years = RUL_adjusted / 365.25
            if rul_years < RULConfig.CRITICAL_RUL_THRESHOLD_YEARS:
                print(f"Warning: Node {node} has critically low RUL of {rul_years:.1f} years.")
            if annual_failure_probability > 0.20:
                print(f"Alert: Node {node} has high failure risk of {annual_failure_probability:.1%}.")
        rul_dict[node] = RUL_adjusted
    return rul_dict

def _assess_risk_level(rul_years: float, condition: float) -> str:
    """Assess risk level based on RUL and condition"""
    if rul_years <= RULConfig.CRITICAL_RUL_THRESHOLD_YEARS or condition < 0.3:
        return "CRITICAL"
    elif rul_years <= RULConfig.HIGH_RUL_THRESHOLD_YEARS or condition < 0.5:
        return "HIGH"
    elif rul_years <= RULConfig.MEDIUM_RUL_THRESHOLD_YEARS or condition < 0.7:
        return "MEDIUM"
    else:
        return "LOW"


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

    # print(f"Lowest RUL: {min(rul_dict.values())} days, Highest RUL: {max(rul_dict.values())} days")
    return graph

def apply_maintenance_log_to_graph(df: pd.DataFrame, graph):
    """
    Updates graph node attributes based on maintenance log DataFrame,
    and triggers a re-computation of RUL.
    
    Expected DataFrame format:
        node_id,last_maintenance_date,operating_hours
    """
    """debug code
    print(f"=== CSV Processing Debug ===")
    print(f"CSV rows: {len(df)}")
    print(f"CSV columns: {list(df.columns)}")
    print("CSV contents:")
    for index, row in df.iterrows():
        print(f"  Row {index}: {dict(row)}")
    print("=== End CSV Debug ===")"""
    
    for _, row in df.iterrows():
        node_id = row.get('node_id') or row.get('component_id')
        maintenance_type = row.get('maintenance_type', row.get('type', 'routine')).lower()
        """debug code
        print(f"=== Processing Row ===")
        print(f"  Looking for node_id: '{node_id}'")
        print(f"  Maintenance type: '{maintenance_type}'")
        print(f"  Node in graph: {node_id in graph.nodes if node_id else False}")"""

        if pd.notna(maintenance_type) and node_id in graph.nodes:
            """debug code
            print(f"  ✅ PROCESSING MAINTENANCE for {node_id}")"""
            # Get current condition
            current_condition = graph.nodes[node_id].get('current_condition', RULConfig.DEFAULT_INITIAL_CONDITION)
                
            # Determine condition improvement based on maintenance type
            if maintenance_type in ['scheduled', 'routine', 'preventive', 'pm']:
                # Routine maintenance - modest improvement
                condition_improvement = 0.05  # 5% improvement
                new_condition = min(1.0, current_condition + condition_improvement)
                reason = f"Scheduled maintenance: {maintenance_type}"
                    
            elif maintenance_type in ['major', 'overhaul', 'rebuild', 'refurbishment']:
                # Major maintenance - significant improvement
                condition_improvement = 0.30  # 30% improvement
                new_condition = min(1.0, current_condition + condition_improvement)
                reason = f"Major maintenance: {maintenance_type}"
                    
            elif maintenance_type in ['replacement', 'new', 'install']:
                # Full replacement - like new condition
                new_condition = 1.0
                reason = f"Equipment replacement: {maintenance_type}"
                    
                # Reset installation date for replacements
                maintenance_date = row.get('maintenance_date', row.get('date'))
                if pd.notna(maintenance_date):
                    graph.nodes[node_id]['installation_date'] = str(maintenance_date)[:10]  # YYYY-MM-DD format
                        
            elif maintenance_type in ['repair', 'corrective', 'emergency', 'breakdown']:
                # Repair after breakdown - limited improvement
                condition_improvement = 0.15  # 15% improvement
                new_condition = min(1.0, current_condition + condition_improvement)
                reason = f"Corrective maintenance: {maintenance_type}"
                    
            elif maintenance_type in ['inspection', 'testing', 'diagnostic']:
                # Inspection only - minimal improvement
                condition_improvement = 0.02  # 2% improvement
                new_condition = min(1.0, current_condition + condition_improvement)
                reason = f"Inspection: {maintenance_type}"
                    
            else:
                # Unknown maintenance type - small default improvement
                condition_improvement = 0.03  # 3% improvement
                new_condition = min(1.0, current_condition + condition_improvement)
                reason = f"General maintenance: {maintenance_type}"
                
            # Update the component condition
            graph.nodes[node_id]['current_condition'] = new_condition
                
            # Track condition history
            if 'condition_history' not in graph.nodes[node_id]:
                graph.nodes[node_id]['condition_history'] = []
                
            graph.nodes[node_id]['condition_history'].append({
                'date': str(row.get('maintenance_date', row.get('date', datetime.datetime.now().date()))),
                'old_condition': current_condition,
                'new_condition': new_condition,
                'reason': reason,
                'maintenance_type': maintenance_type
            })
                
            if RULConfig.ENABLE_DEBUG_OUTPUT:
                print(f"Maintenance applied to {node_id}: {current_condition:.2f} → {new_condition:.2f} ({reason})")
    # Now apply RUL calculations with updated conditions
        if node_id in graph.nodes:
            if pd.notna(row.get('last_maintenance_date')):
                graph.nodes[node_id]['last_maintenance_date'] = str(row['last_maintenance_date'])
            if pd.notna(row.get('operating_hours')):
                graph.nodes[node_id]['operating_hours'] = int(row['operating_hours'])

    # Recalculate RUL after graph update
    apply_rul_to_graph(graph)
    
def apply_condition_improvement(graph, node_id: str, improvement_effect: float, maintenance_type: str):
    """
    Applies a condition improvement to a node and logs the change.
    """
    if node_id not in graph.nodes:
        return

    old_condition = graph.nodes[node_id].get('current_condition', RULConfig.DEFAULT_INITIAL_CONDITION)
    
    # If effect is 1.0, it's a full replacement, setting condition to 1.0
    if improvement_effect >= 1.0:
        new_condition = 1.0
    else:
        new_condition = min(1.0, old_condition + improvement_effect) # TODO improve logic

    graph.nodes[node_id]['current_condition'] = new_condition

    # Track condition history
    if 'condition_history' not in graph.nodes[node_id]:
        graph.nodes[node_id]['condition_history'] = []
    
    graph.nodes[node_id]['condition_history'].append({
        'date': datetime.datetime.now().isoformat(),
        'old_condition': old_condition,
        'new_condition': new_condition,
        'reason': f"Executed task: {maintenance_type}"
    })

    if RULConfig.ENABLE_DEBUG_OUTPUT:
        print(f"Condition for {node_id} improved: {old_condition:.2f} -> {new_condition:.2f} due to {maintenance_type}")


def update_component_condition(graph, node_id: str, new_condition: float, reason: str = "Manual update") -> bool:
    """
    Update component condition and track the change
    """
    if node_id not in graph.nodes:
        print(f"Error: Component {node_id} not found in graph")
        return False
    
    # Get current condition
    old_condition = graph.nodes[node_id].get('current_condition', RULConfig.DEFAULT_INITIAL_CONDITION)
    
    # Set new condition with bounds checking
    new_condition = max(0.0, min(1.0, new_condition))
    graph.nodes[node_id]['current_condition'] = new_condition
    
    # Track condition history
    if 'condition_history' not in graph.nodes[node_id]:
        graph.nodes[node_id]['condition_history'] = []
    
    graph.nodes[node_id]['condition_history'].append({
        'date': datetime.datetime.now().isoformat(),
        'old_condition': old_condition,
        'new_condition': new_condition,
        'reason': reason
    })
    
    # Recalculate RUL with new condition
    apply_rul_to_graph(graph)
    
    if RULConfig.ENABLE_DEBUG_OUTPUT:
        print(f"Updated {node_id} condition: {old_condition:.2f} → {new_condition:.2f} ({reason})")
    
    return True

def adjust_rul_parameters(**kwargs) -> dict:
    """
    Adjust RUL calculation parameters (Scott's "dials")
    """
    changed_params = {}
    
    for param_name, new_value in kwargs.items():
        if hasattr(RULConfig, param_name):
            old_value = getattr(RULConfig, param_name)
            setattr(RULConfig, param_name, new_value)
            changed_params[param_name] = {'old': old_value, 'new': new_value}
            
            if RULConfig.ENABLE_DEBUG_OUTPUT:
                print(f"Parameter {param_name}: {old_value} → {new_value}")
        else:
            print(f"Warning: Unknown parameter {param_name}")
    
    return changed_params

def get_current_parameters() -> dict:
    """
    Get current values of all RUL parameters
    """
    params = {}
    for attr_name in dir(RULConfig):
        if not attr_name.startswith('_'):  # Skip private attributes
            params[attr_name] = getattr(RULConfig, attr_name)
    
    return params

def reset_all_conditions(graph, condition: float = 1.0, reason: str = "System reset"):
    """
    Reset all component conditions (useful for testing)
    """
    count = 0
    for node_id, attrs in graph.nodes(data=True):
        if attrs.get('type') != 'end_load':
            update_component_condition(graph, node_id, condition, reason)
            count += 1
    
    print(f"Reset {count} components to condition {condition:.1f}")
    return count

def get_component_summary(graph, node_id: str) -> dict:
    """
    Get comprehensive summary for a specific component
    """
    if node_id not in graph.nodes:
        return {'error': f'Component {node_id} not found'}
    
    attrs = graph.nodes[node_id]
    
    # Calculate current age
    installation_date = attrs.get('installation_date')
    if installation_date:
        try:
            install_date = datetime.datetime.strptime(installation_date, '%Y-%m-%d')
            age_years = (datetime.datetime.now() - install_date).days / 365.25
        except:
            age_years = 0
    else:
        age_years = 0
    
    summary = {
        'component_id': node_id,
        'type': attrs.get('type', 'unknown'),
        'age_years': round(age_years, 1),
        'installation_date': installation_date,
        'current_condition': attrs.get('current_condition', 1.0),
        'tasks_deferred_count': attrs.get('tasks_deferred_count', 0),
        'aging_factor': attrs.get('aging_factor', 1.0),
        'condition_factor': attrs.get('condition_factor', 1.0),
        'annual_failure_probability': attrs.get('annual_failure_probability', 0.0),
        'risk_level': attrs.get('risk_level', 'UNKNOWN'),
        'rul_years': attrs.get('remaining_useful_life_days', 0) / 365.25 if attrs.get('remaining_useful_life_days') else 0,
        'expected_lifespan': get_equipment_lifespan(attrs.get('type', 'unknown'))
    }
    
    return summary

def get_system_risk_overview(graph) -> dict:
    """
    Get system-wide risk overview
    """
    components = []
    risk_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'UNKNOWN': 0}
    total_failure_probability = 0
    
    for node_id, attrs in graph.nodes(data=True):
        if attrs.get('type') == 'end_load':
            continue  # Skip end loads
            
        summary = get_component_summary(graph, node_id)
        components.append(summary)
        
        risk_level = summary.get('risk_level', 'UNKNOWN')
        risk_counts[risk_level] += 1
        
        failure_prob = summary.get('annual_failure_probability', 0)
        total_failure_probability += failure_prob
    
    total_components = len(components)
    
    overview = {
        'total_components': total_components,
        'risk_distribution': risk_counts,
        'high_risk_components': risk_counts['CRITICAL'] + risk_counts['HIGH'],
        'avg_failure_probability': total_failure_probability / max(total_components, 1),
        'components_needing_attention': [
            c for c in components 
            if c.get('risk_level') in ['CRITICAL', 'HIGH'] or c.get('rul_years', 0) < 2
        ]
    }
    
    return overview