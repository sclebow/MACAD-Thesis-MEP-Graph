"""
MEP Graph Generator - Creates realistic electrical system topologies

This module generates random but logical electrical system graphs in MEPG format.
The generator creates hierarchical topologies starting from utility transformers,
through switchboards, to distribution panels and end loads.

General Strategy:
1. Define the building characteristics:
- Number of floors
- X and Y dimensions of the building (assuming a rectangular shape)
- Total Electrical load in kW

2. Determine the number of vertical risers:
- Based on the number of floors and the X dimension, calculate how many vertical risers are needed.
- A tall, narrow building may have fewer risers, while a short, wide building may have more.
- Each riser will have a dedicated path for electrical distribution.

3. Locate the risers within the building:
- Randomly place risers along the X, Y planes of the building.
- Ensure that risers are spaced evenly to allow for efficient distribution.
- For a single riser, place it centrally; for multiple risers, distribute them evenly across the X dimension.

4. Determine building voltage level:
- If the Total Electrical Load is below a certain threshold, use 120/208V.
- If the load is above the threshold, use 277/480V.
- If 480V we will have step-down transformers to 208V for the distribution system.
- If 208V we only need the utility transformer and distribution nodes.

5. Distribute loads across the building levels:
- Calculate the total load per floor based on the total load and number of floors.
- Randomly vary the load per floor within a reasonable range, e.g., ±10% of the average load per floor.  The sum of all loads should equal the total load.
- Ensure that the total load across all floors matches the specified total load.
- Distribute end loads across the floors.
    - We can have a set list of end load types: ["lighting", "receptacles", "hvac", "kitchen", "specialty"]
- Each end load type can have a specific power rating, e.g., lighting = 1.5 kW, receptacles = 2.0 kW, etc.
- Randomly assign end loads to floors, ensuring that the total load per floor does not exceed a reasonable limit, e.g., 50% of the floor's total load.
- Each end load will be represented as a node in the graph with its power rating.
- Assign each end load to the nearest riser based on its floor location.
- Assign each end load a voltage level based on the available voltages in the building.
    - For 120/208V buildings, end loads will be at 208V or 120V.
    - For 277/480V buildings, end loads will be at 480V, 277V, 208V, or 120V.

6. Determine the riser attributes on each floor:
- For each floor, each riser will power a set of end loads.
- Using the end loads determine the following attributes for each riser on the floor:
    - dictionary of end load types with their total power ratings at each voltage level.
    - For example, if a riser powers 3 lighting loads at 208V, 2 receptacles at 120V, 1 HVAC load at 277V, and 1 lighting load at 277V, the dictionary could look like:
      {
        "lighting": { 208: 3 * 1.5, 277: 1 * 1.5 },
        "receptacles": { 120: 2 * 2.0 },
        "hvac": { 277: 1 * 3.0 }
      }
- This will help in understanding the load distribution across risers and floors.

7. Place distribution equipment in each riser on each floor:
- At this stage we refer to "distribution equipment" as the nodes that will connect to end loads.
- Each riser will have a set of distribution equipment based on the end loads it serves.
- First there will be a distribution equipment at the highest voltage level (480V or 208V).
- Then for each end load type's voltage level, there will be either a step-down transformer or distribution panel.
- For end load types that require both 480V or 277V, and 208V or 120V, we will a 480V/277V distribution panel and a 208V/120V distribution panel with a step-down transformer.
- Each distribution equipment will be represented as a node in the graph.

8. Connect the nodes:
- Connect the utility transformer the nearest riser level node on the ground floor.
- Connect each riser level node to the riser distribution equipment on that floor.

"""

import random
import math
import datetime
import networkx as nx
from typing import List, Dict, Tuple, Any, Optional
from dataclasses import dataclass

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from helpers.node_risk import apply_risk_scores_to_graph
from helpers.rul_helper import apply_rul_to_graph

# --- Constants ---
# Standard equipment sizes in Amps for distribution panels and switchboards.
STANDARD_DISTRIBUTION_EQUIPMENT_SIZES = [
    60,
    100,
    150,
    200,
    225,
    300,
    400,
    500,
    600,
    800,
    1000,
    1200,
    1600,
    2000,
    2500,
    3000,
    4000,
    5000,
    6000,
    8000,
    10000,
]

STANDARD_DISTRIBUTION_EQUIPMENT_COSTS = [ # Costs in USD for each size
    1000,  # 60A
    1500,  # 100A
    2000,  # 150A
    2250,  # 200A
    3000,  # 225A
    4000,  # 300A
    5000,  # 400A
    6000,  # 500A
    8000,  # 600A
    10000, # 800A
    12000, # 1000A
    16000, # 1200A
    20000, # 1600A
    25000, # 2000A
    30000, # 2500A
    40000, # 3000A
    50000, # 4000A
    60000, # 5000A
    80000, # 6000A
    100000, # 8000A
    120000, # 10000A
]

MAXIMUM_PANEL_SIZE = 800 # Any larger than this is considered a switchboard

STANDARD_TRANSFORMER_SIZES = [
    15,  # kVA
    25,
    37.5,
    50,
    75,
    100,
    112.5,
    150,
    167,
    200,
    225,
    250,
    300,
    400,
    500,
]

STANDARD_TRANSFORMER_COSTS = [ # Costs in USD for each size
    1500,  # 15 kVA
    2500,  # 25 kVA
    3750,  # 37.5 kVA
    5000,  # 50 kVA
    7500,  # 75 kVA
    10000, # 100 kVA
    11250, # 112.5 kVA
    15000, # 150 kVA
    16700, # 167 kVA
    20000, # 200 kVA
    22500, # 225 kVA
    25000, # 250 kVA
    30000, # 300 kVA
    40000, # 400 kVA
    50000, # 500 kVA
]

# Equipment baseline attributes for new construction
EQUIPMENT_BASELINE_ATTRIBUTES = {
    'utility_transformer': {
        'expected_lifespan': 35,  # years
        'maintenance_frequency': 12,  # months between maintenance intervals
        'operating_hours': 0,  # total cumulative runtime hours since installation
        'mean_time_to_failure': 306600,  # hours (theoretical, based on expected lifespan)
        'failure_count': 0  # number of failures since installation
    },
    'main_panel': {
        'expected_lifespan': 30,  # years
        'maintenance_frequency': 24,  # months between maintenance intervals
        'operating_hours': 0,  # total cumulative runtime hours since installation
        'mean_time_to_failure': 262800,  # hours (theoretical, based on expected lifespan)
        'failure_count': 0  # number of failures since installation
    },
    'sub_panel': {
        'expected_lifespan': 25,  # years
        'maintenance_frequency': 24,  # months between maintenance intervals
        'operating_hours': 0,  # total cumulative runtime hours since installation
        'mean_time_to_failure': 219000,  # hours (theoretical, based on expected lifespan)
        'failure_count': 0  # number of failures since installation
    },
    'transformer': {
        'expected_lifespan': 30,  # years
        'maintenance_frequency': 12,  # months between maintenance intervals
        'operating_hours': 0,  # total cumulative runtime hours since installation
        'mean_time_to_failure': 262800,  # hours (theoretical, based on expected lifespan)
        'failure_count': 0  # number of failures since installation
    },
    'end_load': {
        'expected_lifespan': 15,  # years (varies by load type, this is average)
        'maintenance_frequency': 6,   # months between maintenance intervals
        'operating_hours': 0,  # total cumulative runtime hours since installation
        'mean_time_to_failure': 131400,  # hours (theoretical, based on expected lifespan)
        'failure_count': 0  # number of failures since installation
    }
}

