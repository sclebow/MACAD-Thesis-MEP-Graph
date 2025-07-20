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

def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate random MEP electrical system graphs')
    parser.add_argument('--total_load', type=int, default=1000, help='Total electrical load in kW')
    parser.add_argument('--filename', '-f', type=str, help='Output filename (optional)')
    parser.add_argument('--seed', '-s', type=int, help='Random seed for reproducible results')
    parser.add_argument('--building-length', type=float, default=20.0, help='Building length in meters')
    parser.add_argument('--building-width', type=float, default=20.0, help='Building width in meters')
    parser.add_argument('--num-floors', type=int, default=4, help='Number of floors')
    parser.add_argument('--floor-height', type=float, default=3.5, help='Floor height in meters')
    
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    building_attributes = {
        "total_load": args.total_load,
        "building_length": args.building_length,
        "building_width": args.building_width,
        "num_floors": args.num_floors,
        "floor_height": args.floor_height
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
    graph = connect_nodes(building_attrs, riser_locations, distribution_equipment, voltage_info)

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
    graph = connect_nodes(building_attrs, riser_locations, distribution_equipment, voltage_info)

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
    Step 4: Determine voltage level based on total load.
    """
    total_load = building_attrs['total_load']
    if total_load <= 288.872:
        return {'voltage_3phase': 208, 'voltage_1phase': 120, 'voltage_level': '120/208V'}
    else:
        return {'voltage_3phase': 480, 'voltage_1phase': 277, 'voltage_level': '277/480V'}

def distribute_loads(building_attrs: Dict[str, Any], voltage_info: Dict[str, Any], variation: float = 0.1) -> Tuple[List[float], List[Dict[str, Any]]]:
    """
    Step 5: Distribute loads across floors and assign end loads.
    - Split total load across floors with ±variation (default 10%), sum matches total.
    - Assign end loads (lighting, receptacles, hvac, kitchen, specialty) to each floor.
    - Each end load type has a power rating.
    - No more than 50% of a floor's load can be a single end load type.
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

    # 2. Assign end loads to each floor
    end_loads = []
    for floor_idx, floor_load in enumerate(floor_loads):
        remaining = floor_load
        floor_end_loads = []
        # To avoid >50% of a type, set max for each type
        max_type_load = 0.5 * floor_load
        type_loads = {t["type"]: 0.0 for t in end_load_types}
        while remaining > 0.2:  # stop when remaining load is very small
            # Pick a random end load type
            t = random.choice(end_load_types)
            t_name = t["type"]
            t_power = t["power"]
            # Don't exceed max for this type
            if type_loads[t_name] + t_power > max_type_load:
                continue
            # Don't exceed remaining load
            if t_power > remaining:
                t_power = remaining
            # Assign voltage level for this end load
            if voltage_info['voltage_level'] == '120/208V':
                possible_voltages = [208, 120]
            else:
                possible_voltages = [480, 277, 208, 120]
            voltage = random.choice(possible_voltages)
            # Create end load dict
            end_load = {
                "floor": floor_idx,
                "type": t_name,
                "power": t_power,
                "voltage": voltage
            }
            floor_end_loads.append(end_load)
            type_loads[t_name] += t_power
            remaining -= t_power
        end_loads.extend(floor_end_loads)

    return floor_loads, end_loads

def determine_riser_attributes(building_attrs: Dict[str, Any], riser_locations: List[Tuple[float, float]], floor_loads: List[float], end_loads: List[Dict[str, Any]], voltage_info: Dict[str, Any]) -> Dict:
    """
    Step 6: Determine riser attributes on each floor.
    For each floor, assign each end load to the nearest riser (by x/y distance).
    For each riser on each floor, summarize the total power per end load type and voltage.
    Returns a nested dict: {floor: {riser_idx: {type: {voltage: total_power}}}}
    """
    num_floors = building_attrs['num_floors']
    riser_attrs = {floor: {r: {} for r in range(len(riser_locations))} for floor in range(num_floors)}

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

    return riser_attrs

def place_distribution_equipment(building_attrs: Dict[str, Any], riser_floor_attributes: Dict, voltage_info: Dict[str, Any]) -> Dict:
    """
    Step 7: Place distribution equipment in each riser on each floor.
    For each riser on each floor, determine what equipment is needed based on the load types and voltages.
    Returns a dict: {floor: {riser_idx: [equipment_dict, ...]}}
    """
    equipment = {}
    main_voltage = voltage_info['voltage_3phase']
    is_480_building = (main_voltage == 480)
    for floor, risers in riser_floor_attributes.items():
        equipment[floor] = {}
        for riser_idx, load_types in risers.items():
            riser_equipment = []
            # Always add a main distribution panel at the building's main voltage
            riser_equipment.append({
                "type": "main_panel",
                "voltage": main_voltage,
                "loads": load_types
            })
            # For each load type, handle sub-panels and transformers
            for t, vdict in load_types.items():
                if is_480_building:
                    high_v_power = 0.0
                    low_v_power = 0.0
                    for v, p in vdict.items():
                        if v in [480, 277]:
                            high_v_power += p
                        elif v in [208, 120]:
                            low_v_power += p
                    if high_v_power > 0 and low_v_power > 0:
                        # Add 480V sub-panel (parent: main_panel)
                        riser_equipment.append({
                            "type": "sub_panel",
                            "voltage": 480,
                            "load_type": t,
                            "power": high_v_power,
                            "parent": "main_panel"
                        })
                        # Add transformer (parent: 480V sub-panel)
                        riser_equipment.append({
                            "type": "transformer",
                            "from_voltage": 480,
                            "to_voltage": 208,
                            "load_type": t,
                            "power": low_v_power,
                            "parent": "sub_panel_480_{}".format(t)
                        })
                        # Add 208V sub-panel (parent: transformer)
                        riser_equipment.append({
                            "type": "sub_panel",
                            "voltage": 208,
                            "load_type": t,
                            "power": low_v_power,
                            "parent": "transformer_208_{}".format(t)
                        })
                    elif high_v_power > 0:
                        # Only high voltage loads: just add 480V sub-panel (parent: main_panel)
                        riser_equipment.append({
                            "type": "sub_panel",
                            "voltage": 480,
                            "load_type": t,
                            "power": high_v_power,
                            "parent": "main_panel"
                        })
                    elif low_v_power > 0:
                        # Only low voltage loads: transformer and 208V sub-panel, both parented to main_panel
                        riser_equipment.append({
                            "type": "transformer",
                            "from_voltage": 480,
                            "to_voltage": 208,
                            "load_type": t,
                            "power": low_v_power,
                            "parent": "main_panel"
                        })
                        riser_equipment.append({
                            "type": "sub_panel",
                            "voltage": 208,
                            "load_type": t,
                            "power": low_v_power,
                            "parent": "transformer_208_{}".format(t)
                        })
                else:
                    # For 208/120V building, just add sub-panels for each voltage if not main
                    for v, total_power in vdict.items():
                        if v == main_voltage:
                            continue
                        riser_equipment.append({
                            "type": "sub_panel",
                            "voltage": v,
                            "load_type": t,
                            "power": total_power,
                            "parent": "main_panel"
                        })
            equipment[floor][riser_idx] = riser_equipment
    return equipment

def connect_nodes(building_attrs: Dict[str, Any], riser_locations: List[Tuple[float, float]], distribution_equipment: Dict, voltage_info: Dict[str, Any]) -> nx.DiGraph:
    """
    Step 8: Connect all nodes to form the final graph.
    Framework only: placeholder functions for each connection step.
    """
    G = nx.DiGraph()

    # 1. Add utility transformer node
    add_utility_transformer(G, building_attrs)

    # 2. Add all distribution equipment nodes (main panels, transformers, sub-panels, etc.)
    add_distribution_equipment_nodes(G, distribution_equipment, riser_locations)

    # 3. Connect utility transformer to the nearest main panel on the ground floor
    connect_utility_to_main_panel(G, distribution_equipment, riser_locations)

    # 4. Connect main panels vertically in each riser
    connect_main_panels_vertically(G, distribution_equipment)

    # 5. Connect equipment within each riser/floor (main panel → transformer → sub-panel, etc.)
    connect_equipment_hierarchy(G, distribution_equipment)

    # # 6. Add end load nodes and connect them to the appropriate equipment
    add_and_connect_end_loads(G, distribution_equipment, building_attrs)

    return G

# --- Placeholder functions for graph construction ---
def add_utility_transformer(G, building_attrs):
    """Add the utility transformer node to the graph, placed outside the building footprint."""
    length = building_attrs['building_length']
    width = building_attrs['building_width']
    floor_height = building_attrs['floor_height']
    num_floors = building_attrs['num_floors']
    # Place transformer outside the building, near the main entrance (assume at x = -5, y = width/2, z = 0)
    x = -5.0
    y = width / 2.0
    z = 0.0
    G.add_node(
        "utility_transformer",
        type="utility_transformer",
        x=x,
        y=y,
        z=z,
        description="Utility transformer located outside the building footprint"
    )

def add_distribution_equipment_nodes(G, distribution_equipment, riser_locations):
    """Add all distribution equipment nodes to the graph with unique IDs and coordinates."""
    for floor, risers in distribution_equipment.items():
        for riser_idx, equipment_list in risers.items():
            x, y = riser_locations[riser_idx]
            z = floor * G.graph.get('floor_height', 3.5)
            for eq_idx, eq in enumerate(equipment_list):
                eq_type = eq.get('type', 'equipment')
                voltage = eq.get('voltage', '')
                node_id = f"{eq_type}_f{floor}_r{riser_idx}"
                if eq_type == 'transformer':
                    node_id += f"_{eq.get('to_voltage','')}_{eq.get('load_type','')}"
                    # Add all transformer attributes
                    G.add_node(
                        node_id,
                        type=eq_type,
                        floor=floor,
                        riser=riser_idx,
                        from_voltage=eq.get('from_voltage',''),
                        to_voltage=eq.get('to_voltage',''),
                        load_type=eq.get('load_type',''),
                        power=eq.get('power',0.0),
                        parent=eq.get('parent',''),
                        x=x,
                        y=y,
                        z=z
                    )
                elif eq_type == 'sub_panel':
                    node_id += f"_{voltage}_{eq.get('load_type','')}"
                    G.add_node(
                        node_id,
                        type=eq_type,
                        floor=floor,
                        riser=riser_idx,
                        voltage=voltage,
                        load_type=eq.get('load_type',''),
                        power=eq.get('power',0.0),
                        parent=eq.get('parent',''),
                        x=x,
                        y=y,
                        z=z
                    )
                else:
                    G.add_node(
                        node_id,
                        type=eq_type,
                        floor=floor,
                        riser=riser_idx,
                        voltage=voltage,
                        x=x,
                        y=y,
                        z=z,
                        **{k: v for k, v in eq.items() if k not in ['type', 'voltage', 'loads', 'load_type']}
                    )

def connect_utility_to_main_panel(G, distribution_equipment, riser_locations):
    """Connect the utility transformer to the nearest main panel on the ground floor."""
    # Find all main panels on the ground floor (floor 0)
    ground_floor = 0
    main_panel_nodes = []
    for riser_idx, equipment_list in distribution_equipment.get(ground_floor, {}).items():
        for eq in equipment_list:
            if eq.get('type') == 'main_panel':
                node_id = f"main_panel_f{ground_floor}_r{riser_idx}"
                main_panel_nodes.append((node_id, riser_idx))
    if not main_panel_nodes:
        return
    # Get utility transformer coordinates
    util_x = G.nodes['utility_transformer']['x']
    util_y = G.nodes['utility_transformer']['y']
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
        G.add_edge('utility_transformer', nearest_node, description='Utility to main panel connection')

def connect_main_panels_vertically(G, distribution_equipment):
    """Connect main panels vertically in each riser."""
    # For each riser, connect main panels from top floor down to ground floor
    # Assumes node ids are 'main_panel_f{floor}_r{riser_idx}'
    # Get all floors and risers
    if not distribution_equipment:
        return
    floors = sorted(distribution_equipment.keys(), reverse=True)  # top to bottom
    if not floors:
        return
    riser_indices = set()
    for risers in distribution_equipment.values():
        riser_indices.update(risers.keys())
    for riser_idx in riser_indices:
        # Collect all main panel node ids for this riser, sorted by floor descending
        main_panels = []
        for floor in floors:
            eq_list = distribution_equipment.get(floor, {}).get(riser_idx, [])
            for eq in eq_list:
                if eq.get('type') == 'main_panel':
                    node_id = f"main_panel_f{floor}_r{riser_idx}"
                    main_panels.append((floor, node_id))
        # Sort by floor descending (top to bottom)
        main_panels.sort(reverse=True)
        # Connect each main panel to the one below
        for i in range(len(main_panels) - 1):
            upper_node = main_panels[i][1]
            lower_node = main_panels[i + 1][1]
            G.add_edge(lower_node, upper_node, description='Vertical main panel connection')

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
                if eq_type == 'main_panel':
                    node_id = f"main_panel_f{floor}_r{riser_idx}"
                    node_id_map['main_panel'] = node_id
                elif eq_type == 'sub_panel':
                    node_id = f"sub_panel_f{floor}_r{riser_idx}_{voltage}_{load_type}"
                    if voltage == 480:
                        node_id_map[f"sub_panel_480_{load_type}"] = node_id
                    elif voltage == 208:
                        node_id_map[f"sub_panel_208_{load_type}"] = node_id
                    # Add for other voltages if needed
                elif eq_type == 'transformer':
                    to_voltage = eq.get('to_voltage', '')
                    node_id = f"transformer_f{floor}_r{riser_idx}_{to_voltage}_{load_type}"
                    node_id_map[f"transformer_{to_voltage}_{load_type}"] = node_id
            # Now connect each node to its parent using the parent field
            for eq in equipment_list:
                eq_type = eq.get('type')
                voltage = eq.get('voltage', '')
                load_type = eq.get('load_type', '')
                parent_key = eq.get('parent', None)
                # Determine this node's ID
                if eq_type == 'main_panel':
                    node_id = f"main_panel_f{floor}_r{riser_idx}"
                elif eq_type == 'sub_panel':
                    node_id = f"sub_panel_f{floor}_r{riser_idx}_{voltage}_{load_type}"
                elif eq_type == 'transformer':
                    to_voltage = eq.get('to_voltage', '')
                    node_id = f"transformer_f{floor}_r{riser_idx}_{to_voltage}_{load_type}"
                else:
                    continue
                # Connect to parent if parent_key is in map
                if parent_key and parent_key in node_id_map:
                    parent_id = node_id_map[parent_key]
                    G.add_edge(parent_id, node_id, description=f'{parent_key} to {eq_type}')

def add_and_connect_end_loads(G, distribution_equipment, building_attrs):
    """Add end load nodes and connect them to the appropriate equipment."""
    # To add end loads, we need to reconstruct the end loads per riser/floor/type/voltage
    # We'll use the same logic as in determine_riser_attributes, but for each riser/floor/type/voltage, add N end loads
    num_floors = building_attrs['num_floors']
    floor_height = building_attrs['floor_height']
    building_length = building_attrs['building_length']
    building_width = building_attrs['building_width']
    for floor, risers in distribution_equipment.items():
        for riser_idx, equipment_list in risers.items():
            sub_panel_map = {}
            main_panel_id = None
            created_nodes = set()
            # Map for transformer nodes (load_type, voltage) → node_id
            transformer_map = {}
            for eq in equipment_list:
                eq_type = eq.get('type')
                voltage = eq.get('voltage', '')
                load_type = eq.get('load_type','')
                if eq_type == 'sub_panel':
                    node_id = f"sub_panel_f{floor}_r{riser_idx}_{voltage}_{load_type}"
                    if node_id not in created_nodes:
                        sub_panel_map[(load_type, voltage)] = node_id
                        created_nodes.add(node_id)
                elif eq_type == 'main_panel':
                    main_panel_id = f"main_panel_f{floor}_r{riser_idx}"
                elif eq_type == 'transformer':
                    node_id = f"transformer_f{floor}_r{riser_idx}_{eq.get('to_voltage','')}_{load_type}"
                    transformer_map[(load_type, eq.get('to_voltage',''))] = node_id
            # For each sub-panel, add a single end load for its type/voltage with total power
            for (load_type, voltage), sub_panel_id in sub_panel_map.items():
                power = 0.0
                for eq in equipment_list:
                    if eq.get('type') == 'sub_panel' and eq.get('load_type','') == load_type and str(eq.get('voltage','')) == str(voltage):
                        power = eq.get('power', 0.0)
                        break
                x = random.uniform(0, building_length)
                y = random.uniform(0, building_width)
                z = floor * floor_height
                end_load_id = f"end_load_f{floor}_r{riser_idx}_{load_type}_{voltage}"
                if end_load_id not in created_nodes:
                    G.add_node(
                        end_load_id,
                        type='end_load',
                        floor=floor,
                        riser=riser_idx,
                        load_type=load_type,
                        voltage=voltage,
                        x=x,
                        y=y,
                        z=z,
                        power=round(power, 2)
                    )
                    created_nodes.add(end_load_id)
                G.add_edge(sub_panel_id, end_load_id, description='Sub-panel to end load')
            # If no sub-panels, connect a single end load directly to main panel (for main voltage)
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
                        for voltage, power in vdict.items():
                            if str(voltage) == str(main_voltage):
                                x = random.uniform(0, building_length)
                                y = random.uniform(0, building_width)
                                z = floor * floor_height
                                end_load_id = f"end_load_f{floor}_r{riser_idx}_{load_type}_{voltage}"
                                if end_load_id not in created_nodes:
                                    G.add_node(
                                        end_load_id,
                                        type='end_load',
                                        floor=floor,
                                        riser=riser_idx,
                                        load_type=load_type,
                                        voltage=voltage,
                                        x=x,
                                        y=y,
                                        z=z,
                                        power=round(power, 2)
                                    )
                                    created_nodes.add(end_load_id)
                                G.add_edge(main_panel_id, end_load_id, description='Main panel to end load')

if __name__ == "__main__":
    main()