# Helper functions for Remaining Useful Life (RUL) calculations and graph attribute assignment
import networkx as nx
import datetime
from dateutil.relativedelta import relativedelta

def calculate_remaining_useful_life(graph):
    """
    Calculate Remaining Useful Life (RUL) for each node using provided formula.
    Returns a dict mapping node to RUL in days.
    """
    import datetime
    rul_dict = {}
    current_date = datetime.datetime.now()
    for node, attrs in graph.nodes(data=True):
        # Extract attributes, with defaults if missing
        installation_date = attrs.get('installation_date')
        # installation_date is in YYYY-MM-DD format
        installation_date = datetime.datetime.strptime(installation_date, '%Y-%m-%d') 
        
        last_maintenance_date = attrs.get('last_maintenance_date')
        last_maintenance_date = datetime.datetime.strptime(last_maintenance_date, '%Y-%m-%d')

        operating_hours = attrs.get('operating_hours')
        maintenance_frequency = attrs.get('maintenance_frequency')  # in days
        expected_lifespan_years = attrs.get('expected_lifespan')  # in years, default 10 years
        expected_end_date = installation_date + relativedelta(years=expected_lifespan_years)

        expected_lifespan_days = (expected_end_date - installation_date).days

        time_since_maintenance = (current_date - last_maintenance_date).days

        # Overdue days and factor
        overdue_days = time_since_maintenance - maintenance_frequency
        overdue_factor = min(overdue_days / 30, 1.0) if overdue_days > 0 else 0.0

        # RUL baseline (in days)
        RUL_baseline_days = expected_lifespan_days - operating_hours
        # Adjusted RUL
        RUL_adjusted = RUL_baseline_days * (1 - 0.2 * overdue_factor)

        # Ensure RUL is not negative
        RUL_adjusted = max(RUL_adjusted, 0)
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
    rul_dict = calculate_remaining_useful_life(graph)
    for node, rul in rul_dict.items():
        graph.nodes[node]['remaining_useful_life_days'] = rul
        graph.nodes[node]['remaining_useful_life_years'] = rul / 365.25  # Convert days to years
    return graph