# --- Node ID Abbreviation Functions ---
def abbreviate_equipment_type(eq_type):
    """Convert equipment type to abbreviated form."""
    abbreviations = {
        'main_panel': 'MP',
        'sub_panel': 'SP',
        'transformer': 'TR',
        'end_load': 'EL',
        'utility_transformer': 'UT',
        'panel': 'P',
        'switchboard': 'SB'
    }
    return abbreviations.get(eq_type, eq_type)

def abbreviate_load_type(load_type):
    """Convert load type to abbreviated form."""
    abbreviations = {
        'lighting': 'L',
        'receptacles': 'R',
        'hvac': 'H',
        'kitchen': 'K',
        'specialty': 'S'
    }
    return abbreviations.get(load_type, load_type)

def create_abbreviated_node_id(eq_type, floor=None, riser=None, voltage=None, load_type=None, secondary_voltage=None, cluster_id=None):
    """Create abbreviated node ID using compact notation."""
    type_abbrev = abbreviate_equipment_type(eq_type)
    
    if eq_type == 'utility_transformer':
        return 'UT'
    
    # Base ID with floor and riser
    base_id = f"{type_abbrev}{floor}.{riser}"
    
    # Add voltage and load type for specific equipment
    if eq_type == 'transformer':
        load_abbrev = abbreviate_load_type(load_type) if load_type else ''
        return f"{base_id}.{secondary_voltage}.{load_abbrev}" if secondary_voltage and load_abbrev else base_id
    elif eq_type in ['sub_panel', 'panel', 'switchboard']:
        load_abbrev = abbreviate_load_type(load_type) if load_type else ''
        if voltage and load_abbrev:
            return f"{base_id}.{voltage}.{load_abbrev}"
        elif voltage:
            return f"{base_id}.{voltage}"
        else:
            return base_id
    elif eq_type == 'end_load':
        load_abbrev = abbreviate_load_type(load_type) if load_type else ''
        if cluster_id is not None:
            return f"{base_id}.{voltage}.{load_abbrev}.c{cluster_id}" if voltage and load_abbrev else f"{base_id}.c{cluster_id}"
        else:
            return f"{base_id}.{voltage}.{load_abbrev}" if voltage and load_abbrev else base_id
    else:
        return base_id

def create_full_node_id(eq_type, floor=None, riser=None, voltage=None, load_type=None, secondary_voltage=None, cluster_id=None):
    """Create full (original) node ID for storage as an attribute."""
    if eq_type == 'utility_transformer':
        return 'utility_transformer'
    
    # Base ID with floor and riser
    base_id = f"{eq_type}_f{floor}_r{riser}"
    
    # Add voltage and load type for specific equipment
    if eq_type == 'transformer':
        return f"{base_id}_{secondary_voltage}_{load_type}" if secondary_voltage and load_type else base_id
    elif eq_type in ['sub_panel', 'panel', 'switchboard']:
        if voltage and load_type:
            return f"{base_id}_{voltage}_{load_type}"
        elif voltage:
            return f"{base_id}_{voltage}"
        else:
            return base_id
    elif eq_type == 'end_load':
        if cluster_id is not None:
            return f"{base_id}_{load_type}_{voltage}_c{cluster_id}" if voltage and load_type else f"{base_id}_c{cluster_id}"
        else:
            return f"{base_id}_{load_type}_{voltage}" if voltage and load_type else base_id
    else:
        return base_id

def get_baseline_attributes(equipment_type, building_attrs):
    """Get baseline attributes for new equipment based on type and construction year."""
    construction_date = building_attrs.get('construction_date')

    # Get baseline attributes for this equipment type
    baseline = EQUIPMENT_BASELINE_ATTRIBUTES.get(equipment_type)
    # Create attributes dictionary

    # Assume installation_date is the current day

    attributes = {
        'installation_date': construction_date,  # Use construction date as installation date
        'expected_lifespan': baseline['expected_lifespan'],
    }
    return attributes

# Utility: Clean None values from graph attributes for GraphML compatibility
def clean_graph_none_values(G):
    """
    Replace None values in node, edge, and graph attributes with empty strings for GraphML compatibility.
    """
    # Clean node attributes
    for n, attrs in G.nodes(data=True):
        for k, v in list(attrs.items()):
            if v is None:
                G.nodes[n][k] = ""
    # Clean edge attributes
    for u, v, attrs in G.edges(data=True):
        for k, val in list(attrs.items()):
            if val is None:
                G.edges[u, v][k] = ""
    # Clean graph-level attributes
    for k, v in list(G.graph.items()):
        if v is None:
            G.graph[k] = ""
    return G

