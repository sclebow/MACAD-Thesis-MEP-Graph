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
    
    def __init__(self, seed: int = None):
        """
        Initialize the generator.
        
        Args:
            seed: Random seed for reproducible results
        """
        if seed is not None:
            random.seed(seed)
        
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
    
    def generate_graph(self, node_count: int) -> nx.DiGraph:
        """
        Generate a logical electrical system graph.
        
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
        
        # Calculate logical distribution of components
        distribution = self._calculate_component_distribution(node_count)
        
        # Generate nodes in hierarchical order
        node_id = 1
        level_nodes = {}
        
        # Level 1: Main transformers
        level_nodes[1] = []
        for i in range(distribution['transformers_main']):
            node_id_str = f"transformer_{node_id:03d}"
            self._add_transformer_node(G, node_id_str, 'main', node_id)
            level_nodes[1].append(node_id_str)
            node_id += 1
        
        # Level 2: Main switchboards
        level_nodes[2] = []
        for i in range(distribution['switchboards']):
            node_id_str = f"switchboard_{node_id:03d}"
            self._add_switchboard_node(G, node_id_str, node_id)
            level_nodes[2].append(node_id_str)
            node_id += 1
        
        # Level 3: Secondary transformers (if needed)
        level_nodes[3] = []
        for i in range(distribution['transformers_secondary']):
            node_id_str = f"transformer_{node_id:03d}"
            self._add_transformer_node(G, node_id_str, 'secondary', node_id)
            level_nodes[3].append(node_id_str)
            node_id += 1
        
        # Level 4: Distribution panelboards
        level_nodes[4] = []
        for i in range(distribution['panelboards']):
            node_id_str = f"panelboard_{node_id:03d}"
            self._add_panelboard_node(G, node_id_str, node_id)
            level_nodes[4].append(node_id_str)
            node_id += 1
        
        # Level 5: End loads (if specified)
        level_nodes[5] = []
        for i in range(distribution['loads']):
            node_id_str = f"load_{node_id:03d}"
            self._add_load_node(G, node_id_str, node_id)
            level_nodes[5].append(node_id_str)
            node_id += 1
        
        # Create logical connections
        self._create_connections(G, level_nodes)
        
        # Update voltages to ensure proper step-down relationships
        self._update_voltage_relationships(G)
        
        return G
    
    def _calculate_component_distribution(self, node_count: int) -> Dict[str, int]:
        """Calculate logical distribution of component types."""
        # Start with minimum viable system
        distribution = {
            'transformers_main': 1,
            'switchboards': 1,
            'transformers_secondary': 0,
            'panelboards': 0,
            'loads': 0
        }
        
        remaining = node_count - 2  # Account for main transformer and switchboard
        
        # Add components based on typical electrical system ratios
        if remaining > 0:
            # 20% secondary transformers, 60% panelboards, 20% loads
            distribution['transformers_secondary'] = max(0, int(remaining * 0.2))
            distribution['panelboards'] = max(1, int(remaining * 0.6))
            distribution['loads'] = max(0, remaining - distribution['transformers_secondary'] - distribution['panelboards'])
        
        # Ensure we don't exceed node_count
        total = sum(distribution.values())
        if total > node_count:
            distribution['loads'] = max(0, distribution['loads'] - (total - node_count))
        
        return distribution
    
    def _add_transformer_node(self, G: nx.DiGraph, node_id: str, transformer_type: str, position_id: int):
        """Add a transformer node with realistic attributes."""
        x, y, z = self._generate_position(position_id)
        
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
        x, y, z = self._generate_position(position_id)
        # Switchboards will have voltage set later based on upstream transformer
        voltage = 480.0  # Default medium voltage, will be updated in connections
        
        attrs = {
            'type': self.component_types['switchboard'],
            'x': x, 'y': y, 'z': z,
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
        x, y, z = self._generate_position(position_id)
        # Panelboards will have voltage set later based on upstream equipment
        voltage = 208.0  # Default voltage, will be updated in connections
        
        attrs = {
            'type': self.component_types['panelboard'],
            'x': x, 'y': y, 'z': z,
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
        x, y, z = self._generate_position(position_id)
        # Loads will have voltage set later based on upstream panelboard
        voltage = 120.0  # Default low voltage, will be updated in connections
        
        attrs = {
            'type': self.component_types['load'],
            'x': x, 'y': y, 'z': z,
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
    
    def _generate_position(self, position_id: int) -> Tuple[float, float, float]:
        """Generate realistic 3D position for a component."""
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
        """Create logical connections between nodes."""
        edge_id = 1
        
        # Level 1 to Level 2: Transformers to Switchboards
        for transformer in level_nodes[1]:
            for switchboard in level_nodes[2]:
                self._add_connection(G, f"connection_{edge_id:03d}", transformer, switchboard, 'Main Distribution')
                edge_id += 1
                break  # Each transformer connects to one main switchboard
        
        # Level 2 to Level 3: Switchboards to Secondary Transformers
        if level_nodes[3]:  # If there are secondary transformers
            for i, transformer in enumerate(level_nodes[3]):
                switchboard = level_nodes[2][i % len(level_nodes[2])]
                self._add_connection(G, f"connection_{edge_id:03d}", switchboard, transformer, 'Secondary Distribution')
                edge_id += 1
        
        # Connect transformers to panelboards (1:1 relationship - each transformer powers exactly one panelboard)
        connected_panelboards = set()
        
        # First, connect secondary transformers to panelboards (1:1 relationship)
        if level_nodes[3]:  # If there are secondary transformers
            for i, transformer in enumerate(level_nodes[3]):
                if i < len(level_nodes[4]):  # Ensure we have panelboards available
                    panelboard = level_nodes[4][i]
                    load_type = random.choice(self.load_types)
                    self._add_connection(G, f"connection_{edge_id:03d}", transformer, panelboard, load_type)
                    connected_panelboards.add(panelboard)
                    edge_id += 1
        
        # Connect remaining panelboards in a tree structure
        remaining_panelboards = [pb for pb in level_nodes[4] if pb not in connected_panelboards]
        
        if remaining_panelboards:
            # Connect one panelboard directly to each switchboard
            num_switchboard_connections = min(len(remaining_panelboards), len(level_nodes[2]))
            
            for i in range(num_switchboard_connections):
                panelboard = remaining_panelboards[i]
                switchboard = level_nodes[2][i % len(level_nodes[2])]
                load_type = random.choice(self.load_types)
                self._add_connection(G, f"connection_{edge_id:03d}", switchboard, panelboard, load_type)
                connected_panelboards.add(panelboard)
                edge_id += 1
            
            # Connect remaining panelboards to already connected panelboards (creating sub-distribution)
            # This allows multiple panelboards to be powered from a single panelboard
            available_sources = list(connected_panelboards)
            for panelboard in remaining_panelboards[num_switchboard_connections:]:
                if available_sources:
                    source_panelboard = random.choice(available_sources)
                    load_type = random.choice(['Lighting', 'General Power', 'Sub-Distribution'])
                    self._add_connection(G, f"connection_{edge_id:03d}", source_panelboard, panelboard, load_type)
                    connected_panelboards.add(panelboard)
                    # Add this panelboard as a potential source for future connections
                    available_sources.append(panelboard)
                    edge_id += 1
        
        # Level 4 to Level 5: Panelboards to Loads
        if level_nodes[5]:  # If there are load nodes
            for i, load in enumerate(level_nodes[5]):
                panelboard = level_nodes[4][i % len(level_nodes[4])]
                load_type = random.choice(['Lighting', 'General Power', 'Motor Loads'])
                self._add_connection(G, f"connection_{edge_id:03d}", panelboard, load, load_type)
                edge_id += 1
    
    def _add_connection(self, G: nx.DiGraph, edge_id: str, source: str, target: str, load_classification: str):
        """Add a connection (edge) between two nodes."""
        source_attrs = G.nodes[source]
        target_attrs = G.nodes[target]
        
        # Determine voltage based on source downstream voltage
        voltage = source_attrs.get('distribution_downstream_voltage', 480.0)
        
        # Calculate current rating (typically less than source capacity)
        source_current = source_attrs.get('distribution_downstream_current_rating', 1000.0)
        current_rating = round(source_current * random.uniform(0.6, 0.9), 1)
        
        # Calculate apparent current (typically less than rating)
        apparent_current = round(current_rating * random.uniform(0.7, 0.95), 1)
        
        # Calculate voltage drop (realistic values)
        voltage_drop = round(random.uniform(1.0, 8.0), 1)
        
        edge_attrs = {
            'connection_type': 'Power',
            'voltage': voltage,
            'current_rating': current_rating,
            'phase_number': 3 if voltage > 240 else 1,
            'frequency': 60.0,
            'apparent_current': apparent_current,
            'voltage_drop': voltage_drop,
            'load_classification': load_classification
        }
        
        G.add_edge(source, target, id=edge_id, **edge_attrs)
    
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
    
    args = parser.parse_args()
    
    if args.node_count < 3:
        print("Error: Node count must be at least 3 for a meaningful electrical system")
        return
    
    # Create generator
    generator = MEPGraphGenerator(seed=args.seed)
    
    # Generate graph
    print(f"Generating electrical system graph with {args.node_count} nodes...")
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


if __name__ == "__main__":
    main()
