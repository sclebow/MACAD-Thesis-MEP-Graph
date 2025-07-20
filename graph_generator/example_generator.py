"""
Example usage of the MEP Graph Generator

This script demonstrates how to use the MEPGraphGenerator class to create
random electrical system graphs.
"""

from mepg_generator import MEPGraphGenerator
import networkx as nx


def generate_example_graphs():
    """Generate a few example graphs of different sizes."""
    
    generator = MEPGraphGenerator(seed=42)  # Use seed for reproducible results
    
    # Generate graphs of different sizes
    sizes = [5, 10, 15, 25]
    
    for size in sizes:
        print(f"\nGenerating graph with {size} nodes...")
        
        # Generate the graph
        graph = generator.generate_graph(size)
        
        # Save the graph
        filename = f"example_{size}_nodes.mepg"
        filepath = generator.save_graph(graph, filename)
        
        print(f"  Saved to: {filepath}")
        print(f"  Actual nodes: {graph.number_of_nodes()}")
        print(f"  Edges: {graph.number_of_edges()}")
        
        # Show component breakdown
        component_types = {}
        for node, attrs in graph.nodes(data=True):
            # Extract the last part of the type for simplification
            comp_type = attrs.get('type', 'Unknown')
            if 'transformer' in comp_type.lower():
                comp_type = 'Transformer'
            elif 'switchboard' in comp_type.lower() or 'distribution board' in comp_type.lower():
                comp_type = 'Distribution Board'
            elif 'load' in comp_type.lower():
                comp_type = 'Load'
            else:
                comp_type = 'Other'
                
            component_types[comp_type] = component_types.get(comp_type, 0) + 1
        
        print(f"  Component breakdown:")
        for comp_type, count in component_types.items():
            print(f"    {comp_type}: {count}")


def generate_single_core_building():
    """Generate a tall building with single stacked electrical core."""
    
    print("\n" + "="*60)
    print("Single Core Building - Tall & Compact Configuration")
    print("="*60)
    
    # Building configuration for single core: tall and compact
    # Height > 30m OR (aspect_ratio < 2.0 AND floors > 6)
    building_config = {
        'length': 50.0,          # Compact footprint
        'width': 40.0,           # Compact footprint
        'floor_height': 3.5,
        'num_floors': 12,        # Tall building (42m height)
        'basement_depth': -3.0,
        'electrical_core': {
            'x_center': 25.0,    # Center of building
            'y_center': 20.0,    # Center of building
            'width': 12.0,
            'depth': 8.0
        }
    }
    
    generator = MEPGraphGenerator(seed=100, building_config=building_config)
    
    # Generate electrical system for this tall building
    node_count = 20
    print(f"Building specs: {building_config['length']}m × {building_config['width']}m, {building_config['num_floors']} floors")
    print(f"Building height: {building_config['num_floors'] * building_config['floor_height']:.1f}m")
    print(f"Aspect ratio: {max(building_config['length'], building_config['width']) / min(building_config['length'], building_config['width']):.2f}")
    print(f"Generating electrical system with {node_count} nodes...")
    
    graph = generator.generate_graph(node_count)
    
    # Print building strategy information
    core_strategy = generator._determine_electrical_core_strategy()
    print(f"\nElectrical Core Strategy:")
    print(f"  Strategy Type: {core_strategy['type']}")
    print(f"  Number of Cores: {core_strategy['num_cores']}")
    print(f"  Core Positions: {len(core_strategy['core_positions'])}")
    
    # Analyze floor distribution
    floor_distribution = {}
    for node, attrs in graph.nodes(data=True):
        floor = attrs.get('floor', 0)
        floor_distribution[floor] = floor_distribution.get(floor, 0) + 1
    
    print(f"\nFloor Distribution:")
    for floor in sorted(floor_distribution.keys()):
        print(f"  Floor {floor}: {floor_distribution[floor]} components")
    
    # Save the graph
    filepath = generator.save_graph(graph, "single_core_tall_building.mepg")
    print(f"\nSingle core building graph saved to: {filepath}")
    
    return graph


