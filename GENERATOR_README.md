# MEP Graph Generator

This module provides tools for generating realistic electrical system graphs in MEPG format. The generator creates logical hierarchical topologies that represent real-world electrical distribution systems.

## Features

- **Realistic Topology**: Creates hierarchical electrical systems with proper component relationships
- **Configurable Size**: Generate graphs with any number of nodes (minimum 3)
- **Logical Components**: Includes transformers, switchboards, panelboards, and loads
- **Realistic Attributes**: All components have proper electrical characteristics, physical dimensions, and metadata
- **Standard Format**: Outputs GraphML files with .mepg extension compatible with the graph viewer

## Quick Start

### Command Line Usage

Generate a graph with a specific number of nodes:

```bash
python mepg_generator.py 10
```

Generate with custom filename:

```bash
python mepg_generator.py 15 --filename my_electrical_system.mepg
```

Generate with reproducible results using a seed:

```bash
python mepg_generator.py 20 --seed 42
```

### Python API Usage

```python
from mepg_generator import MEPGraphGenerator

# Create generator instance
generator = MEPGraphGenerator(seed=42)  # Optional seed for reproducibility

# Generate a graph with 12 nodes
graph = generator.generate_graph(12)

# Save the graph
filepath = generator.save_graph(graph, "my_system.mepg")
print(f"Graph saved to: {filepath}")

# Access graph properties
print(f"Nodes: {graph.number_of_nodes()}")
print(f"Edges: {graph.number_of_edges()}")
```

### Running Examples

Execute the example script to generate sample graphs of various sizes:

```bash
python example_generator.py
```

This will create several example graphs in the `graph_outputs` directory.

## Generated System Structure

The generator creates realistic electrical system hierarchies:

1. **Primary Transformers**: High voltage to medium voltage conversion
2. **Main Switchboards**: Primary distribution points
3. **Secondary Transformers**: Medium to low voltage conversion (optional)
4. **Distribution Panelboards**: Final distribution to loads
5. **End Loads**: Connected equipment (optional)

### Component Types

- **Transformers**: High-voltage dry-type power transformers
- **Switchboards**: High-voltage distribution boards
- **Panelboards**: Lighting and general distribution boards
- **Loads**: General electrical loads

### Electrical Characteristics

All components include realistic:
- Voltage levels (13.8kV, 4.16kV, 480V, 208V, 120V, 277V)
- Current ratings calculated from power and voltage
- Phase configurations (1-phase and 3-phase)
- Short-circuit ratings
- Physical dimensions
- Manufacturer information
- Installation and warranty data

## File Outputs

Generated graphs are saved as GraphML (.mepg) files in the `graph_outputs` directory. These files can be loaded directly into the graph viewer application for visualization and analysis.

## System Requirements

- Python 3.6+
- NetworkX library
- Standard Python libraries (random, math, datetime)

## Parameters

### node_count (required)
The target number of nodes in the generated graph. Minimum value is 3.

### Optional Parameters
- `--filename, -f`: Custom output filename
- `--seed, -s`: Random seed for reproducible results

## Examples

Generate a small system (5 nodes):
```bash
python mepg_generator.py 5
```

Generate a medium system (15 nodes):
```bash
python mepg_generator.py 15 --filename medium_system.mepg
```

Generate a large system (30 nodes) with reproducible results:
```bash
python mepg_generator.py 30 --seed 123 --filename large_system.mepg
```

## Integration with Graph Viewer

The generated .mepg files are fully compatible with the existing graph viewer application. Simply:

1. Generate a graph using the generator
2. Open the graph viewer application
3. Load the generated .mepg file
4. Visualize and interact with the electrical system

## Technical Details

### Component Distribution

For a given node count, the generator distributes components as follows:
- 1 primary transformer (minimum)
- 1 main switchboard (minimum)
- ~20% secondary transformers
- ~60% distribution panelboards
- ~20% end loads

### Spatial Layout

Components are positioned in a logical 3D grid with randomization to avoid perfect alignment. The layout considers:
- Hierarchical relationships (upstream to downstream flow)
- Realistic spacing between components
- Floor height variations (z-axis)

### Connection Logic

Connections follow electrical engineering principles:
- Radial distribution topology (no loops)
- Proper voltage step-down through transformers
- Realistic current ratings and voltage drops
- Appropriate load classifications

This ensures that generated systems represent realistic electrical distribution networks that could exist in real buildings.