def main():
    """Main function for command-line usage."""
    import argparse
    import datetime
    
    parser = argparse.ArgumentParser(description='Generate random MEP electrical system graphs')
    parser.add_argument('--total_load', type=int, default=1000, help='Total electrical load in kW')
    parser.add_argument('--filename', '-f', type=str, help='Output filename (optional)')
    parser.add_argument('--seed', '-s', type=int, help='Random seed for reproducible results')
    parser.add_argument('--building_length', type=float, default=20.0, help='Building length in meters')
    parser.add_argument('--building_width', type=float, default=20.0, help='Building width in meters')
    parser.add_argument('--num_floors', type=int, default=4, help='Number of floors')
    parser.add_argument('--floor_height', type=float, default=3.5, help='Floor height in meters')
    parser.add_argument('--cluster_strength', type=float, default=0.95, help='Strength of clustering (0.0 = no clustering, 1.0 = full clustering)')
    parser.add_argument('--construction_year', type=int, default=datetime.datetime.now().year, help='Year of building construction')
    parser.add_argument('--construction_date', type=str, default=datetime.datetime.now().strftime("%Y-%m-%d"), help='Construction date in YYYY-MM-DD format (optional)')

    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    building_attributes = {
        "total_load": args.total_load,
        "building_length": args.building_length,
        "building_width": args.building_width,
        "num_floors": args.num_floors,
        "floor_height": args.floor_height,
        "construction_year": args.construction_year,
        "construction_date": args.construction_date
    }


    # --- Generate graph and collect reporting info ---
    # Instead of just the graph, get all intermediate data for reporting
    building_attrs = define_building_characteristics(building_attributes)
    num_risers = determine_number_of_risers(building_attrs)
    riser_locations = locate_risers(building_attrs, num_risers)
    voltage_info = determine_voltage_level(building_attrs)
    floor_loads, end_loads = distribute_loads(building_attrs, voltage_info)
    riser_floor_attributes = determine_riser_attributes(building_attrs, riser_locations, floor_loads, end_loads, voltage_info)
    distribution_equipment = place_distribution_equipment(building_attrs, riser_floor_attributes, voltage_info)
    cluster_strength = args.cluster_strength
    graph = connect_nodes(building_attrs, riser_locations, distribution_equipment, voltage_info, end_loads, cluster_strength)

    # Apply risk scores and RUL to the graph
    graph = apply_risk_scores_to_graph(graph)
    graph = apply_rul_to_graph(graph)

    # --- Reporting ---
    print("\n--- BUILDING MEP GRAPH REPORT ---")
    print(f"Total load: {building_attrs['total_load']} kW")
    print(f"Building size: {building_attrs['building_length']}m x {building_attrs['building_width']}m x {building_attrs['num_floors']} floors (floor height {building_attrs['floor_height']}m)")
    print(f"Number of risers: {num_risers}")
    print(f"Voltage system: {voltage_info['voltage_level']}")
    print(f"Total end loads: {len(end_loads)}")
    # Equipment counts (total)
    eq_counts = {"main_panel": 0, "transformer": 0, "sub_panel": 0}
    for floor, risers in distribution_equipment.items():
        for riser_idx, eq_list in risers.items():
            for eq in eq_list:
                t = eq.get('type')
                if t in eq_counts:
                    eq_counts[t] += 1
    print(f"Main panels: {eq_counts['main_panel']}")
    print(f"Transformers: {eq_counts['transformer']}")
    print(f"Sub-panels: {eq_counts['sub_panel']}")
    # End load breakdown by type (total)
    type_counts = {}
    for e in end_loads:
        t = e['type']
        type_counts[t] = type_counts.get(t, 0) + 1
    print("End load breakdown (total):")
    for t, c in type_counts.items():
        print(f"  {t}: {c}")
    print(f"Graph nodes: {graph.number_of_nodes()} | Graph edges: {graph.number_of_edges()}")

    # --- Per floor and per riser breakdown ---
    print("\n--- Per Floor and Per Riser Breakdown ---")
    for floor in sorted(distribution_equipment.keys()):
        print(f"\nFloor {floor}:")
        risers = distribution_equipment[floor]
        for riser_idx in sorted(risers.keys()):
            eq_list = risers[riser_idx]
            eq_count = {"main_panel": 0, "transformer": 0, "sub_panel": 0}
            for eq in eq_list:
                t = eq.get('type')
                if t in eq_count:
                    eq_count[t] += 1
            print(f"  Riser {riser_idx}: Main panels: {eq_count['main_panel']}, Transformers: {eq_count['transformer']}, Sub-panels: {eq_count['sub_panel']}")
            # End load type/voltage/power breakdown for this riser/floor
            # Use riser_floor_attributes for this
            if floor in riser_floor_attributes and riser_idx in riser_floor_attributes[floor]:
                loads = riser_floor_attributes[floor][riser_idx]
                if loads:
                    print(f"    End loads:")
                    for load_type, vdict in loads.items():
                        for voltage, power in vdict.items():
                            print(f"      {load_type} @ {voltage}V: {round(power,2)} kW")
                else:
                    print(f"    End loads: None")
            else:
                print(f"    End loads: None")
    print("--- END REPORT ---\n")

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    default_filename = f"mep_graph_{timestamp}_seed_{args.seed}_load_{args.total_load}_length_{args.building_length}_width_{args.building_width}_floors_{args.num_floors}_height_{args.floor_height}.mepg"

    filename = args.filename if args.filename else default_filename

    if not filename.endswith('.mepg'):
        filename += '.mepg'
    print(f"Generated MEP graph with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges.")

    output_dir = "graph_outputs/"

    # If output_dir doesn't exist, create it
    import os
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Sanitize graph: replace None attributes with empty string before saving
    graph = clean_graph_none_values(graph)

    # Save the graph in graphml format
    nx.write_graphml(graph, f"{output_dir}{filename}")
    print(f"Graph saved to {output_dir}{filename}")

def generate_mep_graph(building_attributes: Dict[str, Any]) -> nx.DiGraph:
    """
    Framework for generating a random MEP graph based on building attributes.
    Each step is modularized for clarity and future extension.
    """
    # 1. Define building characteristics
    building_attrs = define_building_characteristics(building_attributes)

    # 2. Determine number of vertical risers
    num_risers = determine_number_of_risers(building_attrs)

    # 3. Locate risers within the building
    riser_locations = locate_risers(building_attrs, num_risers)

    # 4. Determine building voltage level
    voltage_info = determine_voltage_level(building_attrs)

    # 5. Distribute loads across the building levels
    floor_loads, end_loads = distribute_loads(building_attrs, voltage_info)

    # 6. Determine riser attributes on each floor
    riser_floor_attributes = determine_riser_attributes(building_attrs, riser_locations, floor_loads, end_loads, voltage_info)

    # 7. Place distribution equipment in each riser on each floor
    distribution_equipment = place_distribution_equipment(building_attrs, riser_floor_attributes, voltage_info)

    # 8. Connect the nodes
    graph = connect_nodes(building_attrs, riser_locations, distribution_equipment, voltage_info, end_loads, 1.0)

    return graph