def generate_multi_core_building():
    """Generate a shorter, wider building with multiple stacked electrical cores."""
    
    print("\n" + "="*60)
    print("Multi Core Building - Short & Wide Configuration")
    print("="*60)
    
    # Building configuration for multi-core: short and wide
    # Height < 15m OR aspect_ratio > 3.5
    building_config = {
        'length': 120.0,         # Wide footprint
        'width': 30.0,           # Creates high aspect ratio
        'floor_height': 3.5,
        'num_floors': 3,         # Short building (10.5m height)
        'basement_depth': -3.0,
        'electrical_core': {
            'x_center': 60.0,    # Center of building length
            'y_center': 15.0,    # Center of building width
            'width': 12.0,
            'depth': 8.0
        }
    }
    
    generator = MEPGraphGenerator(seed=200, building_config=building_config)
    
    # Generate electrical system for this wide building
    node_count = 18
    print(f"Building specs: {building_config['length']}m × {building_config['width']}m, {building_config['num_floors']} floors")
    print(f"Building height: {building_config['num_floors'] * building_config['floor_height']:.1f}m")
    print(f"Aspect ratio: {max(building_config['length'], building_config['width']) / min(building_config['length'], building_config['width']):.2f}")
    print(f"Generating electrical system with {node_count} nodes...")
    
    graph = generator.generate_graph(node_count)
    
    # Print building strategy information
    core_strategy = generator._determine_electrical_core_strategy()
    print(f"\nElectrical Core Strategy:")
    print(f"  Strategy Type: {core_strategy['type']}")
    print(f"  Number of Cores: {core_strategy['num_cores']}")
    print(f"  Core Positions: {len(core_strategy['core_positions'])}")
    
    # Show core positions
    for i, core_pos in enumerate(core_strategy['core_positions']):
        print(f"    Core {i+1}: x={core_pos['x_center']:.1f}m, y={core_pos['y_center']:.1f}m")
    
    # Analyze spatial distribution
    x_coords = [attrs['x'] for _, attrs in graph.nodes(data=True)]
    y_coords = [attrs['y'] for _, attrs in graph.nodes(data=True)]
    
    print(f"\nSpatial Distribution:")
    print(f"  X range: {min(x_coords):.1f}m to {max(x_coords):.1f}m (span: {max(x_coords) - min(x_coords):.1f}m)")
    print(f"  Y range: {min(y_coords):.1f}m to {max(y_coords):.1f}m (span: {max(y_coords) - min(y_coords):.1f}m)")
    
    # Analyze floor distribution
    floor_distribution = {}
    for node, attrs in graph.nodes(data=True):
        floor = attrs.get('floor', 0)
        floor_distribution[floor] = floor_distribution.get(floor, 0) + 1
    
    print(f"\nFloor Distribution:")
    for floor in sorted(floor_distribution.keys()):
        print(f"  Floor {floor}: {floor_distribution[floor]} components")
    
    # Save the graph
    filepath = generator.save_graph(graph, "multi_core_wide_building.mepg")
    print(f"\nMulti-core building graph saved to: {filepath}")
    
    return graph


def demonstrate_custom_generation():
    """Demonstrate custom graph generation with specific parameters."""
    
    print("\n" + "="*50)
    print("Custom Graph Generation Example")
    print("="*50)
    
    generator = MEPGraphGenerator()
    
    # Generate a medium-sized system
    node_count = 12
    print(f"Generating custom electrical system with {node_count} nodes...")
    
    graph = generator.generate_graph(node_count)
    
    # Print detailed information about the generated graph
    print(f"\nGraph Details:")
    print(f"  Graph ID: {graph.graph.get('id', 'Unknown')}")
    print(f"  Total Nodes: {graph.number_of_nodes()}")
    print(f"  Total Edges: {graph.number_of_edges()}")
    
    # Show all nodes with their types and key attributes
    print(f"\nNodes:")
    for node, attrs in graph.nodes(data=True):
        node_type = "Unknown"
        if 'transformer' in attrs.get('type', '').lower():
            node_type = "Transformer"
        elif 'switchboard' in attrs.get('type', '').lower():
            node_type = "Switchboard"
        elif 'panelboard' in attrs.get('type', '').lower() or 'distribution board' in attrs.get('type', '').lower():
            node_type = "Panelboard"
        elif 'load' in attrs.get('type', '').lower():
            node_type = "Load"
        
        voltage = attrs.get('distribution_downstream_voltage', attrs.get('Voltage', 'N/A'))
        manufacturer = attrs.get('Manufacturer', 'N/A')
        print(f"  {node}: {node_type} | Voltage: {voltage} | Manufacturer: {manufacturer}")
    
    # Show connections
    print(f"\nConnections:")
    for source, target, attrs in graph.edges(data=True):
        voltage = attrs.get('voltage', 'N/A')
        current = attrs.get('current_rating', 'N/A')
        load_class = attrs.get('load_classification', 'N/A')
        print(f"  {source} → {target} | {voltage}V | {current}A | {load_class}")
    
    # Save the custom graph
    filepath = generator.save_graph(graph, "custom_example.mepg")
    print(f"\nCustom graph saved to: {filepath}")


