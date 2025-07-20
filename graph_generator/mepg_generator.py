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
from typing import List, Dict, Tuple, Any, Optional
from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class ElectricalRequirement:
    """Represents an electrical requirement that drives node creation."""
    load_kw: float
    voltage_level: str  # 'high', 'medium', 'low'
    location: Tuple[float, float, float]  # x, y, z
    load_type: str  # 'lighting', 'power', 'hvac', etc.
    floor: int
    room: str
    priority: int = 1  # 1=critical, 2=important, 3=normal

@dataclass
class NodeDecision:
    """Represents a logical decision about what type of node to create."""
    node_type: str  # 'transformer', 'switchboard', 'panelboard', 'load'
    subtype: str    # 'main', 'secondary', etc.
    reason: str
    capacity_kw: float
    floor: int
    location: Tuple[float, float, float]
    serves_requirements: List[ElectricalRequirement]
    electrical_characteristics: Dict = None
    decision_id: int = 0  # Unique identifier for hashing
    
    def __post_init__(self):
        if not hasattr(NodeDecision, '_id_counter'):
            NodeDecision._id_counter = 0
        NodeDecision._id_counter += 1
        object.__setattr__(self, 'decision_id', NodeDecision._id_counter)
    
    def __hash__(self):
        return hash(self.decision_id)


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
            'low': [208.0]  # Lowest voltage level - no 120V equipment
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
        """Define electrical rooms on each floor with adaptive multi-core strategy."""
        config = self.building_config
        electrical_rooms = {}
        
        # Determine electrical core strategy based on building characteristics
        core_strategy = self._determine_electrical_core_strategy()
        
        # Basement electrical room(s) - main service
        electrical_rooms[-1] = self._create_basement_electrical_rooms(core_strategy)
        
        # Electrical rooms on each floor based on strategy
        for floor in range(config['num_floors']):
            electrical_rooms[floor] = self._create_floor_electrical_rooms(floor, core_strategy)
        
        return electrical_rooms
    
    def _determine_electrical_core_strategy(self) -> Dict[str, any]:
        """Determine electrical core strategy based on building characteristics."""
        config = self.building_config
        
        # Calculate building aspect ratio and total floor area
        aspect_ratio = max(config['length'], config['width']) / min(config['length'], config['width'])
        floor_area = config['length'] * config['width']
        total_area = floor_area * config['num_floors']
        height = config['num_floors'] * config['floor_height']
        
        # Strategy decision criteria:
        # - Single core: Tall/compact buildings (height > 30m OR aspect_ratio < 2.0)
        # - Dual core: Medium buildings (height 15-30m AND aspect_ratio 2.0-3.5)
        # - Multi core: Low/wide buildings (height < 15m OR aspect_ratio > 3.5)
        
        if height > 30.0 or (aspect_ratio < 2.0 and config['num_floors'] > 6):
            strategy_type = 'single_core'
            num_cores = 1
        elif height >= 15.0 and aspect_ratio <= 3.5:
            strategy_type = 'dual_core'
            num_cores = 2
        else:
            strategy_type = 'multi_core'
            # For multi-core, base number on floor area (1 core per 1000-1500 sqm)
            num_cores = max(2, min(4, int(floor_area / 1200)))
        
        return {
            'type': strategy_type,
            'num_cores': num_cores,
            'core_positions': self._calculate_core_positions(num_cores),
            'aspect_ratio': aspect_ratio,
            'floor_area': floor_area,
            'building_height': height
        }
    
    def _calculate_core_positions(self, num_cores: int) -> List[Dict[str, float]]:
        """Calculate optimal positions for electrical cores."""
        config = self.building_config
        positions = []
        
        if num_cores == 1:
            # Single central core
            positions.append({
                'x_center': config['length'] / 2,
                'y_center': config['width'] / 2,
                'core_id': 'A'
            })
        
        elif num_cores == 2:
            # Two cores along the longer dimension
            if config['length'] > config['width']:
                # Split along length
                positions.extend([
                    {
                        'x_center': config['length'] * 0.3,
                        'y_center': config['width'] / 2,
                        'core_id': 'A'
                    },
                    {
                        'x_center': config['length'] * 0.7,
                        'y_center': config['width'] / 2,
                        'core_id': 'B'
                    }
                ])
            else:
                # Split along width
                positions.extend([
                    {
                        'x_center': config['length'] / 2,
                        'y_center': config['width'] * 0.3,
                        'core_id': 'A'
                    },
                    {
                        'x_center': config['length'] / 2,
                        'y_center': config['width'] * 0.7,
                        'core_id': 'B'
                    }
                ])
        
        elif num_cores == 3:
            # Three cores in triangular arrangement
            positions.extend([
                {
                    'x_center': config['length'] * 0.25,
                    'y_center': config['width'] * 0.3,
                    'core_id': 'A'
                },
                {
                    'x_center': config['length'] * 0.75,
                    'y_center': config['width'] * 0.3,
                    'core_id': 'B'
                },
                {
                    'x_center': config['length'] * 0.5,
                    'y_center': config['width'] * 0.7,
                    'core_id': 'C'
                }
            ])
        
        else:  # 4 or more cores
            # Four cores in quadrant arrangement
            positions.extend([
                {
                    'x_center': config['length'] * 0.25,
                    'y_center': config['width'] * 0.25,
                    'core_id': 'A'
                },
                {
                    'x_center': config['length'] * 0.75,
                    'y_center': config['width'] * 0.25,
                    'core_id': 'B'
                },
                {
                    'x_center': config['length'] * 0.25,
                    'y_center': config['width'] * 0.75,
                    'core_id': 'C'
                },
                {
                    'x_center': config['length'] * 0.75,
                    'y_center': config['width'] * 0.75,
                    'core_id': 'D'
                }
            ])
        
        return positions
    
    def _create_basement_electrical_rooms(self, core_strategy: Dict) -> List[Dict]:
        """Create basement electrical rooms based on core strategy."""
        config = self.building_config
        basement_rooms = []
        
        if core_strategy['num_cores'] == 1:
            # Single large main electrical room
            core_pos = core_strategy['core_positions'][0]
            basement_rooms.append({
                'id': 'MER-B01',
                'description': 'Main Electrical Room',
                'core_id': core_pos['core_id'],
                'x_min': core_pos['x_center'] - config['electrical_core']['width'] / 2,
                'x_max': core_pos['x_center'] + config['electrical_core']['width'] / 2,
                'y_min': core_pos['y_center'] - config['electrical_core']['depth'] / 2,
                'y_max': core_pos['y_center'] + config['electrical_core']['depth'] / 2,
                'equipment_types': ['main_transformer', 'main_switchboard'],
                'capacity': 6
            })
        
        else:
            # Multiple electrical rooms for multi-core strategy
            for i, core_pos in enumerate(core_strategy['core_positions']):
                room_size_factor = 0.8  # Smaller rooms for multi-core
                basement_rooms.append({
                    'id': f'MER-B0{i+1}',
                    'description': f'Main Electrical Room {core_pos["core_id"]}',
                    'core_id': core_pos['core_id'],
                    'x_min': core_pos['x_center'] - (config['electrical_core']['width'] * room_size_factor) / 2,
                    'x_max': core_pos['x_center'] + (config['electrical_core']['width'] * room_size_factor) / 2,
                    'y_min': core_pos['y_center'] - (config['electrical_core']['depth'] * room_size_factor) / 2,
                    'y_max': core_pos['y_center'] + (config['electrical_core']['depth'] * room_size_factor) / 2,
                    'equipment_types': ['main_transformer', 'main_switchboard'],
                    'capacity': 4
                })
        
        return basement_rooms
    
    def _create_floor_electrical_rooms(self, floor: int, core_strategy: Dict) -> List[Dict]:
        """Create electrical rooms for a specific floor based on core strategy."""
        config = self.building_config
        rooms = []
        
        for i, core_pos in enumerate(core_strategy['core_positions']):
            core_id = core_pos['core_id']
            
            # Primary electrical closet for each core
            rooms.append({
                'id': f'EC-{floor:02d}{core_id}',
                'description': f'Electrical Closet {core_id} - Floor {floor}',
                'core_id': core_id,
                'x_min': core_pos['x_center'] - 4.0,
                'x_max': core_pos['x_center'] + 4.0,
                'y_min': core_pos['y_center'] - 3.0,
                'y_max': core_pos['y_center'] + 3.0,
                'equipment_types': ['secondary_transformer', 'main_panelboard'],
                'capacity': 3
            })
            
            # Secondary electrical closet (offset from core)
            offset_x = 6.0 if i % 2 == 0 else -6.0
            offset_y = 4.0 if i < 2 else -4.0
            
            rooms.append({
                'id': f'EC-{floor:02d}{core_id}-2',
                'description': f'Secondary Electrical Closet {core_id} - Floor {floor}',
                'core_id': core_id,
                'x_min': core_pos['x_center'] + offset_x - 2.0,
                'x_max': core_pos['x_center'] + offset_x + 2.0,
                'y_min': core_pos['y_center'] + offset_y - 2.0,
                'y_max': core_pos['y_center'] + offset_y + 2.0,
                'equipment_types': ['panelboard'],
                'capacity': 2
            })
        
        # Add IDF rooms for floors above ground level
        if floor > 0 and core_strategy['num_cores'] >= 2:
            # Distribute IDF rooms based on available cores
            idf_positions = [
                {'x': config['length'] * 0.1, 'y': config['width'] * 0.1},
                {'x': config['length'] * 0.9, 'y': config['width'] * 0.1},
                {'x': config['length'] * 0.1, 'y': config['width'] * 0.9},
                {'x': config['length'] * 0.9, 'y': config['width'] * 0.9}
            ]
            
            for j, idf_pos in enumerate(idf_positions[:min(2, core_strategy['num_cores'])]):
                rooms.append({
                    'id': f'IDF-{floor:02d}-{j+1}',
                    'description': f'IDF Room {j+1} - Floor {floor}',
                    'core_id': f'IDF{j+1}',
                    'x_min': idf_pos['x'] - 2.0,
                    'x_max': idf_pos['x'] + 2.0,
                    'y_min': idf_pos['y'] - 2.0,
                    'y_max': idf_pos['y'] + 2.0,
                    'equipment_types': ['panelboard'],
                    'capacity': 2
                })
        
        return rooms
    
    def generate_graph(self, node_count: int) -> nx.DiGraph:
        """
        Generate a logical electrical system graph using demand-driven approach.
        
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
        
        # Step 1: Analyze building electrical requirements
        building_requirements = self._analyze_building_electrical_requirements()
        
        # Step 2: Generate logical node decisions based on requirements
        node_decisions = self._generate_logical_node_decisions(building_requirements, node_count)
        
        # Step 3: Create nodes and connections from decisions
        G = self._build_graph_from_logical_decisions(G, node_decisions)
        
        # Step 4: Update voltages to ensure proper step-down relationships
        self._update_voltage_relationships(G)
        
        # Step 5: Validate electrical constraints
        self._validate_electrical_constraints(G)
        
        # Step 5.5: Validate load connections (ensure each load has exactly one feeding panelboard)
        self._validate_load_connections(G)

        # Step 6: Align transformer positions with upstream or downstream node
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
    
    def _analyze_building_electrical_requirements(self) -> List[ElectricalRequirement]:
        """Analyze building characteristics to generate electrical requirements."""
        requirements = []
        config = self.building_config
        
        # Calculate floor area for load density calculations
        floor_area = config['length'] * config['width']
        
        # Standard electrical load densities (W/sf)
        load_densities = {
            'lighting': 1.5,      # 1.5 W/sf for LED lighting
            'general_power': 3.0, # 3.0 W/sf for general receptacles
            'hvac': 2.0,         # 2.0 W/sf for HVAC systems
            'kitchen': 8.0,      # 8.0 W/sf for kitchen equipment (if applicable)
            'data_center': 50.0  # 50 W/sf for high-density areas
        }
        
        # Generate requirements for each floor
        for floor in range(-1, config['num_floors']):
            
            if floor == -1:  # Basement - mechanical and service equipment
                # Main service requirement
                total_building_load = self._estimate_total_building_load(floor_area, config['num_floors'])
                requirements.append(ElectricalRequirement(
                    load_kw=total_building_load,
                    voltage_level='high',
                    location=self._get_electrical_core_location(floor),
                    load_type='main_service',
                    floor=floor,
                    room='MER-B01',
                    priority=1
                ))
                
                # Mechanical equipment
                mech_load = floor_area * load_densities['hvac'] / 1000  # Convert to kW
                requirements.append(ElectricalRequirement(
                    load_kw=mech_load,
                    voltage_level='medium',
                    location=self._get_mechanical_room_location(floor),
                    load_type='hvac',
                    floor=floor,
                    room=f'MECH-{floor:02d}',
                    priority=1
                ))
                
            else:  # Upper floors - office/commercial loads
                # Lighting loads
                lighting_load = floor_area * load_densities['lighting'] / 1000
                requirements.append(ElectricalRequirement(
                    load_kw=lighting_load,
                    voltage_level='low',
                    location=self._get_distributed_floor_location(floor),
                    load_type='lighting',
                    floor=floor,
                    room=f'GENERAL-{floor:02d}',
                    priority=2
                ))
                
                # General power loads
                power_load = floor_area * load_densities['general_power'] / 1000
                requirements.append(ElectricalRequirement(
                    load_kw=power_load,
                    voltage_level='low',
                    location=self._get_distributed_floor_location(floor),
                    load_type='general_power',
                    floor=floor,
                    room=f'GENERAL-{floor:02d}',
                    priority=2
                ))
                
                # Special loads for certain floors
                if floor % 3 == 0:  # Every third floor has kitchen/break room
                    kitchen_load = 200.0 * load_densities['kitchen'] / 1000  # 200 sf kitchen
                    requirements.append(ElectricalRequirement(
                        load_kw=kitchen_load,
                        voltage_level='low',
                        location=self._get_special_room_location(floor, 'kitchen'),
                        load_type='kitchen',
                        floor=floor,
                        room=f'KITCHEN-{floor:02d}',
                        priority=2
                    ))
                
                if floor == config['num_floors'] - 1:  # Top floor has data center
                    dc_load = 500.0 * load_densities['data_center'] / 1000  # 500 sf data center
                    requirements.append(ElectricalRequirement(
                        load_kw=dc_load,
                        voltage_level='medium',
                        location=self._get_special_room_location(floor, 'data_center'),
                        load_type='data_center',
                        floor=floor,
                        room=f'DC-{floor:02d}',
                        priority=1
                    ))
        
        return requirements
    
    def _generate_logical_node_decisions(self, requirements: List[ElectricalRequirement], 
                                       target_node_count: int) -> List[NodeDecision]:
        """Generate logical decisions about what nodes to create based on requirements."""
        decisions = []
        
        # Step 1: Analyze total load to determine main service requirements
        total_load = sum(req.load_kw for req in requirements)
        main_service_req = next((req for req in requirements if req.load_type == 'main_service'), None)
        
        if main_service_req and total_load > 100:  # Lowered threshold to 100kW for testing
            decisions.append(NodeDecision(
                node_type='transformer',
                subtype='main',
                reason=f"Main service transformer for {total_load:.0f}kW building load",
                capacity_kw=total_load * 1.25,  # 25% safety factor
                floor=-1,
                location=main_service_req.location,
                serves_requirements=[main_service_req]
            ))
            
            decisions.append(NodeDecision(
                node_type='switchboard',
                subtype='main',
                reason="Main service switchboard for distribution",
                capacity_kw=total_load * 1.2,
                floor=-1,
                location=main_service_req.location,
                serves_requirements=[main_service_req]
            ))
        
        # Step 2: Group requirements by floor and voltage for distribution planning
        floor_groups = {}
        for req in requirements:
            if req.floor not in floor_groups:
                floor_groups[req.floor] = {'medium': [], 'low': []}
            
            voltage_key = req.voltage_level if req.voltage_level in ['medium', 'low'] else 'medium'
            floor_groups[req.floor][voltage_key].append(req)
        
        # Step 3: Create distribution equipment decisions
        for floor, voltage_groups in floor_groups.items():
            if floor == -1:  # Skip basement, already handled
                continue
                
            # Medium voltage loads (HVAC, large equipment)
            medium_loads = voltage_groups.get('medium', [])
            if medium_loads:
                total_medium_load = sum(req.load_kw for req in medium_loads)
                
                if total_medium_load > 75:  # Needs secondary transformer
                    decisions.append(NodeDecision(
                        node_type='transformer',
                        subtype='secondary',
                        reason=f"Secondary transformer for {total_medium_load:.0f}kW medium voltage loads on floor {floor}",
                        capacity_kw=total_medium_load * 1.3,
                        floor=floor,
                        location=self._get_electrical_closet_location(floor),
                        serves_requirements=medium_loads
                    ))
                
                decisions.append(NodeDecision(
                    node_type='panelboard',
                    subtype='distribution',
                    reason=f"Distribution panel for medium voltage loads on floor {floor}",
                    capacity_kw=total_medium_load * 1.2,
                    floor=floor,
                    location=self._get_electrical_closet_location(floor),
                    serves_requirements=medium_loads
                ))
            
            # Low voltage loads (lighting, power)
            low_loads = voltage_groups.get('low', [])
            if low_loads:
                total_low_load = sum(req.load_kw for req in low_loads)
                
                # Determine number of panelboards needed based on load and layout
                num_panels = max(1, min(3, int(total_low_load / 40)))  # 40kW per panel max
                
                load_per_panel = total_low_load / num_panels
                loads_per_panel = [low_loads[i::num_panels] for i in range(num_panels)]
                
                for i, panel_loads in enumerate(loads_per_panel):
                    if panel_loads:  # Only create panel if it has loads
                        decisions.append(NodeDecision(
                            node_type='panelboard',
                            subtype='lighting' if any(req.load_type == 'lighting' for req in panel_loads) else 'power',
                            reason=f"Panel {i+1} for {load_per_panel:.0f}kW low voltage loads on floor {floor}",
                            capacity_kw=load_per_panel * 1.25,
                            floor=floor,
                            location=self._get_electrical_closet_location(floor, i),
                            serves_requirements=panel_loads
                        ))
        
        # Step 4: Create individual load decisions
        for req in requirements:
            if req.load_type not in ['main_service']:  # Skip service requirements, already handled
                decisions.append(NodeDecision(
                    node_type='load',
                    subtype=req.load_type,
                    reason=f"{req.load_type} load ({req.load_kw:.1f}kW) on floor {req.floor}",
                    capacity_kw=req.load_kw,
                    floor=req.floor,
                    location=req.location,
                    serves_requirements=[req]
                ))
        
        # Step 5: Adjust decisions to meet target node count
        decisions = self._adjust_decisions_to_target_count(decisions, target_node_count)
        
        return decisions
    
    def _build_graph_from_logical_decisions(self, G: nx.DiGraph, decisions: List[NodeDecision]) -> nx.DiGraph:
        """Build the actual graph from logical decisions."""
        node_id_counter = 1
        decision_to_node_id = {}
        
        # Create nodes from decisions
        for decision in decisions:
            node_id = f"{decision.node_type}_{node_id_counter:03d}"
            decision_to_node_id[decision] = node_id
            node_id_counter += 1
            
            # Create node based on its type
            if decision.node_type == 'transformer':
                self._add_logical_transformer_node(G, node_id, decision)
            elif decision.node_type == 'switchboard':
                self._add_logical_switchboard_node(G, node_id, decision)
            elif decision.node_type == 'panelboard':
                self._add_logical_panelboard_node(G, node_id, decision)
            elif decision.node_type == 'load':
                self._add_logical_load_node(G, node_id, decision)
        
        # Create logical connections between nodes
        self._create_logical_connections_from_decisions(G, decisions, decision_to_node_id)
        
        return G
    
    def _add_logical_transformer_node(self, G: nx.DiGraph, node_id: str, decision: NodeDecision):
        """Add a transformer node based on logical decision."""
        x, y, z = decision.location
        room_code = self._get_room_code_for_floor_and_type(decision.floor, 'transformer')
        
        performance = f"{decision.capacity_kw:.0f} kVA"
        
        if decision.subtype == 'main':
            upstream_voltage = self.selected_high_voltage
            downstream_voltage = self.voltage_levels['medium'][0]
        else:  # secondary
            upstream_voltage = self.voltage_levels['medium'][0]
            downstream_voltage = self.voltage_levels['low'][0]
        
        attrs = {
            'type': self.component_types['transformer'],
            'x': x, 'y': y, 'z': z,
            'room': room_code,
            'floor': decision.floor,
            'Identifier': f"Transformer-{node_id.split('_')[1]}",
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
            'distribution_downstream_current_rating': self._calculate_current_rating(downstream_voltage, performance),
            'distribution_downstream_phase_number': 3,
            'distribution_downstream_frequency': 60.0,
            'AIC_rating': round(random.uniform(22.0, 65.0), 1),
            'generation_reason': decision.reason,
            'serves_load_kw': decision.capacity_kw
        }
        
        G.add_node(node_id, **attrs)
    
    def _add_logical_switchboard_node(self, G: nx.DiGraph, node_id: str, decision: NodeDecision):
        """Add a switchboard node based on logical decision."""
        x, y, z = decision.location
        room_code = self._get_room_code_for_floor_and_type(decision.floor, 'switchboard')
        
        attrs = {
            'type': self.component_types['switchboard'],
            'x': x, 'y': y, 'z': z,
            'room': room_code,
            'floor': decision.floor,
            'Identifier': f"Switchboard-{node_id.split('_')[1]}",
            'Manufacturer': random.choice(self.manufacturers),
            'Operating_company_department': 'Facilities',
            'Owner': random.choice(['Building Owner', 'Tenant', 'Management Company']),
            'Nominal_current': round(decision.capacity_kw / 480.0 * 1000 / 1.732, 1),  # Rough 3-phase current
            'Short-circuit_strength_kA': round(random.uniform(25.0, 65.0), 1),
            'Physical_Height_mm': float(random.randint(*self.physical_dims['switchboard']['height'])),
            'Physical_Length_mm': float(random.randint(*self.physical_dims['switchboard']['length'])),
            'Physical_Width_mm': float(random.randint(*self.physical_dims['switchboard']['width'])),
            'Warranty_months': random.choice([24, 36, 60]),
            'Year_of_manufacture': random.randint(2018, 2024),
            'Year_of_installation': random.randint(2018, 2024),
            'Outdoor_rated': random.choice([True, False]),
            'distribution_upstream_voltage': None,  # Will be set by propagation
            'distribution_upstream_current_rating': round(decision.capacity_kw / 480.0 * 1000 / 1.732, 1),
            'distribution_upstream_phase_number': 3,
            'distribution_upstream_frequency': 60.0,
            'distribution_downstream_voltage': None,  # Will be set by propagation
            'distribution_downstream_current_rating': round(decision.capacity_kw / 480.0 * 1000 / 1.732 * 0.8, 1),
            'distribution_downstream_phase_number': 3,
            'distribution_downstream_frequency': 60.0,
            'AIC_rating': round(random.uniform(42.0, 65.0), 1),
            'generation_reason': decision.reason,
            'serves_load_kw': decision.capacity_kw
        }
        
        G.add_node(node_id, **attrs)
    
    def _add_logical_panelboard_node(self, G: nx.DiGraph, node_id: str, decision: NodeDecision):
        """Add a panelboard node based on logical decision."""
        x, y, z = decision.location
        room_code = self._get_room_code_for_floor_and_type(decision.floor, 'panelboard')
        
        attrs = {
            'type': self.component_types['panelboard'],
            'x': x, 'y': y, 'z': z,
            'room': room_code,
            'floor': decision.floor,
            'Identifier': f"Panelboard-{node_id.split('_')[1]}",
            'Manufacturer': random.choice(self.manufacturers),
            'Masked_yes_no': random.choice([True, False]),
            'Mounting_method': random.choice(self.mounting_methods),
            'Nominal_current': round(decision.capacity_kw / 208.0 * 1000, 1),  # Single phase assumption
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
            'distribution_upstream_voltage': None,  # Will be set by propagation
            'distribution_upstream_current_rating': round(decision.capacity_kw / 208.0 * 1000, 1),
            'distribution_upstream_phase_number': 3,
            'distribution_upstream_frequency': 60.0,
            'distribution_downstream_voltage': None,  # Will be set by propagation
            'distribution_downstream_current_rating': round(decision.capacity_kw / 208.0 * 1000 * 0.8, 1),
            'distribution_downstream_phase_number': 1,
            'distribution_downstream_frequency': 60.0,
            'AIC_rating': round(random.uniform(10.0, 25.0), 1),
            'generation_reason': decision.reason,
            'serves_load_kw': decision.capacity_kw,
            'panel_type': decision.subtype
        }
        
        G.add_node(node_id, **attrs)
    
    def _add_logical_load_node(self, G: nx.DiGraph, node_id: str, decision: NodeDecision):
        """Add a load node based on logical decision."""
        x, y, z = decision.location
        room_code = decision.serves_requirements[0].room if decision.serves_requirements else f"ROOM-{decision.floor:02d}"
        
        attrs = {
            'type': self.component_types['load'],
            'x': x, 'y': y, 'z': z,
            'room': room_code,
            'floor': decision.floor,
            'Identifier': f"Load-{node_id.split('_')[1]}",
            'Manufacturer': random.choice(self.manufacturers),
            'Nominal_current': round(decision.capacity_kw / 208.0 * 1000, 1),
            'Physical_Height_mm': float(random.randint(*self.physical_dims['load']['height'])),
            'Physical_Length_mm': float(random.randint(*self.physical_dims['load']['length'])),
            'Physical_Width_mm': float(random.randint(*self.physical_dims['load']['width'])),
            'Voltage': "TBD",  # Will be set by propagation
            'Warranty_months': random.choice([12, 24, 36]),
            'Year_of_manufacture': random.randint(2018, 2024),
            'Year_of_installation': random.randint(2018, 2024),
            'distribution_upstream_voltage': None,  # Will be set by propagation
            'distribution_upstream_current_rating': round(decision.capacity_kw / 208.0 * 1000, 1),
            'distribution_upstream_phase_number': 1,
            'distribution_upstream_frequency': 60.0,
            'generation_reason': decision.reason,
            'load_kw': decision.capacity_kw,
            'load_type': decision.subtype
        }
        
        G.add_node(node_id, **attrs)
    
    def _create_logical_connections_from_decisions(self, G: nx.DiGraph, decisions: List[NodeDecision], 
                                                 decision_to_node_id: Dict[NodeDecision, str]):
        """Create logical connections between nodes based on electrical hierarchy."""
        
        # Group decisions by type and hierarchy
        transformers = [d for d in decisions if d.node_type == 'transformer']
        switchboards = [d for d in decisions if d.node_type == 'switchboard']
        panelboards = [d for d in decisions if d.node_type == 'panelboard']
        loads = [d for d in decisions if d.node_type == 'load']
        
        edge_id = 1
        
        # Step 1: Connect transformers to switchboards
        main_transformer = next((t for t in transformers if t.subtype == 'main'), None)
        main_switchboard = next((s for s in switchboards if s.subtype == 'main'), None)
        
        if main_transformer and main_switchboard:
            self._add_connection(G, f"connection_{edge_id:03d}", 
                               decision_to_node_id[main_transformer], 
                               decision_to_node_id[main_switchboard], 
                               'Main Distribution')
            edge_id += 1
        
        # Step 2: Connect main switchboard to secondary transformers on other floors
        if main_switchboard:
            secondary_transformers = [t for t in transformers if t.subtype == 'secondary']
            for transformer in secondary_transformers:
                self._add_connection(G, f"connection_{edge_id:03d}", 
                                   decision_to_node_id[main_switchboard], 
                                   decision_to_node_id[transformer], 
                                   'Floor Distribution')
                edge_id += 1
        
        # Step 3: Connect transformers to panelboards on same floor
        for transformer in transformers:
            if transformer.subtype == 'secondary':
                # Connect to panelboards on same floor
                floor_panelboards = [p for p in panelboards if p.floor == transformer.floor]
                for panelboard in floor_panelboards:
                    self._add_connection(G, f"connection_{edge_id:03d}", 
                                       decision_to_node_id[transformer], 
                                       decision_to_node_id[panelboard], 
                                       'Secondary Distribution')
                    edge_id += 1
        
        # Step 4: Connect main switchboard directly to panelboards on floors without transformers
        if main_switchboard:
            transformer_floors = set(t.floor for t in transformers if t.subtype == 'secondary')
            
            for panelboard in panelboards:
                if panelboard.floor not in transformer_floors and panelboard.floor != -1:
                    self._add_connection(G, f"connection_{edge_id:03d}", 
                                       decision_to_node_id[main_switchboard], 
                                       decision_to_node_id[panelboard], 
                                       'Direct Distribution')
                    edge_id += 1
        
        # Step 5: Connect loads to closest panelboards (ensure each load has only one connection)
        connected_loads = set()  # Track which loads have been connected
        
        for load in loads:
            if load in connected_loads:
                continue  # Skip if already connected
                
            # Find the closest panelboard regardless of floor
            if panelboards:
                closest_panelboard = min(panelboards, 
                                       key=lambda p: self._calculate_decision_distance(load, p))
                load_type = load.subtype.replace('_', ' ').title()
                self._add_connection(G, f"connection_{edge_id:03d}", 
                                   decision_to_node_id[closest_panelboard], 
                                   decision_to_node_id[load], 
                                   load_type)
                edge_id += 1
                connected_loads.add(load)

    def _calculate_decision_distance(self, load_decision: NodeDecision, panel_decision: NodeDecision) -> float:
        """Calculate distance between two node decisions based on their locations."""
        load_x, load_y, load_z = load_decision.location
        panel_x, panel_y, panel_z = panel_decision.location
        
        dx = load_x - panel_x
        dy = load_y - panel_y
        dz = load_z - panel_z
        
        return (dx*dx + dy*dy + dz*dz)**0.5
    
    # Helper methods for the logical generation
    def _estimate_total_building_load(self, floor_area: float, num_floors: int) -> float:
        """Estimate total building electrical load."""
        # Typical office building: 4-6 W/sf
        load_density = 5.0  # W/sf
        total_load = floor_area * num_floors * load_density / 1000  # Convert to kW
        return total_load
    
    def _get_electrical_core_location(self, floor: int) -> Tuple[float, float, float]:
        """Get location in electrical core."""
        config = self.building_config
        return (
            config['electrical_core']['x_center'],
            config['electrical_core']['y_center'],
            self.floor_levels[floor]['z_center']
        )
    
    def _get_mechanical_room_location(self, floor: int) -> Tuple[float, float, float]:
        """Get mechanical room location."""
        config = self.building_config
        return (
            config['electrical_core']['x_center'] + random.uniform(-4, 4),
            config['electrical_core']['y_center'] + random.uniform(-4, 4),
            self.floor_levels[floor]['z_center']
        )
    
    def _get_distributed_floor_location(self, floor: int) -> Tuple[float, float, float]:
        """Get distributed location on floor."""
        config = self.building_config
        return (
            random.uniform(10, config['length'] - 10),
            random.uniform(10, config['width'] - 10),
            self.floor_levels[floor]['z_center'] + random.uniform(0, 2)
        )
    
    def _get_special_room_location(self, floor: int, room_type: str) -> Tuple[float, float, float]:
        """Get location for special rooms."""
        config = self.building_config
        
        if room_type == 'kitchen':
            # Kitchens typically in core area
            x = config['electrical_core']['x_center'] + random.uniform(-8, 8)
            y = config['electrical_core']['y_center'] + random.uniform(-6, 6)
        elif room_type == 'data_center':
            # Data centers typically in secure areas
            x = config['length'] * 0.8
            y = config['width'] * 0.2
        else:
            x = random.uniform(10, config['length'] - 10)
            y = random.uniform(10, config['width'] - 10)
        
        return (x, y, self.floor_levels[floor]['z_center'])
    
    def _get_electrical_closet_location(self, floor: int, closet_number: int = 0) -> Tuple[float, float, float]:
        """Get electrical closet location."""
        config = self.building_config
        
        # Multiple closets on larger floors
        if closet_number == 0:
            x = config['electrical_core']['x_center'] + random.uniform(-2, 2)
            y = config['electrical_core']['y_center'] + random.uniform(-2, 2)
        else:
            # Distribute additional closets around the floor
            x = config['length'] * (0.2 + closet_number * 0.3)
            y = config['width'] * (0.2 + closet_number * 0.3)
        
        return (x, y, self.floor_levels[floor]['z_center'])
    
    def _get_room_code_for_floor_and_type(self, floor: int, equipment_type: str) -> str:
        """Get appropriate room code for equipment type and floor."""
        if equipment_type in ['transformer', 'switchboard'] and floor == -1:
            return 'MER-B01'
        elif equipment_type in ['transformer', 'panelboard']:
            return f'EC-{floor:02d}A'
        else:
            return f'ELEC-{floor:02d}'
    
    def _adjust_decisions_to_target_count(self, decisions: List[NodeDecision], 
                                        target_count: int) -> List[NodeDecision]:
        """Adjust number of decisions to approximately match target node count."""
        current_count = len(decisions)
        
        if current_count < target_count:
            # Add more distribution equipment
            needed = target_count - current_count
            for i in range(needed):
                floor = random.randint(0, self.building_config['num_floors'] - 1)
                decisions.append(NodeDecision(
                    node_type='panelboard',
                    subtype='additional',
                    reason=f"Additional distribution panel {i+1} for load balancing",
                    capacity_kw=random.uniform(20, 50),
                    floor=floor,
                    location=self._get_electrical_closet_location(floor, i % 3),
                    serves_requirements=[]
                ))
        elif current_count > target_count:
            # Remove some of the smaller loads
            loads = [d for d in decisions if d.node_type == 'load']
            infrastructure = [d for d in decisions if d.node_type != 'load']
            
            # Keep infrastructure, reduce loads
            loads_to_keep = target_count - len(infrastructure)
            if loads_to_keep > 0:
                loads.sort(key=lambda x: x.capacity_kw, reverse=True)
                decisions = infrastructure + loads[:loads_to_keep]
            else:
                decisions = infrastructure[:target_count]
        
        return decisions
    
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
            # Main transformer: Set upstream to selected high voltage, downstream will be updated by propagation
            upstream_voltage = self.selected_high_voltage
            downstream_voltage = self.voltage_levels['medium'][0]  # 480V - will be verified by propagation
            performance = random.choice(['1000 kVA', '1500 kVA', '2000 kVA', '2500 kVA'])
        else:  # secondary
            # Secondary transformer: Voltages will be set by propagation based on actual connections
            upstream_voltage = None  # Will be set by propagation
            downstream_voltage = None  # Will be set by propagation
            performance = random.choice(['150 kVA', '225 kVA', '300 kVA', '500 kVA'])
        
        # Calculate current rating if we have voltages, otherwise use placeholder
        if downstream_voltage:
            current_rating = self._calculate_current_rating(downstream_voltage, performance)
            upstream_current = self._calculate_current_rating(upstream_voltage, performance) if upstream_voltage else 0.0
        else:
            current_rating = 0.0  # Will be updated by propagation
            upstream_current = 0.0
        
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
            'Voltage': f"{upstream_voltage/1000:.1f} kV" if upstream_voltage and upstream_voltage >= 1000 else f"{upstream_voltage:.0f} V" if upstream_voltage else "TBD",
            'Warranty_months': random.choice([24, 36, 60, 120]),
            'Year_of_manufacture': random.randint(2018, 2024),
            'Year_of_installation': random.randint(2018, 2024),
            'distribution_upstream_voltage': upstream_voltage,
            'distribution_upstream_current_rating': upstream_current,
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
        # Voltage will be set by propagation based on upstream connection
        
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
            'distribution_upstream_voltage': None,  # Will be set by propagation
            'distribution_upstream_current_rating': round(random.uniform(1000.0, 4000.0), 1),
            'distribution_upstream_phase_number': 3,
            'distribution_upstream_frequency': 60.0,
            'distribution_downstream_voltage': None,  # Will be set by propagation
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
        # Voltage will be set by propagation based on upstream connection
        
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
            'distribution_upstream_voltage': None,  # Will be set by propagation
            'distribution_upstream_current_rating': round(random.uniform(100.0, 800.0), 1),
            'distribution_upstream_phase_number': 3,
            'distribution_upstream_frequency': 60.0,
            'distribution_downstream_voltage': None,  # Will be set by propagation
            'distribution_downstream_current_rating': round(random.uniform(80.0, 600.0), 1),
            'distribution_downstream_phase_number': 1,  # Panelboards can supply single-phase to loads
            'distribution_downstream_frequency': 60.0,
            'AIC_rating': round(random.uniform(10.0, 25.0), 1)
        }
        
        G.add_node(node_id, **attrs)
    
    def _add_load_node_on_floor(self, G: nx.DiGraph, node_id: str, position_id: int, floor: int):
        """Add a load node distributed around the floor, outside electrical rooms."""
        x, y, z = self._generate_position_outside_electrical_rooms(node_id, position_id, floor)
        room_code = self._get_room_code_for_position(floor, x, y, 'load')
        # Voltage will be set by propagation based on upstream panelboard
        
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
            'Voltage': "TBD",  # Will be set by propagation
            'Warranty_months': random.choice([12, 24, 36]),
            'Year_of_manufacture': random.randint(2018, 2024),
            'Year_of_installation': random.randint(2018, 2024),
            'distribution_upstream_voltage': None,  # Will be set by propagation
            'distribution_upstream_current_rating': round(random.uniform(10.0, 100.0), 1),
            'distribution_upstream_phase_number': 1,  # Loads are typically single-phase
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
        
        # Track equipment that can serve upper floors (switchboards and panelboards only)
        feeding_equipment = basement_switchboards.copy()
        
        # Connect each floor in ascending order
        for floor in sorted([f for f in floor_nodes.keys() if f >= 0]):
            floor_equipment = floor_nodes[floor]
            floor_transformers = [n for n in floor_equipment if 'transformer' in n]
            floor_panelboards = [n for n in floor_equipment if 'panelboard' in n]
            floor_loads = [n for n in floor_equipment if 'load' in n]
            
            # Connect transformers on this floor to switchboards/panelboards (never to other transformers)
            for transformer in floor_transformers:
                if feeding_equipment:
                    # Only connect to switchboards or panelboards, not other transformers
                    valid_feeders = [f for f in feeding_equipment if 'transformer' not in f]
                    if valid_feeders:
                        closest_feeder = self._find_closest_equipment(G, transformer, valid_feeders)
                        if closest_feeder:
                            self._add_connection(G, f"connection_{edge_id:03d}", closest_feeder, transformer, 'Floor Distribution')
                            edge_id += 1
            
            # Connect each transformer to panelboards (transformers must feed panelboards)
            for transformer in floor_transformers:
                # Find panelboards on same floor that aren't connected yet
                available_panelboards = [pb for pb in floor_panelboards if not any(pred for pred in G.predecessors(pb))]
                if available_panelboards:
                    closest_panelboard = self._find_closest_equipment(G, transformer, available_panelboards)
                    if closest_panelboard:
                        self._add_connection(G, f"connection_{edge_id:03d}", transformer, closest_panelboard, 'Secondary Distribution')
                        edge_id += 1
            
            # Connect remaining panelboards to feeding equipment from below
            for panelboard in floor_panelboards:
                # Skip if already connected to a transformer
                if any('transformer' in pred for pred in G.predecessors(panelboard)):
                    continue
                    
                if feeding_equipment:
                    closest_source = self._find_closest_equipment(G, panelboard, feeding_equipment)
                    if closest_source:
                        load_type = random.choice(['Lighting', 'General Power', 'HVAC'])
                        self._add_connection(G, f"connection_{edge_id:03d}", closest_source, panelboard, load_type)
                        edge_id += 1
            
            # Connect loads to closest panelboards on same floor (ensure single connection per load)
            for load in floor_loads:
                # Check if load is already connected (avoid multiple connections)
                if G.in_degree(load) > 0:
                    continue  # Skip if already connected
                    
                if floor_panelboards:
                    closest_panelboard = self._find_closest_equipment(G, load, floor_panelboards)
                    if closest_panelboard:
                        load_type = random.choice(['Lighting', 'General Power', 'Motor Loads'])
                        self._add_connection(G, f"connection_{edge_id:03d}", closest_panelboard, load, load_type)
                        edge_id += 1
            
            # Add panelboards (not transformers) to feeding equipment for next floor
            feeding_equipment.extend(floor_panelboards)
    
    def _define_equipment_zones(self) -> Dict[str, Dict]:
        """Define realistic zones for different equipment types based on multi-core strategy."""
        config = self.building_config
        
        # Get the core strategy to determine zones dynamically
        core_strategy = self._determine_electrical_core_strategy()
        
        zones = {
            'main_electrical': {
                'description': 'Main electrical rooms (basement/ground floor)',
                'cores': [],  # Will be populated with core-specific ranges
                'z_range': (config['basement_depth'], config['floor_height']),
                'equipment': ['main_transformer', 'main_switchboard']
            },
            
            'floor_electrical_rooms': {
                'description': 'Electrical closets on each floor',
                'cores': [],  # Will be populated with core-specific ranges
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
        
        # Populate core-specific ranges for main electrical and floor electrical rooms
        for core_pos in core_strategy['core_positions']:
            # Main electrical zones (basement)
            zones['main_electrical']['cores'].append({
                'core_id': core_pos['core_id'],
                'x_range': (core_pos['x_center'] - config['electrical_core']['width']/2,
                           core_pos['x_center'] + config['electrical_core']['width']/2),
                'y_range': (core_pos['y_center'] - config['electrical_core']['depth']/2,
                           core_pos['y_center'] + config['electrical_core']['depth']/2)
            })
            
            # Floor electrical zones
            zones['floor_electrical_rooms']['cores'].append({
                'core_id': core_pos['core_id'],
                'x_range': (core_pos['x_center'] - 6.0, core_pos['x_center'] + 6.0),
                'y_range': (core_pos['y_center'] - 4.0, core_pos['y_center'] + 4.0)
            })
        
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
        voltage = self.voltage_levels['medium'][0]  # Use standard medium voltage, will be updated in connections
        
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
        voltage = self.voltage_levels['low'][0]  # Use standard low voltage, will be updated in connections
        
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
        voltage = self.voltage_levels['low'][0]  # Use standard low voltage (208V), will be updated in connections
        
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
        """Generate realistic position based on equipment type and multi-core building zones."""
        zones = self._define_equipment_zones()
        config = self.building_config
        
        if 'transformer' in node_id and 'transformer_001' in node_id:
            # Main transformer - basement electrical room (select appropriate core)
            zone = zones['main_electrical']
            selected_core = self._select_core_for_equipment(node_id, position_id, zone['cores'])
            x = random.uniform(*selected_core['x_range'])
            y = random.uniform(*selected_core['y_range'])
            z = random.uniform(config['basement_depth'], 0.5)  # Prefer basement
            
        elif 'transformer' in node_id:
            # Secondary transformers - distributed in electrical rooms on floors
            zone = zones['floor_electrical_rooms']
            floor = self._assign_floor_for_equipment(position_id, 'secondary_transformer')
            selected_core = self._select_core_for_equipment(node_id, position_id, zone['cores'])
            x = random.uniform(*selected_core['x_range'])
            y = random.uniform(*selected_core['y_range'])
            z = floor * config['floor_height'] + random.uniform(0.0, 0.5)
            
        elif 'switchboard' in node_id:
            # Main switchboards - main electrical room
            zone = zones['main_electrical']
            selected_core = self._select_core_for_equipment(node_id, position_id, zone['cores'])
            x = random.uniform(*selected_core['x_range'])
            y = random.uniform(*selected_core['y_range'])
            z = random.uniform(0.0, config['floor_height'])
            
        elif 'panelboard' in node_id:
            # Distribution strategy based on building hierarchy
            if self._is_main_distribution_panel(node_id):
                # Main distribution panels - electrical rooms
                zone = zones['floor_electrical_rooms']
                floor = self._assign_floor_for_equipment(position_id, 'main_panelboard')
                selected_core = self._select_core_for_equipment(node_id, position_id, zone['cores'])
                x = random.uniform(*selected_core['x_range'])
                y = random.uniform(*selected_core['y_range'])
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
    
    def _select_core_for_equipment(self, node_id: str, position_id: int, available_cores: List[Dict]) -> Dict:
        """Select appropriate electrical core for equipment placement."""
        if not available_cores:
            # Fallback if no cores available
            config = self.building_config
            return {
                'x_range': (config['length'] * 0.4, config['length'] * 0.6),
                'y_range': (config['width'] * 0.4, config['width'] * 0.6)
            }
        
        # For main equipment (transformers, switchboards), distribute across cores
        if 'transformer' in node_id or 'switchboard' in node_id:
            # Use position_id to deterministically assign to cores
            core_index = position_id % len(available_cores)
            return available_cores[core_index]
        
        # For panelboards, prefer load balancing across cores
        else:
            # Rotate through cores based on position_id
            core_index = position_id % len(available_cores)
            return available_cores[core_index]
    
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
        if voltage is None or voltage <= 0:
            return 0.0
            
        # Extract kVA from performance string
        if 'kVA' in performance:
            try:
                kva = float(performance.replace(' kVA', ''))
                # I = P / (√3 × V) for three-phase
                current = (kva * 1000) / (math.sqrt(3) * voltage)
                return round(current, 1)
            except (ValueError, ZeroDivisionError):
                return round(random.uniform(100.0, 1000.0), 1)
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
        
        # Level 4 to Level 5: Panelboards to Loads (proximity-based, single connection per load)
        if level_nodes[5]:  # If there are load nodes
            for load in level_nodes[5]:
                # Check if load is already connected (avoid multiple connections)
                if G.in_degree(load) > 0:
                    continue  # Skip if already connected
                    
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
        
        # Determine voltage based on source downstream voltage, with fallback
        voltage = source_attrs.get('distribution_downstream_voltage')
        if voltage is None:
            # Fallback voltage based on equipment type
            if 'transformer' in source and 'transformer_001' in source:
                voltage = 480.0  # Main transformer output
            elif 'transformer' in source:
                voltage = 208.0  # Secondary transformer output
            elif 'switchboard' in source:
                voltage = 480.0  # Switchboard voltage
            elif 'panelboard' in source:
                voltage = 208.0  # Panelboard voltage
            else:
                voltage = 120.0  # Default load voltage
        
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
        if voltage is None or voltage <= 0:
            return 0.0
            
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
        
        # Clean up None values before saving (GraphML doesn't support None values)
        self._clean_none_values(graph)
        
        # Save as GraphML
        nx.write_graphml(graph, filepath)
        
        return filepath
    
    def _clean_none_values(self, G: nx.DiGraph):
        """Remove or replace None values in graph attributes to make it GraphML-compatible."""
        # Default values for common attributes that might be None
        default_values = {
            'distribution_upstream_voltage': 0.0,
            'distribution_downstream_voltage': 0.0,
            'distribution_upstream_current_rating': 0.0,
            'distribution_downstream_current_rating': 0.0,
            'Voltage': "TBD",
            'electrical_characteristics': {}
        }
        
        # Clean node attributes
        for node_id, attrs in G.nodes(data=True):
            for key, value in list(attrs.items()):
                if value is None:
                    if key in default_values:
                        attrs[key] = default_values[key]
                    else:
                        # Remove the attribute entirely if no default is specified
                        del attrs[key]
        
        # Clean edge attributes
        for source, target, attrs in G.edges(data=True):
            for key, value in list(attrs.items()):
                if value is None:
                    # For edges, just remove None attributes
                    del attrs[key]
    
    def _update_voltage_relationships(self, G: nx.DiGraph):
        """Update voltage relationships to ensure proper step-down from transformers."""
        # Find all source nodes (nodes with no predecessors) and start propagation from them
        source_nodes = [node for node in G.nodes() if G.in_degree(node) == 0]
        
        # If no source nodes found, start from main transformers
        if not source_nodes:
            source_nodes = [node for node in G.nodes() if 'transformer' in node and 'transformer_001' in node]
        
        # Propagate voltages from all source nodes
        for source_node in source_nodes:
            self._propagate_voltage_downstream(G, source_node)
    
    def _get_standard_voltage(self, upstream_voltage: float, equipment_type: str) -> float:
        """Get appropriate standard voltage for equipment based on upstream voltage and type."""
        all_voltages = []
        for level_voltages in self.voltage_levels.values():
            all_voltages.extend(level_voltages)
        all_voltages.sort(reverse=True)  # Sort highest to lowest
        
        if equipment_type == 'transformer':
            # Transformers step down to next lower standard voltage level
            # Ensure meaningful step-down (at least 50% reduction)
            for voltage in all_voltages:
                if voltage < upstream_voltage and voltage <= upstream_voltage * 0.8:
                    return voltage
            # If no suitable step-down found, use the lowest voltage level
            return self.voltage_levels['low'][0]  # 208V
            
        elif equipment_type == 'load':
            # Loads always get 208V (lowest available voltage)
            return self.voltage_levels['low'][0]
            
        else:
            # Switchboards and panelboards pass through voltage
            # Find closest standard voltage to upstream
            closest_voltage = min(all_voltages, key=lambda x: abs(x - upstream_voltage))
            return closest_voltage

    def _propagate_voltage_downstream(self, G: nx.DiGraph, source_node: str):
        """Recursively propagate voltages downstream from a source node."""
        source_attrs = G.nodes[source_node]
        source_downstream_voltage = source_attrs.get('distribution_downstream_voltage')
        
        if source_downstream_voltage is None:
            return  # Skip if source voltage is not set
        
        # Get all nodes this source feeds
        for target_node in G.successors(source_node):
            target_attrs = G.nodes[target_node]
            
            if 'transformer' in target_node:
                # For transformers, get appropriate step-down voltage from standard levels
                upstream_voltage = source_downstream_voltage
                downstream_voltage = self._get_standard_voltage(upstream_voltage, 'transformer')
                
                # Update transformer voltages
                G.nodes[target_node]['distribution_upstream_voltage'] = upstream_voltage
                G.nodes[target_node]['distribution_downstream_voltage'] = downstream_voltage
                
                # Update the Voltage display attribute
                voltage_display = f"{upstream_voltage/1000:.1f} kV" if upstream_voltage >= 1000 else f"{upstream_voltage:.0f} V"
                G.nodes[target_node]['Voltage'] = voltage_display
                
                # Update current ratings based on actual voltages
                performance = G.nodes[target_node].get('Nominal_performance', '150 kVA')
                G.nodes[target_node]['distribution_upstream_current_rating'] = self._calculate_current_rating(upstream_voltage, performance)
                G.nodes[target_node]['distribution_downstream_current_rating'] = self._calculate_current_rating(downstream_voltage, performance)
                
            elif 'switchboard' in target_node:
                # Switchboards pass through voltage (no transformation), but use closest standard voltage
                standard_voltage = self._get_standard_voltage(source_downstream_voltage, 'switchboard')
                G.nodes[target_node]['distribution_upstream_voltage'] = standard_voltage
                G.nodes[target_node]['distribution_downstream_voltage'] = standard_voltage
                
            elif 'panelboard' in target_node:
                # Panelboards pass through voltage, but use closest standard voltage
                upstream_voltage = source_downstream_voltage
                standard_voltage = self._get_standard_voltage(upstream_voltage, 'panelboard')
                
                G.nodes[target_node]['distribution_upstream_voltage'] = standard_voltage
                G.nodes[target_node]['distribution_downstream_voltage'] = standard_voltage
                
            elif 'load' in target_node:
                # Loads always get 208V (lowest available voltage) from standard voltage levels
                load_voltage = self._get_standard_voltage(source_downstream_voltage, 'load')
                phase_number = 1  # All loads are single-phase
                
                G.nodes[target_node]['distribution_upstream_voltage'] = load_voltage
                G.nodes[target_node]['distribution_upstream_phase_number'] = phase_number
                G.nodes[target_node]['Voltage'] = f"{load_voltage:.0f} V"
            
            # Update the edge voltage to match the actual voltage being transmitted
            edge_data = G.get_edge_data(source_node, target_node)
            if edge_data:
                transmitted_voltage = source_downstream_voltage
                edge_data['voltage'] = transmitted_voltage
                
                # Update phase number based on voltage level and target type
                if 'load' in target_node:
                    edge_data['phase_number'] = 1  # Single-phase to loads
                else:
                    edge_data['phase_number'] = 3 if transmitted_voltage > 240 else 1
            
            # Continue propagating downstream
            self._propagate_voltage_downstream(G, target_node)
    
    def _validate_electrical_constraints(self, G: nx.DiGraph):
        """Validate electrical safety constraints and fix violations."""
        violations = []
        
        for node_id, attrs in G.nodes(data=True):
            if 'transformer' in node_id:
                upstream_voltage = attrs.get('distribution_upstream_voltage')
                downstream_voltage = attrs.get('distribution_downstream_voltage')
                
                if upstream_voltage and downstream_voltage:
                    # Transformers should always step down (downstream < upstream)
                    if downstream_voltage >= upstream_voltage:
                        violations.append(f"Transformer {node_id}: downstream voltage ({downstream_voltage}V) >= upstream voltage ({upstream_voltage}V)")
                        
                        # Fix the violation by setting appropriate step-down using standard voltages
                        new_downstream = self._get_standard_voltage(upstream_voltage, 'transformer')
                        
                        # Ensure we don't go below 208V minimum
                        min_voltage = self.voltage_levels['low'][0]  # 208V
                        if new_downstream < min_voltage:
                            new_downstream = min_voltage
                            
                        G.nodes[node_id]['distribution_downstream_voltage'] = new_downstream
                        violations.append(f"  Fixed: Set downstream to {new_downstream}V")
                        
                        # Update current rating
                        performance = attrs.get('Nominal_performance', '150 kVA')
                        G.nodes[node_id]['distribution_downstream_current_rating'] = self._calculate_current_rating(new_downstream, performance)
        
        # Validate that transformers are properly connected
        for node_id in G.nodes():
            if 'transformer' in node_id:
                predecessors = list(G.predecessors(node_id))
                successors = list(G.successors(node_id))
                
                # Transformers should be fed by switchboards or panelboards
                if predecessors:
                    feeder = predecessors[0]
                    if 'transformer' in feeder:
                        violations.append(f"Transformer {node_id}: fed by another transformer {feeder} (should be fed by switchboard/panelboard)")
                
                # Transformers should feed panelboards
                if successors:
                    for successor in successors:
                        if 'transformer' in successor:
                            violations.append(f"Transformer {node_id}: feeds another transformer {successor} (should feed panelboard)")
        
        if violations:
            print("Electrical constraint violations found and fixed:")
            for violation in violations:
                print(f"  {violation}")
    
    def _validate_load_connections(self, G: nx.DiGraph):
        """Validate that each load has exactly one feeding panelboard connection."""
        violations = []
        fixes = []
        
        for node_id, attrs in G.nodes(data=True):
            if 'load' in node_id:
                predecessors = list(G.predecessors(node_id))
                
                if len(predecessors) == 0:
                    # Load with no feeding connection
                    violations.append(f"Load {node_id}: No feeding connection")
                    
                    # Fix: Connect to closest panelboard
                    panelboards = [n for n in G.nodes() if 'panelboard' in n]
                    if panelboards:
                        closest_panelboard = self._find_closest_equipment(G, node_id, panelboards)
                        if closest_panelboard:
                            # Create new edge ID
                            existing_edge_count = G.number_of_edges()
                            edge_id = f"connection_{existing_edge_count + 1:03d}"
                            self._add_connection(G, edge_id, closest_panelboard, node_id, 'General Power')
                            fixes.append(f"  Fixed: Connected {node_id} to closest panelboard {closest_panelboard}")
                
                elif len(predecessors) > 1:
                    # Load with multiple feeding connections
                    violations.append(f"Load {node_id}: Multiple feeding connections from {predecessors}")
                    
                    # Fix: Remove all but the closest panelboard connection
                    panelboard_predecessors = [p for p in predecessors if 'panelboard' in p]
                    if panelboard_predecessors:
                        # Keep the closest panelboard, remove others
                        closest_panelboard = self._find_closest_equipment(G, node_id, panelboard_predecessors)
                        
                        for pred in predecessors:
                            if pred != closest_panelboard:
                                G.remove_edge(pred, node_id)
                                fixes.append(f"  Fixed: Removed connection from {pred} to {node_id}")
                
                else:
                    # Single predecessor - check if it's a panelboard
                    feeder = predecessors[0]
                    if 'panelboard' not in feeder:
                        violations.append(f"Load {node_id}: Fed by non-panelboard {feeder}")
                        
                        # Fix: Replace with connection to closest panelboard
                        panelboards = [n for n in G.nodes() if 'panelboard' in n]
                        if panelboards:
                            closest_panelboard = self._find_closest_equipment(G, node_id, panelboards)
                            if closest_panelboard and closest_panelboard != feeder:
                                G.remove_edge(feeder, node_id)
                                existing_edge_count = G.number_of_edges()
                                edge_id = f"connection_{existing_edge_count + 1:03d}"
                                self._add_connection(G, edge_id, closest_panelboard, node_id, 'General Power')
                                fixes.append(f"  Fixed: Replaced connection from {feeder} to {closest_panelboard} for {node_id}")
        
        if violations:
            print("Load connection violations found and fixed:")
            for violation in violations:
                print(f"  {violation}")
            for fix in fixes:
                print(fix)
    

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