# --- Framework Function Stubs ---
def define_building_characteristics(building_attributes: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 1: Validate and return building characteristics.
    Ensures all required fields are present and have reasonable values.
    """
    required_fields = [
        'total_load',
        'building_length',
        'building_width',
        'num_floors',
        'floor_height'
    ]
    for field in required_fields:
        if field not in building_attributes:
            raise ValueError(f"Missing required building attribute: {field}")

    # Validate values
    if building_attributes['total_load'] <= 0:
        raise ValueError("Total load must be positive.")
    if building_attributes['building_length'] <= 0 or building_attributes['building_width'] <= 0:
        raise ValueError("Building dimensions must be positive.")
    if building_attributes['num_floors'] < 1:
        raise ValueError("Number of floors must be at least 1.")
    if building_attributes['floor_height'] <= 0:
        raise ValueError("Floor height must be positive.")

    # Optionally, add derived attributes here (e.g., total area)
    building_attributes['total_area'] = building_attributes['building_length'] * building_attributes['building_width'] * building_attributes['num_floors']

    return building_attributes

def determine_number_of_risers(building_attrs: Dict[str, Any]) -> int:
    """
    Step 2: Calculate number of vertical risers needed.
    Uses a rule of thumb: one riser per 500 square meters (minimum 1 riser).
    """
    area_per_floor = building_attrs.get('total_area') / building_attrs.get('num_floors')
    riser_area = 500.0  # square meters per riser
    num_risers = max(1, math.ceil(area_per_floor / riser_area))
    return num_risers

def locate_risers(building_attrs: Dict[str, Any], num_risers: int) -> List[Tuple[float, float]]:
    """
    Step 3: Determine riser locations in the building.
    Risers are equally spaced along the longer dimension (length or width),
    and centered along the shorter dimension, but with some randomness
    to how far they are from the outer edge (not perfectly regular).
    Returns a list of (x, y) tuples.
    """
    length = building_attrs['building_length']
    width = building_attrs['building_width']
    edge_buffer_ratio = 0.1  # up to 10% of the axis can be used as a random buffer from the edge

    if length >= width:
        # Risers spaced along length, centered in width
        spacing = length / (num_risers + 1)
        y_coord = width / 2
        riser_locations = []
        for i in range(num_risers):
            base_x = (i + 1) * spacing
            # Add randomness: offset by up to +/- edge_buffer_ratio*spacing, but keep within building
            max_offset = edge_buffer_ratio * spacing
            offset = random.uniform(-max_offset, max_offset)
            x = min(max(base_x + offset, 0.05 * length), 0.95 * length)
            riser_locations.append((x, y_coord))
    else:
        # Risers spaced along width, centered in length
        spacing = width / (num_risers + 1)
        x_coord = length / 2
        riser_locations = []
        for i in range(num_risers):
            base_y = (i + 1) * spacing
            max_offset = edge_buffer_ratio * spacing
            offset = random.uniform(-max_offset, max_offset)
            y = min(max(base_y + offset, 0.05 * width), 0.95 * width)
            riser_locations.append((x_coord, y))

    return riser_locations

def determine_voltage_level(building_attrs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 4: Determine the complete voltage system for the building based on load.
    Returns voltage system information including available voltages for end loads.
    """
    total_load = building_attrs['total_load']
    
    if total_load <= 288.872:
        return {
            'voltage_3phase': 208,
            'voltage_1phase': 120,
            'voltage_level': '120/208V',
            'primary_voltage': 208,
            'available_voltages': [208, 120],  # End loads can use these voltages
            'high_voltages': [],  # No high voltage in 208V system
            'low_voltages': [208, 120],  # Both are considered "low" voltage
            'needs_step_down': False
        }
    else:
        return {
            'voltage_3phase': 480,
            'voltage_1phase': 277,
            'voltage_level': '277/480V',
            'primary_voltage': 480,
            'available_voltages': [480, 277, 208, 120],  # End loads can use any of these
            'high_voltages': [480, 277],  # High voltage side of system
            'low_voltages': [208, 120],   # Low voltage side (requires step-down)
            'needs_step_down': True
        }

def distribute_loads(building_attrs: Dict[str, Any], voltage_info: Dict[str, Any], variation: float = 0.1) -> Tuple[List[float], List[Dict[str, Any]]]:
    """
    Step 5: Distribute loads across floors and assign end loads.
    - Split total load across floors with ±variation (default 10%), sum matches total.
    - Assign end loads (lighting, receptacles, hvac) to each floor.
    - Each end load type has a power rating.
    - All floor load is distributed among end loads to ensure total matches exactly.
    Returns: (floor_loads, end_loads)
    """
    total_load = building_attrs['total_load']
    num_floors = building_attrs['num_floors']
    end_load_types = [
        {"type": "lighting", "power": 1.5},
        {"type": "receptacles", "power": 2.0},
        {"type": "hvac", "power": 3.0},
        # {"type": "kitchen", "power": 4.0},
        # {"type": "specialty", "power": 2.5}
    ]
    # 1. Distribute total load across floors with ±variation
    avg_load = total_load / num_floors
    floor_loads = []
    for i in range(num_floors):
        floor_var = random.uniform(-variation, variation)
        floor_load = avg_load * (1 + floor_var)
        floor_loads.append(floor_load)
    # Normalize so sum matches total_load
    scale = total_load / sum(floor_loads)
    floor_loads = [fl * scale for fl in floor_loads]

    print(f"Distributed floor loads: {floor_loads} (scaled to match total load {total_load})")

    # Set bounds for end load type percentages of total floor load
    minimum_end_load_percentage = 0.05  # Minimum 5% of floor load
    maximum_end_load_percentage = 0.5  # Maximum 50% of floor load

    # 2. Assign end loads to each floor
    end_loads = []
    for floor_idx, floor_load in enumerate(floor_loads):
        type_loads = {t["type"]: 0.0 for t in end_load_types}
        
        # Determine a breakdown of end loads for this floor
        load_type_count = len(end_load_types)
        percent_left = 1.0

        # Assume all load types are present on each floor
        for index, end_load_type in enumerate(end_load_types):
            # Randomly determine how much of the floor load this type will take
            if index == load_type_count - 1:  # Last type takes all remaining load
                load_percentage = percent_left
            else:
                # Ensure we don't exceed the maximum percentage for remaining load types
                max_percentage = min(maximum_end_load_percentage, 
                                   percent_left - (load_type_count - index - 1) * minimum_end_load_percentage)
                load_percentage = random.uniform(minimum_end_load_percentage, max_percentage)
            
            load_power = floor_load * load_percentage
            percent_left -= load_percentage

            # Create end load entries - split the total power for this type across multiple individual loads
            # Each individual load has the base power rating from end_load_types
            individual_load_power = end_load_type["power"]
            num_individual_loads = max(1, int(round(load_power / individual_load_power)))
            actual_individual_power = load_power / num_individual_loads
            
            for load_idx in range(num_individual_loads):
                end_load_entry = {
                    "floor": floor_idx,
                    "type": end_load_type["type"],
                    "power": actual_individual_power,
                    "voltage": random.choice(voltage_info['available_voltages'])  # Randomly assign voltage from available voltages
                }
                end_loads.append(end_load_entry)
            
            type_loads[end_load_type["type"]] += load_power
            
        # Ensure total load matches floor load (within tolerance)
        total_type_load = sum(type_loads.values())
        if abs(total_type_load - floor_load) > 0.01:
            raise ValueError(f"Total end load power for floor {floor_idx} does not match floor load: {total_type_load:.3f} != {floor_load:.3f}")

    return floor_loads, end_loads

def determine_riser_attributes(building_attrs: Dict[str, Any], riser_locations: List[Tuple[float, float]], floor_loads: List[float], end_loads: List[Dict[str, Any]], voltage_info: Dict[str, Any]) -> Dict:
    """
    Step 6: Determine riser attributes on each floor.
    For each floor, assign each end load to the nearest riser (by x/y distance).
    For each riser on each floor, summarize the total power per end load type and voltage.
    Returns a nested dict: {floor: {riser_idx: {type: {voltage: total_power}}}}
    """
    RISER_EQUIPMENT_AREA_SIZE = 2.0  # meters (change this value to adjust riser equipment area size)
    num_floors = building_attrs['num_floors']
    riser_attrs = {floor: {r: {} for r in range(len(riser_locations))} for floor in range(num_floors)}

    # Generate riser bounds: for each riser, a square centered at riser location
    riser_bounds = []  # List of (xmin, xmax, ymin, ymax) for each riser
    half_area = RISER_EQUIPMENT_AREA_SIZE / 2.0
    for rx, ry in riser_locations:
        xmin = rx - half_area
        xmax = rx + half_area
        ymin = ry - half_area
        ymax = ry + half_area
        riser_bounds.append((xmin, xmax, ymin, ymax))

    # Helper: find nearest riser index for a given (x, y)
    def nearest_riser_idx(x, y):
        dists = [math.hypot(x - rx, y - ry) for rx, ry in riser_locations]
        return dists.index(min(dists))

    # For each end load, assign to nearest riser (randomly distributed along the main axis)
    for end_load in end_loads:
        floor = end_load['floor']
        # For simplicity, randomly assign x/y within building for each end load
        length = building_attrs['building_length']
        width = building_attrs['building_width']
        x = random.uniform(0, length)
        y = random.uniform(0, width)
        riser_idx = nearest_riser_idx(x, y)
        t = end_load['type']
        v = end_load['voltage']
        p = end_load['power']
        # Initialize nested dicts
        if t not in riser_attrs[floor][riser_idx]:
            riser_attrs[floor][riser_idx][t] = {}
        if v not in riser_attrs[floor][riser_idx][t]:
            riser_attrs[floor][riser_idx][t][v] = 0.0
        riser_attrs[floor][riser_idx][t][v] += p

    # Attach riser_bounds to riser_attrs for use in equipment placement
    riser_attrs['_riser_bounds'] = riser_bounds
    return riser_attrs

def place_distribution_equipment(building_attrs: Dict[str, Any], riser_floor_attributes: Dict, voltage_info: Dict[str, Any]) -> Dict:
    """
    Step 7: Place distribution equipment in each riser on each floor.
    Uses the voltage system information to determine equipment placement strategy.
    """
    RISER_EQUIPMENT_AREA_SIZE = 6.0  # meters (should match value in determine_riser_attributes)
    equipment = {}
    primary_voltage = voltage_info['primary_voltage']
    needs_step_down = voltage_info['needs_step_down']
    high_voltages = voltage_info['high_voltages']
    low_voltages = voltage_info['low_voltages']
    riser_bounds = riser_floor_attributes.get('_riser_bounds', None)
    half_area = RISER_EQUIPMENT_AREA_SIZE / 2.0

    def unique_xy(riser_idx, used_positions):
        if riser_bounds:
            xmin, xmax, ymin, ymax = riser_bounds[riser_idx]
        else:
            xmin, xmax, ymin, ymax = -half_area, half_area, -half_area, half_area
        for _ in range(100):
            x = random.uniform(xmin, xmax)
            y = random.uniform(ymin, ymax)
            pos = (round(x, 3), round(y, 3))
            if pos not in used_positions:
                used_positions.add(pos)
                return x, y
        return xmin, ymin

    def add_panel(equipment_list, panel_type, voltage, load_type, power, parent, riser_idx, used_positions):
        x, y = unique_xy(riser_idx, used_positions)
        panel = {
            "type": panel_type,
            "voltage": voltage,
            "load_type": load_type,
            "power": power,
            "parent": parent,
            "x": x,
            "y": y
        }
        equipment_list.append(panel)

    def add_transformer(equipment_list, primary_voltage, secondary_voltage, load_type, power, parent, riser_idx, used_positions):
        x, y = unique_xy(riser_idx, used_positions)
        transformer = {
            "type": "transformer",
            "primary_voltage": primary_voltage,
            "secondary_voltage": secondary_voltage,
            "load_type": load_type,
            "power": power,
            "parent": parent,
            "x": x,
            "y": y
        }
        equipment_list.append(transformer)

    for floor, risers in riser_floor_attributes.items():
        if floor == '_riser_bounds':
            continue
        equipment[floor] = {}
        for riser_idx, load_types in risers.items():
            riser_equipment = []
            used_positions = set()
            # Always add a main distribution panel at the building's primary voltage
            x, y = unique_xy(riser_idx, used_positions)
            riser_equipment.append({
                "type": "main_panel",
                "voltage": primary_voltage,
                "loads": load_types,
                "x": x,
                "y": y
            })

            # Use flexible logic based on voltage system
            for load_type, vdict in load_types.items():
                if needs_step_down:
                    # For systems that need step-down (like 480V systems)
                    high_v_power = sum(p for v, p in vdict.items() if v in high_voltages)
                    low_v_power = sum(p for v, p in vdict.items() if v in low_voltages)
                    
                    if high_v_power > 0 and low_v_power > 0:
                        # Need both high voltage sub-panel and step-down for low voltage
                        add_panel(riser_equipment, "sub_panel", primary_voltage, load_type, high_v_power, "main_panel", riser_idx, used_positions)
                        add_transformer(riser_equipment, primary_voltage, low_voltages[0], load_type, low_v_power, f"sub_panel_{primary_voltage}_{load_type}", riser_idx, used_positions)
                        add_panel(riser_equipment, "sub_panel", low_voltages[0], load_type, low_v_power, f"transformer_{low_voltages[0]}_{load_type}", riser_idx, used_positions)
                    elif high_v_power > 0:
                        # Only high voltage loads
                        add_panel(riser_equipment, "sub_panel", primary_voltage, load_type, high_v_power, "main_panel", riser_idx, used_positions)
                    elif low_v_power > 0:
                        # Only low voltage loads, need step-down from main
                        add_transformer(riser_equipment, primary_voltage, low_voltages[0], load_type, low_v_power, "main_panel", riser_idx, used_positions)
                        add_panel(riser_equipment, "sub_panel", low_voltages[0], load_type, low_v_power, f"transformer_{low_voltages[0]}_{load_type}", riser_idx, used_positions)
                else:
                    # For systems that don't need step-down (like 208V systems)
                    # Create sub-panels for each load type, using the appropriate voltage for that load type
                    total_power = sum(vdict.values())
                    if total_power > 0:
                        # Determine the voltage to use for this load type's sub-panel
                        # Use the highest voltage available for this load type
                        load_voltage = max(vdict.keys())
                        add_panel(riser_equipment, "sub_panel", load_voltage, load_type, total_power, "main_panel", riser_idx, used_positions)
            
            equipment[floor][riser_idx] = riser_equipment
    return equipment

def connect_nodes(building_attrs: Dict[str, Any], riser_locations: List[Tuple[float, float]], distribution_equipment: Dict, voltage_info: Dict[str, Any], end_loads: list, cluster_strength: float = 1.0) -> nx.DiGraph:
    """
    Step 8: Connect all nodes to form the final graph.
    Framework only: placeholder functions for each connection step.
    """
    G = nx.DiGraph()

    # 1. Add utility transformer node
    add_utility_transformer(G, building_attrs)

    # 2. Add all distribution equipment nodes (main panels, transformers, sub-panels, etc.)
    add_distribution_equipment_nodes(G, distribution_equipment, riser_locations, building_attrs)

    # 3. Connect utility transformer to the nearest main panel on the ground floor
    connect_utility_to_main_panel(G, distribution_equipment, riser_locations)

    # 4. Connect main panels vertically in each riser
    connect_main_panels_vertically(G, distribution_equipment)

    # 5. Connect equipment within each riser/floor (main panel → transformer → sub-panel, etc.)
    connect_equipment_hierarchy(G, distribution_equipment)

    # 6. Add end load nodes and connect them to the appropriate equipment
    add_and_connect_end_loads(G, distribution_equipment, building_attrs, end_loads, cluster_strength)

    # 7. Propagate the power loads through the graph from the end loads to the utility transformer
    propagate_power_loads(G, distribution_equipment)

    # 8. Calculate the amperage for each node based on the power
    calculate_amperage(G, voltage_info)

    # 9. Size the equipment based on the calculated amperage
    size_equipment(G)

    # 10. Add metadata about the building and graph
    G.graph['building_length'] = building_attrs['building_length']
    G.graph['building_width'] = building_attrs['building_width']
    G.graph['num_floors'] = building_attrs['num_floors']
    G.graph['floor_height'] = building_attrs['floor_height']
    G.graph['total_load'] = building_attrs['total_load']
    G.graph['voltage_level'] = voltage_info['voltage_level']
    G.graph['construction_year'] = building_attrs.get('construction_year')
    G.graph['timestamp'] = datetime.datetime.now().isoformat()
    G.graph['seed'] = str(random.getstate())  # Optionally store as string, or remove entirely
    G.graph['description'] = "Randomly generated MEP electrical system graph"
    G.graph['construction_date'] = building_attrs.get('construction_date')

    # --- Update 'parent' attribute for all nodes ---
    for node in G.nodes:
        preds = list(G.predecessors(node))
        if preds:
            # If multiple parents, just take the first (can be adjusted if needed)
            G.nodes[node]['parent'] = preds[0]
        else:
            G.nodes[node]['parent'] = ''

    return G

# --- Placeholder functions for graph construction ---
def add_utility_transformer(G, building_attrs):
    """Add the utility transformer node to the graph, placed outside the building footprint."""
    length = building_attrs['building_length']
    width = building_attrs['building_width']
    floor_height = building_attrs['floor_height']
    num_floors = building_attrs['num_floors']
    construction_year = building_attrs.get('construction_year')
    construction_date = building_attrs.get('construction_date')
    
    # Place transformer outside the building, near the main entrance (assume at x = -5, y = width/2, z = 0)
    x = -5.0
    y = width / 2.0
    z = 0.0
    node_id = create_abbreviated_node_id('utility_transformer')
    full_name = create_full_node_id('utility_transformer')
    
    # Get baseline attributes for new utility transformer
    baseline_attrs = get_baseline_attributes('utility_transformer', building_attrs)
    
    G.add_node(
        node_id,
        type="utility_transformer",
        full_name=full_name,
        x=x,
        y=y,
        z=z,
        description="Utility transformer located outside the building footprint",
        **baseline_attrs
    )

def add_distribution_equipment_nodes(G, distribution_equipment, riser_locations, building_attrs):
    """Add all distribution equipment nodes to the graph with unique IDs and coordinates."""

    for floor, risers in distribution_equipment.items():
        for riser_idx, equipment_list in risers.items():
            # Use x/y from equipment dict if present, else fallback to riser_locations
            z = floor * G.graph.get('floor_height', 3.5)
            for eq_idx, eq in enumerate(equipment_list):
                eq_type = eq.get('type', 'equipment')
                voltage = eq.get('voltage', '')
                load_type = eq.get('load_type', '')
                
                # Use x/y from equipment dict if present, else fallback
                x = eq.get('x', None)
                y = eq.get('y', None)
                if x is None or y is None:
                    x, y = riser_locations[riser_idx]
                
                # Get baseline attributes for this equipment type
                baseline_attrs = get_baseline_attributes(eq_type, building_attrs)
                # Compute full_name for all node types
                if eq_type == 'transformer':
                    secondary_voltage = eq.get('secondary_voltage', '')
                    node_id = create_abbreviated_node_id('transformer', floor, riser_idx, voltage, load_type, secondary_voltage)
                    full_name = create_full_node_id('transformer', floor, riser_idx, voltage, load_type, secondary_voltage)
                    # Add all transformer attributes
                    G.add_node(
                        node_id,
                        type=eq_type,
                        full_name=full_name,
                        floor=floor,
                        riser=riser_idx,
                        primary_voltage=eq.get('primary_voltage',''),
                        secondary_voltage=secondary_voltage,
                        load_type=load_type,
                        power=eq.get('power',0.0),
                        parent=eq.get('parent',''),
                        x=x,
                        y=y,
                        z=z,
                        **baseline_attrs
                    )
                elif eq_type == 'sub_panel':
                    node_id = create_abbreviated_node_id('sub_panel', floor, riser_idx, voltage, load_type)
                    full_name = create_full_node_id('sub_panel', floor, riser_idx, voltage, load_type)
                    G.add_node(
                        node_id,
                        type=eq_type,
                        full_name=full_name,
                        floor=floor,
                        riser=riser_idx,
                        voltage=voltage,
                        load_type=load_type,
                        power=eq.get('power',0.0),
                        parent=eq.get('parent',''),
                        x=x,
                        y=y,
                        z=z,
                        **baseline_attrs
                    )
                else:
                    node_id = create_abbreviated_node_id(eq_type, floor, riser_idx, voltage, load_type)
                    full_name = create_full_node_id(eq_type, floor, riser_idx, voltage, load_type)
                    # Remove x/y from eq dict to avoid duplicate keys
                    eq_clean = {k: v for k, v in eq.items() if k not in ['type', 'voltage', 'loads', 'load_type', 'x', 'y']}
                    G.add_node(
                        node_id,
                        type=eq_type,
                        full_name=full_name,
                        floor=floor,
                        riser=riser_idx,
                        voltage=voltage,
                        x=x,
                        y=y,
                        z=z,
                        **baseline_attrs,
                        **eq_clean
                    )

def connect_utility_to_main_panel(G, distribution_equipment, riser_locations):
    """Connect the utility transformer to the nearest main panel on the ground floor."""
    # Find all main panels on the ground floor (floor 0)
    ground_floor = 0
    main_panel_nodes = []
    for riser_idx, equipment_list in distribution_equipment.get(ground_floor, {}).items():
        for eq in equipment_list:
            if eq.get('type') == 'main_panel':
                node_id = create_abbreviated_node_id('main_panel', ground_floor, riser_idx, eq.get('voltage', ''))
                main_panel_nodes.append((node_id, riser_idx))
    if not main_panel_nodes:
        return
    # Get utility transformer coordinates
    util_node_id = create_abbreviated_node_id('utility_transformer')
    util_x = G.nodes[util_node_id]['x']
    util_y = G.nodes[util_node_id]['y']
    # Find nearest main panel
    min_dist = float('inf')
    nearest_node = None
    for node_id, riser_idx in main_panel_nodes:
        x, y = riser_locations[riser_idx]
        dist = math.hypot(util_x - x, util_y - y)
        if dist < min_dist:
            min_dist = dist
            nearest_node = node_id
    if nearest_node:
        G.add_edge(util_node_id, nearest_node, description='Utility to main panel connection')

def connect_main_panels_vertically(G, distribution_equipment):
    """Connect main panels vertically in each riser."""
    # For each riser, connect all main panels on upper floors to the main panel on the first (ground) floor
    if not distribution_equipment:
        return
    floors = sorted(distribution_equipment.keys())  # ascending: 0 (ground) up
    if not floors:
        return
    riser_indices = set()
    for risers in distribution_equipment.values():
        riser_indices.update(risers.keys())
    for riser_idx in riser_indices:
        # Find the main panel node id for the ground floor (floor 0)
        ground_floor = 0
        ground_panel_id = None
        eq_list = distribution_equipment.get(ground_floor, {}).get(riser_idx, [])
        for eq in eq_list:
            if eq.get('type') == 'main_panel':
                ground_panel_id = create_abbreviated_node_id('main_panel', ground_floor, riser_idx, eq.get('voltage', ''))
                break
        if not ground_panel_id:
            continue
        # For all upper floors, connect their main panels to the ground floor main panel
        for floor in floors:
            if floor == ground_floor:
                continue
            eq_list = distribution_equipment.get(floor, {}).get(riser_idx, [])
            for eq in eq_list:
                if eq.get('type') == 'main_panel':
                    upper_panel_id = create_abbreviated_node_id('main_panel', floor, riser_idx, eq.get('voltage', ''))
                    G.add_edge(ground_panel_id, upper_panel_id, description='Main panel feed from ground floor')

def connect_equipment_hierarchy(G, distribution_equipment):
    """Connect equipment within each riser/floor (main panel → transformer → sub-panel, etc.)."""
    # For each floor and riser, connect each equipment node to its parent using the parent field
    for floor, risers in distribution_equipment.items():
        for riser_idx, equipment_list in risers.items():
            # Build a mapping from logical parent names to node IDs for this riser/floor
            node_id_map = {}
            for eq in equipment_list:
                eq_type = eq.get('type')
                voltage = eq.get('voltage', '')
                load_type = eq.get('load_type', '')
                secondary_voltage = eq.get('secondary_voltage', '')
                
                if eq_type == 'main_panel':
                    node_id = create_abbreviated_node_id('main_panel', floor, riser_idx, voltage)
                    node_id_map['main_panel'] = node_id
                elif eq_type == 'sub_panel':
                    node_id = create_abbreviated_node_id('sub_panel', floor, riser_idx, voltage, load_type)
                    if voltage == 480:
                        node_id_map[f"sub_panel_480_{load_type}"] = node_id
                    elif voltage == 208:
                        node_id_map[f"sub_panel_208_{load_type}"] = node_id
                    # Add for other voltages if needed
                elif eq_type == 'transformer':
                    node_id = create_abbreviated_node_id('transformer', floor, riser_idx, voltage, load_type, secondary_voltage)
                    node_id_map[f"transformer_{secondary_voltage}_{load_type}"] = node_id
            
            # Now connect each node to its parent using the parent field
            for eq in equipment_list:
                eq_type = eq.get('type')
                voltage = eq.get('voltage', '')
                load_type = eq.get('load_type', '')
                secondary_voltage = eq.get('secondary_voltage', '')
                parent_key = eq.get('parent', None)
                
                # Determine this node's ID
                if eq_type == 'main_panel':
                    node_id = create_abbreviated_node_id('main_panel', floor, riser_idx, voltage)
                elif eq_type == 'sub_panel':
                    node_id = create_abbreviated_node_id('sub_panel', floor, riser_idx, voltage, load_type)
                elif eq_type == 'transformer':
                    node_id = create_abbreviated_node_id('transformer', floor, riser_idx, voltage, load_type, secondary_voltage)
                else:
                    continue
                
                # Connect to parent if parent_key is in map
                if parent_key and parent_key in node_id_map:
                    parent_id = node_id_map[parent_key]
                    G.add_edge(parent_id, node_id, description=f'{parent_key} to {eq_type}')

def add_and_connect_end_loads(G, distribution_equipment, building_attrs, end_loads, cluster_strength=1.0):
    """Add end load nodes and connect them to the appropriate equipment, with clustering control."""
    import math
    from collections import defaultdict
    num_floors = building_attrs['num_floors']
    floor_height = building_attrs['floor_height']
    building_length = building_attrs['building_length']
    building_width = building_attrs['building_width']

    # Build a mapping: (floor, riser, load_type, voltage) -> list of end loads
    # To assign end loads to risers, use the same logic as determine_riser_attributes
    riser_locations = []
    for floor, risers in distribution_equipment.items():
        for riser_idx in risers.keys():
            if len(riser_locations) <= riser_idx:
                riser_locations.extend([None] * (riser_idx - len(riser_locations) + 1))
    # Try to get riser_locations from the first main_panel/sub_panel node
    for risers in distribution_equipment.values():
        for riser_idx, eq_list in risers.items():
            for eq in eq_list:
                if eq.get('x') is not None and eq.get('y') is not None:
                    riser_locations[riser_idx] = (eq['x'], eq['y'])
                    break

    def nearest_riser_idx(x, y):
        dists = [math.hypot(x - rx, y - ry) if rx is not None and ry is not None else float('inf') for rx, ry in riser_locations]
        return dists.index(min(dists))

    # Helper function to map load voltage to panel voltage
    def get_panel_voltage_for_load(load_voltage):
        """Map load voltage to the appropriate panel voltage that can serve it."""
        if load_voltage == 120:
            return 208  # 120V loads connect to 208V panels
        elif load_voltage == 277:
            return 480  # 277V loads connect to 480V panels
        else:
            return load_voltage  # 208V and 480V loads connect to panels of same voltage

    group_map = defaultdict(list)
    for end_load in end_loads:
        floor = end_load['floor']
        length = building_attrs['building_length']
        width = building_attrs['building_width']
        x = random.uniform(0, length)
        y = random.uniform(0, width)
        riser_idx = nearest_riser_idx(x, y)
        t = end_load['type']
        v = end_load['voltage']
        # Map load voltage to the panel voltage that can serve it
        panel_voltage = get_panel_voltage_for_load(v)
        group_map[(floor, riser_idx, t, panel_voltage)].append({'power': end_load['power'], 'x': x, 'y': y, 'load_voltage': v})

    for floor, risers in distribution_equipment.items():
        for riser_idx, equipment_list in risers.items():
            sub_panel_map = {}
            main_panel_id = None
            created_nodes = set()
            for eq in equipment_list:
                eq_type = eq.get('type')
                voltage = eq.get('voltage', '')
                load_type = eq.get('load_type','')
                if eq_type == 'sub_panel':
                    node_id = create_abbreviated_node_id('sub_panel', floor, riser_idx, voltage, load_type)
                    if node_id not in created_nodes:
                        sub_panel_map[(load_type, voltage)] = node_id
                        created_nodes.add(node_id)
                elif eq_type == 'main_panel':
                    main_panel_id = create_abbreviated_node_id('main_panel', floor, riser_idx, voltage)

            # For each sub-panel, add clustered end loads for its type/panel_voltage
            for (load_type, panel_voltage), sub_panel_id in sub_panel_map.items():
                group = group_map.get((floor, riser_idx, load_type, panel_voltage), [])
                N = len(group)
                if N == 0:
                    continue
                num_clusters = max(1, int(round((1 - cluster_strength) * N + cluster_strength * 1)))
                # Split group into clusters
                if num_clusters == 1:
                    total_power = sum(e['power'] for e in group)
                    # Use the original load voltage (not panel voltage) for the end load node
                    load_voltage = group[0]['load_voltage'] if group else panel_voltage
                    x = random.uniform(0, building_length)
                    y = random.uniform(0, building_width)
                    z = floor * floor_height
                    end_load_id = create_abbreviated_node_id('end_load', floor, riser_idx, load_voltage, load_type)
                    full_name = create_full_node_id('end_load', floor, riser_idx, load_voltage, load_type)
                    if end_load_id not in created_nodes:
                        # Get baseline attributes for end load
                        baseline_attrs = get_baseline_attributes('end_load', building_attrs)
                        
                        G.add_node(
                            end_load_id,
                            type='end_load',
                            full_name=full_name,
                            floor=floor,
                            riser=riser_idx,
                            load_type=load_type,
                            voltage=load_voltage,  # Use original load voltage
                            x=x,
                            y=y,
                            z=z,
                            power=round(total_power, 2),
                            **baseline_attrs
                        )
                        created_nodes.add(end_load_id)
                    G.add_edge(sub_panel_id, end_load_id, description='Sub-panel to end load')
                else:
                    # Shuffle group for random clusters
                    random.shuffle(group)
                    cluster_size = int(math.ceil(N / num_clusters))
                    for i in range(num_clusters):
                        cluster = group[i*cluster_size:(i+1)*cluster_size]
                        if not cluster:
                            continue
                        total_power = sum(e['power'] for e in cluster)
                        # Use the original load voltage from the first item in cluster
                        load_voltage = cluster[0]['load_voltage']
                        # Use mean x/y for cluster
                        x = sum(e['x'] for e in cluster) / len(cluster)
                        y = sum(e['y'] for e in cluster) / len(cluster)
                        z = floor * floor_height
                        end_load_id = create_abbreviated_node_id('end_load', floor, riser_idx, load_voltage, load_type, cluster_id=i)
                        full_name = create_full_node_id('end_load', floor, riser_idx, load_voltage, load_type, cluster_id=i)
                        if end_load_id not in created_nodes:
                            # Get baseline attributes for end load
                            baseline_attrs = get_baseline_attributes('end_load', building_attrs)
                            
                            G.add_node(
                                end_load_id,
                                type='end_load',
                                full_name=full_name,
                                floor=floor,
                                riser=riser_idx,
                                load_type=load_type,
                                voltage=load_voltage,  # Use original load voltage
                                x=x,
                                y=y,
                                z=z,
                                power=round(total_power, 2),
                                **baseline_attrs
                            )
                            created_nodes.add(end_load_id)
                        G.add_edge(sub_panel_id, end_load_id, description='Sub-panel to end load')

            # If no sub-panels, connect clustered end loads directly to main panel (for main voltage)
            if not sub_panel_map and main_panel_id:
                main_voltage = None
                main_loads = None
                for eq in equipment_list:
                    if eq.get('type') == 'main_panel':
                        main_voltage = eq.get('voltage', '')
                        main_loads = eq.get('loads', {})
                        break
                if main_loads:
                    for load_type, vdict in main_loads.items():
                        # Check if main panel voltage can serve any loads for this load type
                        group = group_map.get((floor, riser_idx, load_type, main_voltage), [])
                        N = len(group)
                        if N == 0:
                            continue
                        num_clusters = max(1, int(round((1 - cluster_strength) * N + cluster_strength * 1)))
                        if num_clusters == 1:
                            total_power = sum(e['power'] for e in group)
                            # Use the original load voltage (not main panel voltage) for the end load node
                            load_voltage = group[0]['load_voltage'] if group else main_voltage
                            x = random.uniform(0, building_length)
                            y = random.uniform(0, building_width)
                            z = floor * floor_height
                            end_load_id = create_abbreviated_node_id('end_load', floor, riser_idx, load_voltage, load_type)
                            full_name = create_full_node_id('end_load', floor, riser_idx, load_voltage, load_type)
                            if end_load_id not in created_nodes:
                                baseline_attrs = get_baseline_attributes('end_load', building_attrs)
                                G.add_node(
                                    end_load_id,
                                    type='end_load',
                                    full_name=full_name,
                                    floor=floor,
                                    riser=riser_idx,
                                    load_type=load_type,
                                    voltage=load_voltage,  # Use original load voltage
                                    x=x,
                                    y=y,
                                    z=z,
                                    power=round(total_power, 2),
                                    **baseline_attrs
                                )
                                created_nodes.add(end_load_id)
                            G.add_edge(main_panel_id, end_load_id, description='Main panel to end load')
                        else:
                            random.shuffle(group)
                            cluster_size = int(math.ceil(N / num_clusters))
                            for i in range(num_clusters):
                                cluster = group[i*cluster_size:(i+1)*cluster_size]
                                if not cluster:
                                    continue
                                total_power = sum(e['power'] for e in cluster)
                                # Use the original load voltage from the first item in cluster
                                load_voltage = cluster[0]['load_voltage']
                                x = sum(e['x'] for e in cluster) / len(cluster)
                                y = sum(e['y'] for e in cluster) / len(cluster)
                                z = floor * floor_height
                                end_load_id = create_abbreviated_node_id('end_load', floor, riser_idx, load_voltage, load_type, cluster_id=i)
                                full_name = create_full_node_id('end_load', floor, riser_idx, load_voltage, load_type, cluster_id=i)
                                if end_load_id not in created_nodes:
                                    baseline_attrs = get_baseline_attributes('end_load', building_attrs)
                                    G.add_node(
                                        end_load_id,
                                        type='end_load',
                                        full_name=full_name,
                                        floor=floor,
                                        riser=riser_idx,
                                        load_type=load_type,
                                        voltage=load_voltage,  # Use original load voltage
                                        x=x,
                                        y=y,
                                        z=z,
                                        power=round(total_power, 2),
                                        **baseline_attrs
                                    )
                                    created_nodes.add(end_load_id)
                                G.add_edge(main_panel_id, end_load_id, description='Main panel to end load')

def propagate_power_loads(G: nx.DiGraph, distribution_equipment: Dict[str, Any]) -> None:

    """
    Step 9: Propagate the power loads through the graph from the end loads to the utility transformer.
    For each node, calculate the total downstream power (sum of all end loads it serves).
    Adds a 'propagated_power' attribute to each node.
    """
    # 1. Initialize propagated_power to 0 for all nodes
    for n in G.nodes:
        G.nodes[n]['propagated_power'] = 0.0

    # 2. Set propagated_power for end loads to their own power
    end_load_nodes = [n for n, d in G.nodes(data=True) if d.get('type') == 'end_load']
    for n in end_load_nodes:
        G.nodes[n]['propagated_power'] = G.nodes[n].get('power', 0.0)

    # 3. Traverse in reverse topological order (leaves to root)
    try:
        topo_order = list(nx.topological_sort(G))
    except nx.NetworkXUnfeasible:
        # Not a DAG, skip propagation
        return
    for n in reversed(topo_order):
        node_power = G.nodes[n].get('propagated_power', 0.0)
        for pred in G.predecessors(n):
            G.nodes[pred]['propagated_power'] += node_power

def calculate_amperage(G: nx.DiGraph, voltage_info: Dict[str, Any]) -> None:
    """
    Step 10: Calculate the amperage for each node based on the power and voltage.
    For transformers, add both primary and secondary amperage.
    """
    import math

    def is_three_phase(voltage):
        # Three-phase voltage is the primary 3-phase voltage of the system
        return voltage == voltage_info['voltage_3phase']

    def calc_amperage(power_kw, voltage):
        if not voltage or voltage == 0:
            return 0.0
        power_w = power_kw * 1000.0
        if is_three_phase(voltage):
            return power_w / (float(voltage) * math.sqrt(3))
        else:
            return power_w / float(voltage)

    for n, d in G.nodes(data=True):
        # Transformers: calculate both primary and secondary amperage
        if d.get('type') == 'transformer':
            power = d.get('propagated_power', d.get('power', 0.0))
            from_v = d.get('primary_voltage', None)
            to_v = d.get('secondary_voltage', None)
            # Primary (upstream)
            if from_v:
                G.nodes[n]['primary_amperage'] = calc_amperage(power, from_v)
            # Secondary (downstream)
            if to_v:
                G.nodes[n]['secondary_amperage'] = calc_amperage(power, to_v)
        else:
            # For all other nodes with voltage and propagated_power
            voltage = d.get('voltage', None)
            power = d.get('propagated_power', d.get('power', 0.0))
            if voltage and power:
                G.nodes[n]['amperage'] = calc_amperage(power, voltage)

def size_equipment(G: nx.DiGraph) -> None:
    """
    Step 11: Size the equipment based on the calculated amperage.
    For each node, determine the appropriate equipment size based on amperage.
    Adds a 'size' attribute to each node.
    Use STANDARD_DISTRIBUTION_EQUIPMENT_SIZES constant for sizing.
    Assume the standard sizes are 80% rated
    """
    for n, d in G.nodes(data=True):
        if 'panel' in d.get('type'):
            amperage = d.get('amperage', 0.0)
            if amperage > 0:
                # Example sizing logic: round up to nearest 10A
                standard_sizes_sorted = sorted(STANDARD_DISTRIBUTION_EQUIPMENT_SIZES)

                d['amperage_rating'] = standard_sizes_sorted[-1]  # Default to largest size if no match found
                # Find the appropriate size based on amperage
                # Use 80% of the size as the threshold for sizing
                for size in standard_sizes_sorted:
                    if amperage <= size * 0.8:  # Check if 80% of the size is greater than or equal to the amperage
                        d['amperage_rating'] = size
                        break
                
                # Get index of the size in the original list
                size_index = STANDARD_DISTRIBUTION_EQUIPMENT_SIZES.index(d['amperage_rating'])
                # Get cost from the standard costs
                d['replacement_cost'] = STANDARD_DISTRIBUTION_EQUIPMENT_COSTS[size_index]

                # Use MAXIMUM_PANEL_SIZE to determine if the node is a panel or switchboard
                if d['amperage_rating'] > MAXIMUM_PANEL_SIZE:
                    d['type'] = 'switchboard'
                else:
                    d['type'] = 'panel'
        elif 'transformer' in d.get('type'):
            power = d.get('propagated_power', d.get('power', 0.0))

            standard_sizes_sorted = sorted(STANDARD_TRANSFORMER_SIZES)
            d['power_rating'] = standard_sizes_sorted[-1]  # Default to largest size

            # Find the appropriate size based on power
            for size in standard_sizes_sorted:
                if power <= size * 0.8:
                    d['power_rating'] = size
                    break

            # Get index of the size in the original list
            size_index = STANDARD_TRANSFORMER_SIZES.index(d['power_rating'])
            # Get cost from the standard costs
            d['replacement_cost'] = STANDARD_TRANSFORMER_COSTS[size_index]

if __name__ == "__main__":
    main()