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


if __name__ == "__main__":
    print("MEP Graph Generator Examples")
    print("="*40)
    
    # Generate example graphs
    generate_example_graphs()
    
    # Demonstrate custom generation
    demonstrate_custom_generation()
    
    print("\n" + "="*50)
    print("All examples completed successfully!")
    print("Check the 'graph_outputs' directory for generated .mepg files")
    print("You can load these files in the graph viewer application.")
