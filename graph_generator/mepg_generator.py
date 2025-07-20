"""
MEP Graph Generator - Creates realistic electrical system topologies

This module generates random but logical electrical system graphs in MEPG format.
The generator creates hierarchical topologies starting from utility transformers,
through switchboards, to distribution panels and end loads.
"""

import random
import math
import datetime
import networkx as nx
from typing import List, Dict, Tuple, Any


class MEPGraphGenerator:
    """Generates realistic electrical system graphs with logical topology."""
    
    def __init__(self, seed: int = None, building_config: Dict = None):
        """
        Initialize the generator.
        
        Args:
            seed: Random seed for reproducible results
            building_config: Building configuration parameters
        """
        if seed is not None:
            random.seed(seed)
        
        # Default building configuration
        self.building_config = building_config or {
            'length': 80.0,          # Building length (m)
            'width': 60.0,           # Building width (m)
            'floor_height': 3.5,     # Typical floor height (m)
            'num_floors': 8,         # Number of floors
            'basement_depth': -3.0,  # Basement depth (m)
            'electrical_core': {     # Central electrical core area
                'x_center': 40.0,    # Center of building length
                'y_center': 30.0,    # Center of building width
                'width': 12.0,       # Electrical room width
                'depth': 8.0         # Electrical room depth
            }
        }
        
        # Initialize floor-based electrical room system
        self.floor_levels = self._define_floor_levels()
        self.electrical_rooms = self._define_electrical_rooms_by_floor()
        
        # Component type definitions
        self.component_types = {
            'transformer': 'Power Supply - Transformers - High-voltage systems - High-voltage dry-type power transformers',
            'switchboard': 'Power Supply - Power transmission - High-voltage systems - Distribution boards',
            'panelboard': 'Power Supply - Lighting - General lighting systems - Distribution boards',
            'load': 'Power Supply - Loads - General electrical loads'
        }
        
        # Manufacturer options
        self.manufacturers = ['Siemens', 'Schneider Electric', 'ABB', 'Eaton', 'GE', 'Cutler-Hammer']
        
        # Load classification types
        self.load_types = [
            'Main Distribution', 'Lighting', 'HVAC', 'Kitchen Equipment', 
            'General Power', 'Emergency Systems', 'IT Equipment', 'Motor Loads',
            'Sub-Distribution'
        ]
        
        # Voltage levels (typical North American electrical system)
        self.voltage_levels = {
            'high': [13500.0, 4160.0],  # Only one will be selected per graph
            'medium': [480.0],
            'low': [208.0]
        }
        
        # Mounting methods
        self.mounting_methods = ['Wall Mounted', 'Floor Mounted', 'Ceiling Mounted', 'Pole Mounted']
        
        # Physical dimensions ranges (mm)
        self.physical_dims = {
            'transformer': {'height': (2000, 3000), 'length': (2500, 4000), 'width': (1500, 2500)},
            'switchboard': {'height': (2000, 2500), 'length': (2000, 3500), 'width': (600, 1200)},
            'panelboard': {'height': (600, 1200), 'length': (400, 800), 'width': (150, 300)},
            'load': {'height': (100, 500), 'length': (200, 600), 'width': (100, 400)}
        }
    
    def _define_floor_levels(self) -> Dict[int, Dict]:
        """Define Z-coordinate levels for each floor."""
        config = self.building_config
        floor_levels = {}
        
        # Basement level (negative Z)
        floor_levels[-1] = {
            'z_min': config['basement_depth'],
            'z_max': -0.5,
            'z_center': config['basement_depth'] + config['floor_height'] / 2,
            'description': 'Basement level - Main electrical equipment'
        }
        
        # Ground and upper floors
        for floor in range(config['num_floors']):
            z_min = floor * config['floor_height']
            z_max = z_min + config['floor_height']
            floor_levels[floor] = {
                'z_min': z_min,
                'z_max': z_max,
                'z_center': z_min + config['floor_height'] / 2,
                'description': f'Floor {floor} - Distribution level'
            }
        
        return floor_levels
    
    def _define_electrical_rooms_by_floor(self) -> Dict[int, List[Dict]]:
        """Define electrical rooms on each floor with specific x,y bounds."""
        config = self.building_config
        electrical_rooms = {}
        
        # Basement electrical room (main service)
        electrical_rooms[-1] = [{
            'id': 'MER-B01',
            'description': 'Main Electrical Room',
            'x_min': config['electrical_core']['x_center'] - config['electrical_core']['width'] / 2,
            'x_max': config['electrical_core']['x_center'] + config['electrical_core']['width'] / 2,
            'y_min': config['electrical_core']['y_center'] - config['electrical_core']['depth'] / 2,
            'y_max': config['electrical_core']['y_center'] + config['electrical_core']['depth'] / 2,
            'equipment_types': ['main_transformer', 'main_switchboard'],
            'capacity': 4  # Max equipment pieces
        }]
        
        # Electrical rooms on each floor
        for floor in range(config['num_floors']):
            rooms = []
            
            # Primary electrical closet (center core)
            rooms.append({
                'id': f'EC-{floor:02d}A',
                'description': f'Electrical Closet A - Floor {floor}',
                'x_min': config['electrical_core']['x_center'] - 6.0,
                'x_max': config['electrical_core']['x_center'] + 2.0,
                'y_min': config['electrical_core']['y_center'] - 4.0,
                'y_max': config['electrical_core']['y_center'] + 4.0,
                'equipment_types': ['secondary_transformer', 'main_panelboard'],
                'capacity': 3
            })
            
            # Secondary electrical closet (offset core)
            rooms.append({
                'id': f'EC-{floor:02d}B',
                'description': f'Electrical Closet B - Floor {floor}',
                'x_min': config['electrical_core']['x_center'] + 2.0,
                'x_max': config['electrical_core']['x_center'] + 10.0,
                'y_min': config['electrical_core']['y_center'] - 2.0,
                'y_max': config['electrical_core']['y_center'] + 6.0,
                'equipment_types': ['panelboard'],
                'capacity': 2
            })
            
            # IDF rooms (distributed)
            if floor > 0:  # Not on ground floor
                rooms.append({
                    'id': f'IDF-{floor:02d}',
                    'description': f'IDF Room - Floor {floor}',
                    'x_min': config['length'] * 0.8,
                    'x_max': config['length'] * 0.95,
                    'y_min': config['width'] * 0.1,
                    'y_max': config['width'] * 0.3,
                    'equipment_types': ['panelboard'],
                    'capacity': 2
                })
            
            electrical_rooms[floor] = rooms
        
        return electrical_rooms
    
    def generate_graph(self, node_count: int) -> nx.DiGraph:
        """
        Generate a logical electrical system graph starting from basement and distributing upwards.
        
        Args:
            node_count: Target number of nodes in the graph
            
        Returns:
            NetworkX DiGraph representing the electrical system
        """
        if node_count < 3:
            raise ValueError("Node count must be at least 3 for a meaningful electrical system")
        
        G = nx.DiGraph()
        G.graph['id'] = f"Generated_Electrical_System_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        G.graph['source'] = "MEP Graph Generator"
        
        # Select one high voltage level for this entire graph
        self.selected_high_voltage = random.choice(self.voltage_levels['high'])
        
        # Calculate logical distribution of components by floor
        distribution = self._calculate_component_distribution_by_floor(node_count)
        
        # Generate nodes starting from basement (bottom-up approach)
        node_id = 1
        floor_nodes = {}
        
        # Basement level (-1): Main service equipment
        floor_nodes[-1] = []
        for i in range(distribution['floors'][-1]['transformers']):
            node_id_str = f"transformer_{node_id:03d}"
            self._add_transformer_node_in_room(G, node_id_str, 'main', node_id, -1)
            floor_nodes[-1].append(node_id_str)
            node_id += 1
        
        for i in range(distribution['floors'][-1]['switchboards']):
            node_id_str = f"switchboard_{node_id:03d}"
            self._add_switchboard_node_in_room(G, node_id_str, node_id, -1)
            floor_nodes[-1].append(node_id_str)
            node_id += 1
        
        # Upper floors (0 to num_floors-1): Distribution equipment and loads
        for floor in range(self.building_config['num_floors']):
            floor_nodes[floor] = []
            
            # Add transformers for this floor
            for i in range(distribution['floors'][floor]['transformers']):
                node_id_str = f"transformer_{node_id:03d}"
                self._add_transformer_node_in_room(G, node_id_str, 'secondary', node_id, floor)
                floor_nodes[floor].append(node_id_str)
                node_id += 1
            
            # Add panelboards for this floor
            for i in range(distribution['floors'][floor]['panelboards']):
                node_id_str = f"panelboard_{node_id:03d}"
                self._add_panelboard_node_in_room(G, node_id_str, node_id, floor)
                floor_nodes[floor].append(node_id_str)
                node_id += 1
            
            # Add loads distributed around the floor (outside electrical rooms)
            for i in range(distribution['floors'][floor]['loads']):
                node_id_str = f"load_{node_id:03d}"
                self._add_load_node_on_floor(G, node_id_str, node_id, floor)
                floor_nodes[floor].append(node_id_str)
                node_id += 1
        
        # Create logical bottom-up connections
        self._create_bottom_up_connections(G, floor_nodes)
        
        # Update voltages to ensure proper step-down relationships
        self._update_voltage_relationships(G)

        # Align transformer positions with upstream or downstream node
        self._align_transformer_positions(G)
        
        return G
    def _align_transformer_positions(self, G: nx.DiGraph):
        """Set transformer node positions to match either their upstream or downstream node, with randomization."""
        for node_id, attrs in G.nodes(data=True):
            if 'transformer' in node_id:
                predecessors = list(G.predecessors(node_id))
                successors = list(G.successors(node_id))
                ref_node = None
                # 90% chance to use downstream, 10% upstream (if available)
                use_downstream = random.random() < 0.9 and successors
                if use_downstream:
                    ref_node = successors[0]
                elif predecessors:
                    ref_node = predecessors[0]
                elif successors:
                    ref_node = successors[0]
                if ref_node:
                    ref_attrs = G.nodes[ref_node]
                    # Add a small random offset (within +/- 0.5m)
                    offset_x = random.uniform(-0.5, 0.5)
                    offset_y = random.uniform(-0.5, 0.5)
                    offset_z = random.uniform(-0.2, 0.2)
                    attrs['x'] = round(ref_attrs.get('x', attrs.get('x', 0.0)) + offset_x, 2)
                    attrs['y'] = round(ref_attrs.get('y', attrs.get('y', 0.0)) + offset_y, 2)
                    attrs['z'] = round(ref_attrs.get('z', attrs.get('z', 0.0)) + offset_z, 2)
    
    def _calculate_component_distribution_by_floor(self, node_count: int) -> Dict[str, Any]:
        """Calculate distribution of components across floors for bottom-up topology."""
        config = self.building_config
        num_floors = config['num_floors']
        
        # Initialize distribution structure
        distribution = {
            'floors': {}
        }
        
        # Basement floor (-1): Main service equipment
        distribution['floors'][-1] = {
            'transformers': 1,  # Main service transformer
            'switchboards': 1,  # Main service switchboard
            'panelboards': 0,
            'loads': 0
        }
        
        remaining_nodes = node_count - 2  # Account for main transformer and switchboard
        
        # Distribute remaining nodes across upper floors
        if remaining_nodes > 0:
            # Calculate nodes per floor (excluding basement)
            base_nodes_per_floor = max(1, remaining_nodes // num_floors)
            extra_nodes = remaining_nodes % num_floors
            
            for floor in range(num_floors):
                nodes_for_floor = base_nodes_per_floor
                if floor < extra_nodes:
                    nodes_for_floor += 1
                
                # Distribute types within floor
                if nodes_for_floor > 0:
                    # Floor distribution strategy: transformers -> panelboards -> loads
                    transformers = 1 if nodes_for_floor >= 3 and floor % 2 == 0 else 0  # Every other floor
                    remaining_after_transformers = nodes_for_floor - transformers
                    
                    panelboards = min(2, max(1, remaining_after_transformers // 2))
                    loads = max(0, remaining_after_transformers - panelboards)
                    
                    distribution['floors'][floor] = {
                        'transformers': transformers,
                        'switchboards': 0,  # No switchboards on upper floors
                        'panelboards': panelboards,
                        'loads': loads
                    }
                else:
                    distribution['floors'][floor] = {
                        'transformers': 0,
                        'switchboards': 0,
                        'panelboards': 0,
                        'loads': 0
                    }
        else:
            # If not enough nodes, just use basement equipment
            for floor in range(num_floors):
                distribution['floors'][floor] = {
                    'transformers': 0,
                    'switchboards': 0,
                    'panelboards': 0,
                    'loads': 0
                }
        
        return distribution
    
    def _add_transformer_node_in_room(self, G: nx.DiGraph, node_id: str, transformer_type: str, position_id: int, floor: int):
        """Add a transformer node positioned within an appropriate electrical room."""
        x, y, z = self._generate_position_in_electrical_room(node_id, position_id, floor, 'transformer')
        room_code = self._get_room_code_for_position(floor, x, y, 'transformer')
        
        if transformer_type == 'main':
            upstream_voltage = self.selected_high_voltage
            downstream_voltage = self.voltage_levels['medium'][0]  # 480V
            performance = random.choice(['1000 kVA', '1500 kVA', '2000 kVA', '2500 kVA'])
            current_rating = self._calculate_current_rating(downstream_voltage, performance)
        else:  # secondary
            upstream_voltage = 480.0
            downstream_voltage = self.voltage_levels['low'][0]  # 208V
            performance = random.choice(['150 kVA', '225 kVA', '300 kVA', '500 kVA'])
            current_rating = self._calculate_current_rating(downstream_voltage, performance)
        
        attrs = {
            'type': self.component_types['transformer'],
            'x': x, 'y': y, 'z': z,
            'room': room_code,
            'floor': floor,
            'Identifier': f"Transformer-{position_id:03d}",
            'Manufacturer': random.choice(self.manufacturers),
            'Nominal_performance': performance,
            'Short-circuit_strength_kA': round(random.uniform(10.0, 25.0), 1),
            'Physical_Height_mm': float(random.randint(*self.physical_dims['transformer']['height'])),
            'Physical_Length_mm': float(random.randint(*self.physical_dims['transformer']['length'])),
            'Physical_Width_mm': float(random.randint(*self.physical_dims['transformer']['width'])),
            'Type': 'Dry Type',
            'Voltage': f"{upstream_voltage/1000:.1f} kV" if upstream_voltage >= 1000 else f"{upstream_voltage:.0f} V",
            'Warranty_months': random.choice([24, 36, 60, 120]),
            'Year_of_manufacture': random.randint(2018, 2024),
            'Year_of_installation': random.randint(2018, 2024),
            'distribution_upstream_voltage': upstream_voltage,
            'distribution_upstream_current_rating': self._calculate_current_rating(upstream_voltage, performance),
            'distribution_upstream_phase_number': 3,
            'distribution_upstream_frequency': 60.0,
            'distribution_downstream_voltage': downstream_voltage,
            'distribution_downstream_current_rating': current_rating,
            'distribution_downstream_phase_number': 3,
            'distribution_downstream_frequency': 60.0,
            'AIC_rating': round(random.uniform(22.0, 65.0), 1)
        }
        
        G.add_node(node_id, **attrs)
    
    def _add_switchboard_node_in_room(self, G: nx.DiGraph, node_id: str, position_id: int, floor: int):
        """Add a switchboard node positioned within an appropriate electrical room."""
        x, y, z = self._generate_position_in_electrical_room(node_id, position_id, floor, 'switchboard')
        room_code = self._get_room_code_for_position(floor, x, y, 'switchboard')
        voltage = 480.0
        
        attrs = {
            'type': self.component_types['switchboard'],
            'x': x, 'y': y, 'z': z,
            'room': room_code,
            'floor': floor,
            'Identifier': f"Switchboard-{position_id:03d}",
            'Manufacturer': random.choice(self.manufacturers),
            'Operating_company_department': 'Facilities',
            'Owner': random.choice(['Building Owner', 'Tenant', 'Management Company']),
            'Nominal_current': 10.0,
            'Short-circuit_strength_kA': round(random.uniform(25.0, 65.0), 1),
            'Physical_Height_mm': float(random.randint(*self.physical_dims['switchboard']['height'])),
            'Physical_Length_mm': float(random.randint(*self.physical_dims['switchboard']['length'])),
            'Physical_Width_mm': float(random.randint(*self.physical_dims['switchboard']['width'])),
            'Warranty_months': random.choice([24, 36, 60]),
            'Year_of_manufacture': random.randint(2018, 2024),
            'Year_of_installation': random.randint(2018, 2024),
            'Outdoor_rated': random.choice([True, False]),
            'distribution_upstream_voltage': voltage,
            'distribution_upstream_current_rating': round(random.uniform(1000.0, 4000.0), 1),
            'distribution_upstream_phase_number': 3,
            'distribution_upstream_frequency': 60.0,
            'distribution_downstream_voltage': voltage,
            'distribution_downstream_current_rating': round(random.uniform(800.0, 3500.0), 1),
            'distribution_downstream_phase_number': 3,
            'distribution_downstream_frequency': 60.0,
            'AIC_rating': round(random.uniform(42.0, 65.0), 1)
        }
        
        G.add_node(node_id, **attrs)
    
    def _add_panelboard_node_in_room(self, G: nx.DiGraph, node_id: str, position_id: int, floor: int):
        """Add a panelboard node positioned within an appropriate electrical room."""
        x, y, z = self._generate_position_in_electrical_room(node_id, position_id, floor, 'panelboard')
        room_code = self._get_room_code_for_position(floor, x, y, 'panelboard')
        voltage = 208.0
        
        attrs = {
            'type': self.component_types['panelboard'],
            'x': x, 'y': y, 'z': z,
            'room': room_code,
            'floor': floor,
            'Identifier': f"Panelboard-{position_id:03d}",
            'Manufacturer': random.choice(self.manufacturers),
            'Masked_yes_no': random.choice([True, False]),
            'Mounting_method': random.choice(self.mounting_methods),
            'Nominal_current': 10.0,
            'Short-circuit_strength_kA': round(random.uniform(10.0, 22.0), 1),
            'Physical_Height_mm': float(random.randint(*self.physical_dims['panelboard']['height'])),
            'Physical_Length_mm': float(random.randint(*self.physical_dims['panelboard']['length'])),
            'Physical_Width_mm': float(random.randint(*self.physical_dims['panelboard']['width'])),
            'Warranty_months': random.choice([24, 36, 60]),
            'Year_of_manufacture': random.randint(2018, 2024),
            'Year_of_installation': random.randint(2018, 2024),
            'Operating_company_department': 'Facilities',
            'Owner': random.choice(['Building Owner', 'Tenant']),
            'Outdoor_rated': False,
            'distribution_upstream_voltage': voltage,
            'distribution_upstream_current_rating': round(random.uniform(100.0, 800.0), 1),
            'distribution_upstream_phase_number': 3,
            'distribution_upstream_frequency': 60.0,
            'distribution_downstream_voltage': voltage,
            'distribution_downstream_current_rating': round(random.uniform(80.0, 600.0), 1),
            'distribution_downstream_phase_number': 1,
            'distribution_downstream_frequency': 60.0,
            'AIC_rating': round(random.uniform(10.0, 25.0), 1)
        }
        
        G.add_node(node_id, **attrs)
    
    def _add_load_node_on_floor(self, G: nx.DiGraph, node_id: str, position_id: int, floor: int):
        """Add a load node distributed around the floor, outside electrical rooms."""
        x, y, z = self._generate_position_outside_electrical_rooms(node_id, position_id, floor)
        room_code = self._get_room_code_for_position(floor, x, y, 'load')
        voltage = 120.0
        
        attrs = {
            'type': self.component_types['load'],
            'x': x, 'y': y, 'z': z,
            'room': room_code,
            'floor': floor,
            'Identifier': f"Load-{position_id:03d}",
            'Manufacturer': random.choice(self.manufacturers),
            'Nominal_current': round(random.uniform(5.0, 50.0), 1),
            'Physical_Height_mm': float(random.randint(*self.physical_dims['load']['height'])),
            'Physical_Length_mm': float(random.randint(*self.physical_dims['load']['length'])),
            'Physical_Width_mm': float(random.randint(*self.physical_dims['load']['width'])),
            'Voltage': f"{voltage:.0f} V",
            'Warranty_months': random.choice([12, 24, 36]),
            'Year_of_manufacture': random.randint(2018, 2024),
            'Year_of_installation': random.randint(2018, 2024),
            'distribution_upstream_voltage': voltage,
            'distribution_upstream_current_rating': round(random.uniform(10.0, 100.0), 1),
            'distribution_upstream_phase_number': 1,
            'distribution_upstream_frequency': 60.0
        }
        
        G.add_node(node_id, **attrs)
    
    def _generate_position_in_electrical_room(self, node_id: str, position_id: int, floor: int, equipment_type: str) -> Tuple[float, float, float]:
        """Generate position within an appropriate electrical room for the equipment type."""
        # Get floor level info
        floor_level = self.floor_levels[floor]
        
        # Find appropriate room for this equipment type
        available_rooms = []
        if floor in self.electrical_rooms:
            for room in self.electrical_rooms[floor]:
                if equipment_type in room['equipment_types'] or 'any' in room['equipment_types']:
                    available_rooms.append(room)
        
        if not available_rooms:
            # Fallback to first available room on floor
            if floor in self.electrical_rooms and self.electrical_rooms[floor]:
                available_rooms = [self.electrical_rooms[floor][0]]
            else:
                # Ultimate fallback - generate position in building center
                config = self.building_config
                x = config['electrical_core']['x_center'] + random.uniform(-2.0, 2.0)
                y = config['electrical_core']['y_center'] + random.uniform(-2.0, 2.0)
                z = floor_level['z_center'] + random.uniform(-0.5, 0.5)
                return round(x, 1), round(y, 1), round(z, 1)
        
        # Select room (prefer less crowded rooms)
        selected_room = random.choice(available_rooms)
        
        # Generate position within room bounds
        x = random.uniform(selected_room['x_min'], selected_room['x_max'])
        y = random.uniform(selected_room['y_min'], selected_room['y_max'])
        z = floor_level['z_center'] + random.uniform(-0.3, 0.3)
        
        return round(x, 1), round(y, 1), round(z, 1)
    
    def _generate_position_outside_electrical_rooms(self, node_id: str, position_id: int, floor: int) -> Tuple[float, float, float]:
        """Generate position for loads distributed around the floor, avoiding electrical rooms."""
        config = self.building_config
        floor_level = self.floor_levels[floor]
        
        # Define usable floor area (excluding electrical rooms)
        max_attempts = 20
        for attempt in range(max_attempts):
            # Generate random position on floor
            x = random.uniform(5.0, config['length'] - 5.0)
            y = random.uniform(5.0, config['width'] - 5.0)
            z = floor_level['z_center'] + random.uniform(0.0, 2.0)  # Above floor level
            
            # Check if position conflicts with electrical rooms
            if self._is_position_outside_electrical_rooms(x, y, floor):
                return round(x, 1), round(y, 1), round(z, 1)
        
        # If all attempts failed, place at edge of building
        edge = random.choice(['north', 'south', 'east', 'west'])
        if edge == 'north':
            x = random.uniform(10.0, config['length'] - 10.0)
            y = config['width'] - 8.0
        elif edge == 'south':
            x = random.uniform(10.0, config['length'] - 10.0)
            y = 8.0
        elif edge == 'east':
            x = config['length'] - 8.0
            y = random.uniform(10.0, config['width'] - 10.0)
        else:  # west
            x = 8.0
            y = random.uniform(10.0, config['width'] - 10.0)
        
        z = floor_level['z_center'] + random.uniform(0.0, 2.0)
        return round(x, 1), round(y, 1), round(z, 1)
    
    def _is_position_outside_electrical_rooms(self, x: float, y: float, floor: int) -> bool:
        """Check if position is outside all electrical rooms on the floor."""
        if floor not in self.electrical_rooms:
            return True
        
        for room in self.electrical_rooms[floor]:
            # Add buffer around electrical rooms
            buffer = 2.0
            if (room['x_min'] - buffer <= x <= room['x_max'] + buffer and
                room['y_min'] - buffer <= y <= room['y_max'] + buffer):
                return False
        
        return True
    
    def _get_room_code_for_position(self, floor: int, x: float, y: float, equipment_type: str) -> str:
        """Get room code based on position and equipment type."""
        # Check if position is within any electrical room
        if floor in self.electrical_rooms:
            for room in self.electrical_rooms[floor]:
                if (room['x_min'] <= x <= room['x_max'] and
                    room['y_min'] <= y <= room['y_max']):
                    return room['id']
        
        # For loads outside electrical rooms, generate appropriate room codes
        if equipment_type == 'load':
            room_types = ['OFFICE', 'LAB', 'CONF', 'MECH', 'STOR']
            room_type = random.choice(room_types)
            room_num = random.randint(1, 20)
            return f"{room_type}-{floor:02d}{room_num:02d}"
        
        # Fallback room code
        return f"ROOM-{floor:02d}-{random.randint(1, 99):02d}"
    
    def _create_bottom_up_connections(self, G: nx.DiGraph, floor_nodes: Dict[int, List[str]]):
        """Create logical bottom-up connections starting from basement."""
        edge_id = 1
        
        # Start from basement main equipment
        basement_transformers = [n for n in floor_nodes.get(-1, []) if 'transformer' in n]
        basement_switchboards = [n for n in floor_nodes.get(-1, []) if 'switchboard' in n]
        
        # Connect basement transformers to switchboards
        for transformer in basement_transformers:
            for switchboard in basement_switchboards:
                self._add_connection(G, f"connection_{edge_id:03d}", transformer, switchboard, 'Main Distribution')
                edge_id += 1
        
        # Track equipment that can serve upper floors
        feeding_equipment = basement_switchboards.copy()
        
        # Connect each floor in ascending order
        for floor in sorted([f for f in floor_nodes.keys() if f >= 0]):
            floor_equipment = floor_nodes[floor]
            floor_transformers = [n for n in floor_equipment if 'transformer' in n]
            floor_panelboards = [n for n in floor_equipment if 'panelboard' in n]
            floor_loads = [n for n in floor_equipment if 'load' in n]
            
            # Connect transformers on this floor to feeding equipment from below
            for transformer in floor_transformers:
                if feeding_equipment:
                    closest_feeder = self._find_closest_equipment(G, transformer, feeding_equipment)
                    if closest_feeder:
                        self._add_connection(G, f"connection_{edge_id:03d}", closest_feeder, transformer, 'Floor Distribution')
                        edge_id += 1
            
            # Connect panelboards to transformers on same floor, or feeding equipment from below
            available_sources = floor_transformers + feeding_equipment
            for panelboard in floor_panelboards:
                if available_sources:
                    closest_source = self._find_closest_equipment(G, panelboard, available_sources)
                    if closest_source:
                        load_type = random.choice(['Lighting', 'General Power', 'HVAC'])
                        self._add_connection(G, f"connection_{edge_id:03d}", closest_source, panelboard, load_type)
                        edge_id += 1
            
            # Connect loads to panelboards on same floor
            for load in floor_loads:
                if floor_panelboards:
                    closest_panelboard = self._find_closest_equipment(G, load, floor_panelboards)
                    if closest_panelboard:
                        load_type = random.choice(['Lighting', 'General Power', 'Motor Loads'])
                        self._add_connection(G, f"connection_{edge_id:03d}", closest_panelboard, load, load_type)
                        edge_id += 1
            
            # Add floor equipment to feeding equipment for next floor
            feeding_equipment.extend(floor_transformers + floor_panelboards)
    
    def _define_equipment_zones(self) -> Dict[str, Dict]:
        """Define realistic zones for different equipment types."""
        config = self.building_config
        
        zones = {
            'main_electrical': {
                'description': 'Main electrical room (basement/ground floor)',
                'x_range': (config['electrical_core']['x_center'] - config['electrical_core']['width']/2,
                           config['electrical_core']['x_center'] + config['electrical_core']['width']/2),
                'y_range': (config['electrical_core']['y_center'] - config['electrical_core']['depth']/2,
                           config['electrical_core']['y_center'] + config['electrical_core']['depth']/2),
                'z_range': (config['basement_depth'], config['floor_height']),
                'equipment': ['main_transformer', 'main_switchboard']
            },
            
            'floor_electrical_rooms': {
                'description': 'Electrical closets on each floor',
                'x_range': (config['electrical_core']['x_center'] - 6.0,
                           config['electrical_core']['x_center'] + 6.0),
                'y_range': (config['electrical_core']['y_center'] - 4.0,
                           config['electrical_core']['y_center'] + 4.0),
                'z_range': (0.0, config['num_floors'] * config['floor_height']),
                'equipment': ['secondary_transformer', 'distribution_panelboard']
            },
            
            'corridor_locations': {
                'description': 'Corridor locations for smaller panels',
                'x_range': (5.0, config['length'] - 5.0),
                'y_range': (5.0, config['width'] - 5.0),
                'z_range': (0.0, config['num_floors'] * config['floor_height']),
                'equipment': ['panelboard']
            },
            
            'end_use_areas': {
                'description': 'Distributed throughout usable floor areas',
                'x_range': (8.0, config['length'] - 8.0),
                'y_range': (8.0, config['width'] - 8.0),
                'z_range': (0.0, config['num_floors'] * config['floor_height']),
                'equipment': ['load']
            }
        }
        
        return zones
    
    def _define_room_types(self) -> Dict[str, Dict]:
        """Define room types for different equipment based on building zones."""
        return {
            'main_electrical_room': {
                'description': 'Main electrical room in basement/ground floor',
                'typical_equipment': ['main_transformer', 'main_switchboard'],
                'room_codes': ['MER-B01', 'MER-001', 'ELEC-MAIN']
            },
            'electrical_closet': {
                'description': 'Electrical closets distributed on floors',
                'typical_equipment': ['secondary_transformer', 'distribution_panelboard'],
                'room_codes': ['EC-{floor:02d}A', 'EC-{floor:02d}B', 'ELEC-{floor:02d}']
            },
            'idf_room': {
                'description': 'Intermediate Distribution Frame rooms',
                'typical_equipment': ['panelboard', 'IT_equipment'],
                'room_codes': ['IDF-{floor:02d}A', 'IDF-{floor:02d}B', 'COMM-{floor:02d}']
            },
            'corridor': {
                'description': 'Corridor locations for wall-mounted panels',
                'typical_equipment': ['panelboard'],
                'room_codes': ['CORR-{floor:02d}A', 'CORR-{floor:02d}B', 'HALL-{floor:02d}']
            },
            'office': {
                'description': 'Office spaces',
                'typical_equipment': ['load'],
                'room_codes': ['OFF-{floor:02d}{room:02d}', 'OFFICE-{floor:02d}{room:02d}']
            },
            'conference_room': {
                'description': 'Conference and meeting rooms',
                'typical_equipment': ['load'],
                'room_codes': ['CONF-{floor:02d}{room:02d}', 'MEET-{floor:02d}{room:02d}']
            },
            'lab': {
                'description': 'Laboratory spaces',
                'typical_equipment': ['load'],
                'room_codes': ['LAB-{floor:02d}{room:02d}', 'RESEARCH-{floor:02d}{room:02d}']
            },
            'mechanical_room': {
                'description': 'Mechanical equipment rooms',
                'typical_equipment': ['load', 'panelboard'],
                'room_codes': ['MECH-{floor:02d}', 'HVAC-{floor:02d}', 'UTL-{floor:02d}']
            },
            'storage': {
                'description': 'Storage and utility rooms',
                'typical_equipment': ['load'],
                'room_codes': ['STOR-{floor:02d}{room:02d}', 'UTIL-{floor:02d}{room:02d}']
            }
        }
    
    def _assign_room_to_equipment(self, node_id: str, position_id: int, x: float, y: float, z: float) -> str:
        """Assign a realistic room code to equipment based on type and position."""
        room_types = self._define_room_types()
        config = self.building_config
        
        # Calculate floor number
        floor = max(0, int(z // config['floor_height']))
        if z < 0:
            floor = 0  # Basement considered as floor 0
        
        # Determine room based on equipment type and position
        if 'transformer' in node_id and 'transformer_001' in node_id:
            # Main transformer - main electrical room
            room_codes = room_types['main_electrical_room']['room_codes']
            return random.choice(room_codes)
            
        elif 'transformer' in node_id:
            # Secondary transformers - electrical closets
            room_codes = room_types['electrical_closet']['room_codes']
            selected_code = random.choice(room_codes)
            return selected_code.format(floor=floor)
            
        elif 'switchboard' in node_id:
            # Switchboards - main electrical room
            room_codes = room_types['main_electrical_room']['room_codes']
            return random.choice(room_codes)
            
        elif 'panelboard' in node_id:
            if self._is_main_distribution_panel(node_id):
                # Main distribution panels - electrical closets
                room_codes = room_types['electrical_closet']['room_codes']
                selected_code = random.choice(room_codes)
                return selected_code.format(floor=floor)
            else:
                # Sub-distribution panels - corridors or IDF rooms
                if random.random() < 0.3:  # 30% in IDF rooms
                    room_codes = room_types['idf_room']['room_codes']
                else:  # 70% in corridors
                    room_codes = room_types['corridor']['room_codes']
                selected_code = random.choice(room_codes)
                return selected_code.format(floor=floor)
                
        elif 'load' in node_id:
            # Loads - various room types based on building area
            room_type = self._determine_load_room_type(x, y, z, position_id)
            room_codes = room_types[room_type]['room_codes']
            selected_code = random.choice(room_codes)
            
            # Generate room number for spaces that need it
            if '{room:02d}' in selected_code:
                room_number = (position_id % 20) + 1  # Rooms 01-20
                return selected_code.format(floor=floor, room=room_number)
            else:
                return selected_code.format(floor=floor)
        
        # Fallback
        return f"ROOM-{floor:02d}-{position_id:03d}"
    
    def _determine_load_room_type(self, x: float, y: float, z: float, position_id: int) -> str:
        """Determine the room type for a load based on its position and building layout."""
        config = self.building_config
        
        # Calculate relative position in building
        x_ratio = x / config['length']
        y_ratio = y / config['width']
        floor = max(0, int(z // config['floor_height']))
        
        # Building layout assumptions:
        # - Core area (center): mechanical, storage, elevators
        # - Perimeter: offices, conference rooms
        # - Corners: labs, special equipment
        
        core_x_range = (0.3, 0.7)  # Central 40% of building width
        core_y_range = (0.3, 0.7)  # Central 40% of building depth
        
        # Determine if position is in core area
        in_core = (core_x_range[0] <= x_ratio <= core_x_range[1] and 
                  core_y_range[0] <= y_ratio <= core_y_range[1])
        
        # Ground floor has more mechanical rooms
        if floor == 0:
            if in_core:
                return random.choice(['mechanical_room', 'storage']) if random.random() < 0.6 else 'office'
            else:
                return random.choice(['office', 'conference_room', 'storage'])
        
        # Upper floors
        if in_core:
            # Core areas: mechanical, storage, conference rooms
            return random.choice(['mechanical_room', 'conference_room', 'storage'])
        else:
            # Perimeter areas: offices, labs, conference rooms
            # Corner positions more likely to be labs
            is_corner = ((x_ratio < 0.2 or x_ratio > 0.8) and 
                        (y_ratio < 0.2 or y_ratio > 0.8))
            
            if is_corner:
                return random.choice(['lab', 'conference_room'])
            else:
                return random.choice(['office', 'conference_room']) if random.random() < 0.8 else 'lab'
    
    def _assign_floor_for_equipment(self, position_id: int, equipment_type: str) -> int:
        """Assign floor based on equipment distribution strategy."""
        config = self.building_config
        
        if equipment_type in ['secondary_transformer', 'main_panelboard']:
            # Distribute major equipment across floors (every 2-3 floors)
            floors_per_equipment = max(2, config['num_floors'] // 4)
            return min(position_id * floors_per_equipment, config['num_floors'] - 1)
        else:
            # Distribute other equipment more evenly
            return position_id % config['num_floors']

    def _assign_floor_for_load(self, position_id: int) -> int:
        """Assign floor for loads with realistic distribution."""
        config = self.building_config
        
        # Weight distribution - more loads on middle floors (typical office usage)
        floor_weights = []
        for floor in range(config['num_floors']):
            if floor == 0:  # Ground floor
                weight = 0.8  # Some loads but less than upper floors
            elif floor < config['num_floors'] // 2:  # Lower floors
                weight = 1.0
            else:  # Upper floors
                weight = 1.2  # Higher density
            floor_weights.append(weight)
        
        # Weighted random selection
        total_weight = sum(floor_weights)
        rand_val = random.uniform(0, total_weight)
        cumulative = 0
        
        for floor, weight in enumerate(floor_weights):
            cumulative += weight
            if rand_val <= cumulative:
                return floor
        
        return config['num_floors'] - 1  # Fallback
    
    def _is_main_distribution_panel(self, node_id: str) -> bool:
        """Determine if a panelboard is a main distribution panel."""
        # First few panelboards are considered main distribution
        node_num = int(node_id.split('_')[1])
        return node_num <= 3  # First 3 panelboards are main distribution
    
    def _add_transformer_node(self, G: nx.DiGraph, node_id: str, transformer_type: str, position_id: int):
        """Add a transformer node with realistic attributes."""
        x, y, z = self._generate_position(position_id, node_id)
        room_code = self._assign_room_to_equipment(node_id, position_id, x, y, z)
        
        if transformer_type == 'main':
            upstream_voltage = self.selected_high_voltage  # Use the selected high voltage for this graph
            downstream_voltage = self.voltage_levels['medium'][0]  # 480V
            performance = random.choice(['1000 kVA', '1500 kVA', '2000 kVA', '2500 kVA'])
            current_rating = self._calculate_current_rating(downstream_voltage, performance)
        else:  # secondary
            # Secondary transformers will have their voltages set properly in the propagation step
            # Set temporary values that will be overwritten
            upstream_voltage = 480.0  # Will be set based on actual upstream connection
            downstream_voltage = self.voltage_levels['low'][0]  # 208V
            performance = random.choice(['150 kVA', '225 kVA', '300 kVA', '500 kVA'])
            current_rating = self._calculate_current_rating(downstream_voltage, performance)
        
        attrs = {
            'type': self.component_types['transformer'],
            'x': x, 'y': y, 'z': z,
            'room': room_code,
            'Identifier': f"Transformer-{position_id:03d}",
            'Manufacturer': random.choice(self.manufacturers),
            'Nominal_performance': performance,
            'Short-circuit_strength_kA': round(random.uniform(10.0, 25.0), 1),
            'Physical_Height_mm': float(random.randint(*self.physical_dims['transformer']['height'])),
            'Physical_Length_mm': float(random.randint(*self.physical_dims['transformer']['length'])),
            'Physical_Width_mm': float(random.randint(*self.physical_dims['transformer']['width'])),
            'Type': 'Dry Type',
            'Voltage': f"{upstream_voltage/1000:.1f} kV" if upstream_voltage >= 1000 else f"{upstream_voltage:.0f} V",
            'Warranty_months': random.choice([24, 36, 60, 120]),
            'Year_of_manufacture': random.randint(2018, 2024),
            'Year_of_installation': random.randint(2018, 2024),
            'distribution_upstream_voltage': upstream_voltage,
            'distribution_upstream_current_rating': self._calculate_current_rating(upstream_voltage, performance),
            'distribution_upstream_phase_number': 3,
            'distribution_upstream_frequency': 60.0,
            'distribution_downstream_voltage': downstream_voltage,
            'distribution_downstream_current_rating': current_rating,
            'distribution_downstream_phase_number': 3,
            'distribution_downstream_frequency': 60.0,
            'AIC_rating': round(random.uniform(22.0, 65.0), 1)
        }
        
        G.add_node(node_id, **attrs)
    
    def _add_switchboard_node(self, G: nx.DiGraph, node_id: str, position_id: int):
        """Add a switchboard node with realistic attributes."""
        x, y, z = self._generate_position(position_id, node_id)
        room_code = self._assign_room_to_equipment(node_id, position_id, x, y, z)
        # Switchboards will have voltage set later based on upstream transformer
        voltage = 480.0  # Default medium voltage, will be updated in connections
        
        attrs = {
            'type': self.component_types['switchboard'],
            'x': x, 'y': y, 'z': z,
            'room': room_code,
            'Identifier': f"Switchboard-{position_id:03d}",
            'Manufacturer': random.choice(self.manufacturers),
            'Operating_company_department': 'Facilities',
            'Owner': random.choice(['Building Owner', 'Tenant', 'Management Company']),
            'Nominal_current': 10.0,
            'Short-circuit_strength_kA': round(random.uniform(25.0, 65.0), 1),
            'Physical_Height_mm': float(random.randint(*self.physical_dims['switchboard']['height'])),
            'Physical_Length_mm': float(random.randint(*self.physical_dims['switchboard']['length'])),
            'Physical_Width_mm': float(random.randint(*self.physical_dims['switchboard']['width'])),
            'Warranty_months': random.choice([24, 36, 60]),
            'Year_of_manufacture': random.randint(2018, 2024),
            'Year_of_installation': random.randint(2018, 2024),
            'Outdoor_rated': random.choice([True, False]),
            'distribution_upstream_voltage': voltage,
            'distribution_upstream_current_rating': round(random.uniform(1000.0, 4000.0), 1),
            'distribution_upstream_phase_number': 3,
            'distribution_upstream_frequency': 60.0,
            'distribution_downstream_voltage': voltage,  # Same as upstream for switchboards
            'distribution_downstream_current_rating': round(random.uniform(800.0, 3500.0), 1),
            'distribution_downstream_phase_number': 3,
            'distribution_downstream_frequency': 60.0,
            'AIC_rating': round(random.uniform(42.0, 65.0), 1)
        }
        
        G.add_node(node_id, **attrs)
    
    def _add_panelboard_node(self, G: nx.DiGraph, node_id: str, position_id: int):
        """Add a panelboard node with realistic attributes."""
        x, y, z = self._generate_position(position_id, node_id)
        room_code = self._assign_room_to_equipment(node_id, position_id, x, y, z)
        # Panelboards will have voltage set later based on upstream equipment
        voltage = 208.0  # Default voltage, will be updated in connections
        
        attrs = {
            'type': self.component_types['panelboard'],
            'x': x, 'y': y, 'z': z,
            'room': room_code,
            'Identifier': f"Panelboard-{position_id:03d}",
            'Manufacturer': random.choice(self.manufacturers),
            'Masked_yes_no': random.choice([True, False]),
            'Mounting_method': random.choice(self.mounting_methods),
            'Nominal_current': 10.0,
            'Short-circuit_strength_kA': round(random.uniform(10.0, 22.0), 1),
            'Physical_Height_mm': float(random.randint(*self.physical_dims['panelboard']['height'])),
            'Physical_Length_mm': float(random.randint(*self.physical_dims['panelboard']['length'])),
            'Physical_Width_mm': float(random.randint(*self.physical_dims['panelboard']['width'])),
            'Warranty_months': random.choice([24, 36, 60]),
            'Year_of_manufacture': random.randint(2018, 2024),
            'Year_of_installation': random.randint(2018, 2024),
            'Operating_company_department': 'Facilities',
            'Owner': random.choice(['Building Owner', 'Tenant']),
            'Outdoor_rated': False,
            'distribution_upstream_voltage': voltage,
            'distribution_upstream_current_rating': round(random.uniform(100.0, 800.0), 1),
            'distribution_upstream_phase_number': 3,
            'distribution_upstream_frequency': 60.0,
            'distribution_downstream_voltage': voltage,  # Same as upstream for panelboards
            'distribution_downstream_current_rating': round(random.uniform(80.0, 600.0), 1),
            'distribution_downstream_phase_number': 1,
            'distribution_downstream_frequency': 60.0,
            'AIC_rating': round(random.uniform(10.0, 25.0), 1)
        }
        
        G.add_node(node_id, **attrs)
    
    def _add_load_node(self, G: nx.DiGraph, node_id: str, position_id: int):
        """Add a load node with realistic attributes."""
        x, y, z = self._generate_position(position_id, node_id)
        room_code = self._assign_room_to_equipment(node_id, position_id, x, y, z)
        # Loads will have voltage set later based on upstream panelboard
        voltage = 120.0  # Default low voltage, will be updated in connections
        
        attrs = {
            'type': self.component_types['load'],
            'x': x, 'y': y, 'z': z,
            'room': room_code,
            'Identifier': f"Load-{position_id:03d}",
            'Manufacturer': random.choice(self.manufacturers),
            'Nominal_current': round(random.uniform(5.0, 50.0), 1),
            'Physical_Height_mm': float(random.randint(*self.physical_dims['load']['height'])),
            'Physical_Length_mm': float(random.randint(*self.physical_dims['load']['length'])),
            'Physical_Width_mm': float(random.randint(*self.physical_dims['load']['width'])),
            'Voltage': f"{voltage:.0f} V",
            'Warranty_months': random.choice([12, 24, 36]),
            'Year_of_manufacture': random.randint(2018, 2024),
            'Year_of_installation': random.randint(2018, 2024),
            'distribution_upstream_voltage': voltage,
            'distribution_upstream_current_rating': round(random.uniform(10.0, 100.0), 1),
            'distribution_upstream_phase_number': 1,
            'distribution_upstream_frequency': 60.0
        }
        
        G.add_node(node_id, **attrs)
    
    def _generate_position(self, position_id: int, node_id: str = None) -> Tuple[float, float, float]:
        """Generate realistic 3D position for a component based on equipment type."""
        if node_id:
            return self._generate_position_by_type(node_id, position_id)
        else:
            # Fallback to original method for backward compatibility
            return self._generate_position_original(position_id)
    
    def _generate_position_by_type(self, node_id: str, position_id: int) -> Tuple[float, float, float]:
        """Generate realistic position based on equipment type and building zones."""
        zones = self._define_equipment_zones()
        config = self.building_config
        
        if 'transformer' in node_id and 'transformer_001' in node_id:
            # Main transformer - basement or ground floor electrical room
            zone = zones['main_electrical']
            x = random.uniform(*zone['x_range'])
            y = random.uniform(*zone['y_range'])
            z = random.uniform(config['basement_depth'], 0.5)  # Prefer basement
            
        elif 'transformer' in node_id:
            # Secondary transformers - distributed in electrical rooms on floors
            zone = zones['floor_electrical_rooms']
            floor = self._assign_floor_for_equipment(position_id, 'secondary_transformer')
            x = random.uniform(*zone['x_range'])
            y = random.uniform(*zone['y_range'])
            z = floor * config['floor_height'] + random.uniform(0.0, 0.5)
            
        elif 'switchboard' in node_id:
            # Main switchboards - main electrical room
            zone = zones['main_electrical']
            x = random.uniform(*zone['x_range'])
            y = random.uniform(*zone['y_range'])
            z = random.uniform(0.0, config['floor_height'])
            
        elif 'panelboard' in node_id:
            # Distribution strategy based on building hierarchy
            if self._is_main_distribution_panel(node_id):
                # Main distribution panels - electrical rooms
                zone = zones['floor_electrical_rooms']
                floor = self._assign_floor_for_equipment(position_id, 'main_panelboard')
                x = random.uniform(*zone['x_range'])
                y = random.uniform(*zone['y_range'])
                z = floor * config['floor_height'] + random.uniform(0.0, 0.5)
            else:
                # Sub-distribution panels - corridor locations
                zone = zones['corridor_locations']
                floor = self._assign_floor_for_equipment(position_id, 'panelboard')
                x = random.uniform(*zone['x_range'])
                y = random.uniform(*zone['y_range'])
                z = floor * config['floor_height'] + random.uniform(1.0, 2.5)  # Wall mounted height
                
        elif 'load' in node_id:
            # End loads - distributed throughout building
            zone = zones['end_use_areas']
            floor = self._assign_floor_for_load(position_id)
            x = random.uniform(*zone['x_range'])
            y = random.uniform(*zone['y_range'])
            z = floor * config['floor_height'] + random.uniform(0.0, 3.0)
            
        else:
            # Fallback to original method
            return self._generate_position_original(position_id)
        
        return round(x, 1), round(y, 1), round(z, 1)
    
    def _generate_position_original(self, position_id: int) -> Tuple[float, float, float]:
        """Original position generation method (fallback)."""
        # Create a rough grid layout with some randomness
        grid_size = math.ceil(math.sqrt(position_id))
        base_x = (position_id % grid_size) * 20.0
        base_y = (position_id // grid_size) * 20.0
        
        # Add some randomness to avoid perfect grid
        x = base_x + random.uniform(-5.0, 5.0)
        y = base_y + random.uniform(-5.0, 5.0)
        z = random.uniform(0.0, 3.0)  # Typical floor height variation
        
        return round(x, 1), round(y, 1), round(z, 1)
    
    def _calculate_current_rating(self, voltage: float, performance: str) -> float:
        """Calculate realistic current rating based on voltage and power."""
        # Extract kVA from performance string
        if 'kVA' in performance:
            kva = float(performance.replace(' kVA', ''))
            # I = P / (√3 × V) for three-phase
            current = (kva * 1000) / (math.sqrt(3) * voltage)
            return round(current, 1)
        return round(random.uniform(100.0, 1000.0), 1)
    
    def _create_connections(self, G: nx.DiGraph, level_nodes: Dict[int, List[str]]):
        """Create logical connections between nodes with distance considerations."""
        edge_id = 1
        
        # Level 1 to Level 2: Transformers to Switchboards
        for transformer in level_nodes[1]:
            closest_switchboard = self._find_closest_equipment(G, transformer, level_nodes[2])
            if closest_switchboard:
                self._add_connection(G, f"connection_{edge_id:03d}", transformer, closest_switchboard, 'Main Distribution')
                edge_id += 1
        
        # Level 2 to Level 3: Switchboards to Secondary Transformers
        if level_nodes[3]:  # If there are secondary transformers
            for transformer in level_nodes[3]:
                closest_switchboard = self._find_closest_equipment(G, transformer, level_nodes[2])
                if closest_switchboard:
                    self._add_connection(G, f"connection_{edge_id:03d}", closest_switchboard, transformer, 'Secondary Distribution')
                    edge_id += 1
        
        # Connect transformers to panelboards with proximity-based logic
        connected_panelboards = set()
        
        # First, connect secondary transformers to panelboards (proximity-based)
        if level_nodes[3]:  # If there are secondary transformers
            for transformer in level_nodes[3]:
                available_panelboards = [pb for pb in level_nodes[4] if pb not in connected_panelboards]
                if available_panelboards:
                    closest_panelboard = self._find_closest_equipment(G, transformer, available_panelboards)
                    if closest_panelboard:
                        load_type = random.choice(self.load_types)
                        self._add_connection(G, f"connection_{edge_id:03d}", transformer, closest_panelboard, load_type)
                        connected_panelboards.add(closest_panelboard)
                        edge_id += 1
        
        # Connect remaining panelboards to switchboards and other panelboards
        remaining_panelboards = [pb for pb in level_nodes[4] if pb not in connected_panelboards]
        
        if remaining_panelboards:
            # Connect main distribution panelboards directly to switchboards
            main_dist_panels = [pb for pb in remaining_panelboards if self._is_main_distribution_panel(pb)]
            
            for panelboard in main_dist_panels:
                closest_switchboard = self._find_closest_equipment(G, panelboard, level_nodes[2])
                if closest_switchboard:
                    load_type = random.choice(self.load_types)
                    self._add_connection(G, f"connection_{edge_id:03d}", closest_switchboard, panelboard, load_type)
                    connected_panelboards.add(panelboard)
                    edge_id += 1
            
            # Connect remaining panelboards to already connected equipment
            remaining_panelboards = [pb for pb in level_nodes[4] if pb not in connected_panelboards]
            available_sources = list(connected_panelboards) + level_nodes[2]  # Include switchboards as sources
            
            for panelboard in remaining_panelboards:
                if available_sources:
                    closest_source = self._find_closest_equipment(G, panelboard, available_sources)
                    if closest_source:
                        load_type = random.choice(['Lighting', 'General Power', 'Sub-Distribution'])
                        self._add_connection(G, f"connection_{edge_id:03d}", closest_source, panelboard, load_type)
                        connected_panelboards.add(panelboard)
                        available_sources.append(panelboard)
                        edge_id += 1
        
        # Level 4 to Level 5: Panelboards to Loads (proximity-based)
        if level_nodes[5]:  # If there are load nodes
            for load in level_nodes[5]:
                closest_panelboard = self._find_closest_equipment(G, load, level_nodes[4])
                if closest_panelboard:
                    load_type = random.choice(['Lighting', 'General Power', 'Motor Loads'])
                    self._add_connection(G, f"connection_{edge_id:03d}", closest_panelboard, load, load_type)
                    edge_id += 1
    
    def _find_closest_equipment(self, G: nx.DiGraph, source_node: str, target_candidates: List[str]) -> str:
        """Find the closest equipment from a list of candidates, with floor-aware logic."""
        if not target_candidates:
            return None

        source_attrs = G.nodes[source_node]
        source_z = source_attrs.get('z', 0.0)
        source_floor = source_attrs.get('floor', 0)
        min_distance = float('inf')
        closest_node = None

        # For bottom-up topology, prefer candidates at lower or same floor for distribution
        # This reverses the previous logic for upward distribution
        same_floor_candidates = [c for c in target_candidates if G.nodes[c].get('floor', 0) == source_floor]
        lower_floor_candidates = [c for c in target_candidates if G.nodes[c].get('floor', 0) < source_floor]
        
        # Priority: same floor first, then lower floors (for distribution from below)
        candidates_to_check = same_floor_candidates + lower_floor_candidates
        if not candidates_to_check:
            candidates_to_check = target_candidates  # Fallback to all candidates

        for candidate in candidates_to_check:
            candidate_floor = G.nodes[candidate].get('floor', 0)
            distance = self._calculate_distance(G, source_node, candidate)
            
            # Apply floor preference weighting
            if candidate_floor == source_floor:
                # Same floor - prefer closer distances
                weight = 1.0
            elif candidate_floor < source_floor:
                # Lower floor (feeding from below) - slight penalty for distance
                weight = 1.2
            else:
                # Higher floor - larger penalty
                weight = 2.0
            
            weighted_distance = distance * weight
            
            if weighted_distance < min_distance and self._is_reasonable_distance(distance, source_node, candidate):
                min_distance = weighted_distance
                closest_node = candidate

        # If no candidates meet distance criteria, return the closest one anyway
        if closest_node is None and candidates_to_check:
            closest_node = min(candidates_to_check, key=lambda x: self._calculate_distance(G, source_node, x))

        return closest_node
    
    def _calculate_distance(self, G: nx.DiGraph, node1: str, node2: str) -> float:
        """Calculate 3D distance between two nodes."""
        attrs1 = G.nodes[node1]
        attrs2 = G.nodes[node2]
        
        dx = attrs1['x'] - attrs2['x']
        dy = attrs1['y'] - attrs2['y']
        dz = attrs1['z'] - attrs2['z']
        
        return math.sqrt(dx*dx + dy*dy + dz*dz)
    
    def _is_reasonable_distance(self, distance: float, source_node: str, target_node: str) -> bool:
        """Check if connection distance is realistic for cable routing."""
        max_distances = {
            ('transformer', 'switchboard'): 50.0,
            ('switchboard', 'transformer'): 100.0,
            ('switchboard', 'panelboard'): 150.0,
            ('transformer', 'panelboard'): 80.0,
            ('panelboard', 'panelboard'): 100.0,
            ('panelboard', 'load'): 50.0
        }
        
        source_type = 'transformer' if 'transformer' in source_node else \
                     'switchboard' if 'switchboard' in source_node else \
                     'panelboard' if 'panelboard' in source_node else 'load'
        
        target_type = 'transformer' if 'transformer' in target_node else \
                     'switchboard' if 'switchboard' in target_node else \
                     'panelboard' if 'panelboard' in target_node else 'load'
        
        key = (source_type, target_type)
        max_dist = max_distances.get(key, 200.0)  # Default max distance
        
        return distance <= max_dist
    
    def _add_connection(self, G: nx.DiGraph, edge_id: str, source: str, target: str, load_classification: str):
        """Add a connection (edge) between two nodes."""
        source_attrs = G.nodes[source]
        target_attrs = G.nodes[target]
        
        # Calculate actual cable distance
        cable_distance = self._calculate_distance(G, source, target)
        
        # Determine voltage based on source downstream voltage
        voltage = source_attrs.get('distribution_downstream_voltage', 480.0)
        
        # Calculate current rating (typically less than source capacity)
        source_current = source_attrs.get('distribution_downstream_current_rating', 1000.0)
        current_rating = round(source_current * random.uniform(0.6, 0.9), 1)
        
        # Calculate apparent current (typically less than rating)
        apparent_current = round(current_rating * random.uniform(0.7, 0.95), 1)
        
        # Calculate voltage drop based on actual distance and current
        voltage_drop = self._calculate_realistic_voltage_drop(cable_distance, current_rating, voltage)
        
        edge_attrs = {
            'connection_type': 'Power',
            'voltage': voltage,
            'current_rating': current_rating,
            'phase_number': 3 if voltage > 240 else 1,
            'frequency': 60.0,
            'apparent_current': apparent_current,
            'voltage_drop': voltage_drop,
            'load_classification': load_classification,
            'cable_distance': round(cable_distance, 1)  # Add actual cable distance
        }
        
        G.add_edge(source, target, id=edge_id, **edge_attrs)
    
    def _calculate_realistic_voltage_drop(self, distance: float, current: float, voltage: float) -> float:
        """Calculate realistic voltage drop based on distance, current, and voltage."""
        # Simplified voltage drop calculation: V_drop = I × R × L
        # Where R is approximately 0.02 ohms per 100m for typical cable
        resistance_per_100m = 0.02  # ohms per 100m
        resistance = (distance / 100.0) * resistance_per_100m
        voltage_drop = current * resistance
        
        # Cap at reasonable values (1-8% of voltage)
        max_drop = voltage * 0.08
        min_drop = voltage * 0.01
        
        return round(max(min_drop, min(voltage_drop, max_drop)), 1)
    
    def save_graph(self, graph: nx.DiGraph, filename: str = None, node_count: int = None, seed: int = None) -> str:
        """
        Save the graph to a MEPG file.
        
        Args:
            graph: NetworkX graph to save
            filename: Output filename (if None, generates timestamp-based name with node count and seed)
            node_count: Number of nodes in the graph (for filename)
            seed: Random seed used (for filename)
            
        Returns:
            Path to the saved file
        """
        if filename is None:
            timestamp = datetime.datetime.now().strftime('%y%m%d_%H%M%S')
            node_str = f"_{node_count}" if node_count is not None else ""
            seed_str = f"_seed{seed}" if seed is not None else ""
            filename = f"generated_graph{node_str}{seed_str}_{timestamp}.mepg"
        
        # Ensure .mepg extension
        if not filename.lower().endswith('.mepg'):
            filename += '.mepg'
        
        # Ensure graph_outputs directory exists
        import os
        output_dir = 'graph_outputs'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        filepath = os.path.join(output_dir, filename)
        
        # Save as GraphML
        nx.write_graphml(graph, filepath)
        
        return filepath
    
    def _update_voltage_relationships(self, G: nx.DiGraph):
        """Update voltage relationships to ensure proper step-down from transformers."""
        # Start from main transformers and propagate voltages downstream
        for node_id, attrs in G.nodes(data=True):
            if 'transformer' in node_id and 'transformer_001' in node_id:  # Main transformer
                # Main transformers already have correct voltages set
                self._propagate_voltage_downstream(G, node_id)
    
    def _propagate_voltage_downstream(self, G: nx.DiGraph, source_node: str):
        """Recursively propagate voltages downstream from a source node."""
        source_attrs = G.nodes[source_node]
        source_downstream_voltage = source_attrs.get('distribution_downstream_voltage')
        
        # Get all nodes this source feeds
        for target_node in G.successors(source_node):
            target_attrs = G.nodes[target_node]
            
            if 'transformer' in target_node:
                # For transformers, ensure step-down only (downstream < upstream)
                # Secondary transformers step down from 480V to 208V
                if source_downstream_voltage == 480.0:
                    # Step down to 208V
                    new_downstream = 208.0
                    G.nodes[target_node]['distribution_upstream_voltage'] = source_downstream_voltage
                    G.nodes[target_node]['distribution_downstream_voltage'] = new_downstream
                    
                    # Update the Voltage display attribute
                    G.nodes[target_node]['Voltage'] = f"{source_downstream_voltage:.0f} V"
                
            else:
                # For switchboards, panelboards, and loads: upstream = downstream voltage
                G.nodes[target_node]['distribution_upstream_voltage'] = source_downstream_voltage
                G.nodes[target_node]['distribution_downstream_voltage'] = source_downstream_voltage
                
                # Update Voltage display attribute for loads
                if 'load' in target_node:
                    G.nodes[target_node]['Voltage'] = f"{source_downstream_voltage:.0f} V"
            
            # Update the edge voltage to match the actual voltage being transmitted
            edge_data = G.get_edge_data(source_node, target_node)
            if edge_data:
                edge_data['voltage'] = source_downstream_voltage
                # Update phase number based on voltage level
                edge_data['phase_number'] = 3 if source_downstream_voltage > 240 else 1
            
            # Continue propagating downstream
            self._propagate_voltage_downstream(G, target_node)
    

def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate random MEP electrical system graphs')
    parser.add_argument('node_count', type=int, help='Number of nodes in the generated graph')
    parser.add_argument('--filename', '-f', type=str, help='Output filename (optional)')
    parser.add_argument('--seed', '-s', type=int, help='Random seed for reproducible results')
    parser.add_argument('--building-length', type=float, default=80.0, help='Building length in meters')
    parser.add_argument('--building-width', type=float, default=60.0, help='Building width in meters')
    parser.add_argument('--num-floors', type=int, default=8, help='Number of floors')
    parser.add_argument('--floor-height', type=float, default=3.5, help='Floor height in meters')
    
    args = parser.parse_args()
    
    if args.node_count < 3:
        print("Error: Node count must be at least 3 for a meaningful electrical system")
        return
    
    # Create building configuration
    building_config = {
        'length': args.building_length,
        'width': args.building_width,
        'floor_height': args.floor_height,
        'num_floors': args.num_floors,
        'basement_depth': -3.0,
        'electrical_core': {
            'x_center': args.building_length / 2,
            'y_center': args.building_width / 2,
            'width': 12.0,
            'depth': 8.0
        }
    }
    
    # Create generator
    generator = MEPGraphGenerator(seed=args.seed, building_config=building_config)
    
    # Generate graph
    print(f"Generating electrical system graph with {args.node_count} nodes...")
    print(f"Building: {args.building_length}m × {args.building_width}m, {args.num_floors} floors")
    graph = generator.generate_graph(args.node_count)
    
    # Save graph
    filepath = generator.save_graph(graph, args.filename, node_count=args.node_count, seed=args.seed)
    print(f"Graph saved to: {filepath}")
    
    # Print summary
    print(f"\nGraph Summary:")
    print(f"  Nodes: {graph.number_of_nodes()}")
    print(f"  Edges: {graph.number_of_edges()}")
    
    node_types = {}
    for node, attrs in graph.nodes(data=True):
        node_type = attrs.get('type', 'Unknown').split(' - ')[-1]
        node_types[node_type] = node_types.get(node_type, 0) + 1
    
    print(f"  Node Types:")
    for node_type, count in node_types.items():
        print(f"    {node_type}: {count}")
    
    # Print position statistics
    print(f"\nPosition Statistics:")
    x_coords = [attrs['x'] for _, attrs in graph.nodes(data=True)]
    y_coords = [attrs['y'] for _, attrs in graph.nodes(data=True)]
    z_coords = [attrs['z'] for _, attrs in graph.nodes(data=True)]
    
    print(f"  X range: {min(x_coords):.1f} to {max(x_coords):.1f} m")
    print(f"  Y range: {min(y_coords):.1f} to {max(y_coords):.1f} m")
    print(f"  Z range: {min(z_coords):.1f} to {max(z_coords):.1f} m")
    
    # Print cable distance statistics
    cable_distances = []
    for _, _, attrs in graph.edges(data=True):
        if 'cable_distance' in attrs:
            cable_distances.append(attrs['cable_distance'])
    
    if cable_distances:
        print(f"\nCable Distance Statistics:")
        print(f"  Average distance: {sum(cable_distances)/len(cable_distances):.1f} m")
        print(f"  Max distance: {max(cable_distances):.1f} m")
        print(f"  Min distance: {min(cable_distances):.1f} m")
    
    # Print room assignment statistics
    print(f"\nRoom Assignment Statistics:")
    room_assignments = {}
    room_types = {}
    for node, attrs in graph.nodes(data=True):
        room = attrs.get('room', 'Unknown')
        room_assignments[room] = room_assignments.get(room, 0) + 1
        
        # Extract room type from room code
        if '-' in room:
            room_type = room.split('-')[0]
        else:
            room_type = 'OTHER'
        room_types[room_type] = room_types.get(room_type, 0) + 1
    
    print(f"  Room types:")
    for room_type, count in sorted(room_types.items()):
        print(f"    {room_type}: {count} equipment")
    
    print(f"  Sample room assignments:")
    sample_rooms = list(room_assignments.items())[:8]  # Show first 8 rooms
    for room, count in sample_rooms:
        print(f"    {room}: {count} equipment")


if __name__ == "__main__":
    main()