def compare_building_strategies():
    """Compare electrical strategies between different building configurations."""
    
    print("\n" + "="*60)
    print("Building Strategy Comparison")
    print("="*60)
    
    # Single core building config
    single_core_config = {
        'length': 50.0, 'width': 40.0, 'floor_height': 3.5, 'num_floors': 12,
        'basement_depth': -3.0,
        'electrical_core': {'x_center': 25.0, 'y_center': 20.0, 'width': 12.0, 'depth': 8.0}
    }
    
    # Multi-core building config
    multi_core_config = {
        'length': 120.0, 'width': 30.0, 'floor_height': 3.5, 'num_floors': 3,
        'basement_depth': -3.0,
        'electrical_core': {'x_center': 60.0, 'y_center': 15.0, 'width': 12.0, 'depth': 8.0}
    }
    
    configs = [
        ("Single Core (Tall & Compact)", single_core_config),
        ("Multi-Core (Short & Wide)", multi_core_config)
    ]
    
    for name, config in configs:
        print(f"\n{name}:")
        print(f"  Dimensions: {config['length']}m × {config['width']}m × {config['num_floors']} floors")
        
        height = config['num_floors'] * config['floor_height']
        aspect_ratio = max(config['length'], config['width']) / min(config['length'], config['width'])
        floor_area = config['length'] * config['width']
        total_area = floor_area * config['num_floors']
        
        print(f"  Height: {height:.1f}m")
        print(f"  Aspect Ratio: {aspect_ratio:.2f}")
        print(f"  Floor Area: {floor_area:.0f} m²")
        print(f"  Total Area: {total_area:.0f} m²")
        
        # Create temporary generator to analyze strategy
        temp_generator = MEPGraphGenerator(building_config=config)
        strategy = temp_generator._determine_electrical_core_strategy()
        
        print(f"  Core Strategy: {strategy['type']}")
        print(f"  Number of Cores: {strategy['num_cores']}")
        
        # Strategy criteria explanation
        if height > 30.0 or (aspect_ratio < 2.0 and config['num_floors'] > 6):
            print(f"  Reason: {'Height > 30m' if height > 30.0 else 'Compact & tall (AR < 2.0, floors > 6)'}")
        elif height >= 15.0 and aspect_ratio <= 3.5:
            print(f"  Reason: Medium building (15-30m height, AR ≤ 3.5)")
        else:
            print(f"  Reason: {'Low height' if height < 15.0 else 'High aspect ratio'} → distributed cores")


if __name__ == "__main__":
    print("MEP Graph Generator Examples")
    print("="*40)
    
    # Compare building strategies first
    compare_building_strategies()
    
    # Generate example graphs
    generate_example_graphs()
    
    # Generate building with single stacked electrical core
    generate_single_core_building()
    
    # Generate building with multiple stacked electrical cores
    generate_multi_core_building()
    
    # Demonstrate custom generation
    demonstrate_custom_generation()
    
    print("\n" + "="*60)
    print("All examples completed successfully!")
    print("Generated files:")
    print("  - Standard examples: example_*.mepg")
    print("  - Single core building: single_core_tall_building.mepg")
    print("  - Multi-core building: multi_core_wide_building.mepg")
    print("  - Custom example: custom_example.mepg")
    print("Check the 'graph_outputs' directory for generated .mepg files")
    print("You can load these files in the graph viewer application.")
