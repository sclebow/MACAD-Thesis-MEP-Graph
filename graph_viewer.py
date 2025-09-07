# This is a Panel application that allows users to visualize and interact with a graph based on a GraphML xlmns file.
# It provides functionalities to load a graph, display it, and interact with its nodes and edges.

import panel as pn
from panel import widgets
import io
import networkx as nx
import plotly.graph_objects as go
import os
import pandas as pd
import random
import math
import datetime

# Import helper files
# from helpers.maintenance_tasks import process_maintenance_tasks
# from helpers.node_risk import *
# from helpers.rul_helper import apply_rul_to_graph
# Import MEP graph generator
from helpers.rul_helper import apply_maintenance_log_to_graph
from helpers.controllers.graph_controller import GraphController

print("\n" * 5)

pn.extension('plotly')
pn.extension('jsoneditor')

class SystemViewController:
    def __init__(self, graph_controller):
        self.graph_controller = graph_controller
        self.widgets = {}
        # Timeline data
        self.prioritized_schedule = None
        self.months = []
        self.number_of_graphs = 0
        self.max_tasks = 0
        
    def register_widgets(self, widgets_dict):
        """Register UI widgets for event handling"""
        self.widgets.update(widgets_dict)
    
    def set_timeline_data(self, prioritized_schedule, months, number_of_graphs, max_tasks):
        """Set timeline data for controller access"""
        self.prioritized_schedule = prioritized_schedule
        self.months = months
        self.number_of_graphs = number_of_graphs
        self.max_tasks = max_tasks
    
    def setup_callbacks(self):
        """Set up all event callbacks"""
        # File operations
        if 'file_input' in self.widgets:
            self.widgets['file_input'].param.watch(self.handle_file_load, 'value')
        if 'save_button' in self.widgets:
            self.widgets['save_button'].on_click(self.handle_save_graph)
        
        # Visualization controls
        if 'name_toggle' in self.widgets:
            self.widgets['name_toggle'].param.watch(self.handle_name_toggle, 'value')
        
        # Node/edge selection
        if 'node_dropdown' in self.widgets:
            self.widgets['node_dropdown'].param.watch(self.handle_node_selection, 'value')
        if 'edge_dropdown' in self.widgets:
            self.widgets['edge_dropdown'].param.watch(self.handle_edge_selection, 'value')
        if 'node_attr_df' in self.widgets:
            self.widgets['node_attr_df'].param.watch(self.handle_node_attr_change, 'value')
        if 'edge_attr_df' in self.widgets:
            self.widgets['edge_attr_df'].param.watch(self.handle_edge_attr_change, 'value')
        
        # Timeline controls
        if 'graph_slider' in self.widgets:
            self.widgets['graph_slider'].param.watch(self.handle_slider_change, 'value')
        if 'play_button' in self.widgets:
            self.widgets['play_button'].on_click(self.handle_play_animation)
        if 'pause_button' in self.widgets:
            self.widgets['pause_button'].on_click(self.handle_pause_animation)
    
    def handle_file_load(self, event):
        """Handle file upload"""
        if event.new is not None:
            result = self.graph_controller.load_graph_from_file(event.new)
            if result['success']:
                self.refresh_all_displays()
                print("Graph loaded successfully")
            else:
                print(f"Error loading graph: {result['error']}")
    
    def handle_save_graph(self, event):
        """Handle save graph button"""
        if 'save_input' in self.widgets:
            filename = self.widgets['save_input'].value or "graph.mepg"
            result = self.graph_controller.save_graph_to_file(filename)
            if result['success']:
                if 'save_status' in self.widgets:
                    self.widgets['save_status'].object = f"**Graph saved to `{result['path']}`**"
                    self.widgets['save_status'].visible = True
                print(f"Graph saved to {result['path']}")
            else:
                if 'save_status' in self.widgets:
                    self.widgets['save_status'].object = f"**Error saving graph:** {result['error']}"
                    self.widgets['save_status'].visible = True
                print(f"Error saving graph: {result['error']}")
    
    def handle_name_toggle(self, event):
        """Handle name display toggle"""
        self.graph_controller.view_settings['use_full_names'] = event.new
        self.update_all_visualizations()
    
    def handle_node_selection(self, event):
        """Handle node dropdown selection"""
        if event.new and self.graph_controller.current_graph[0]:
            self.update_node_info(event.new)
    
    def handle_edge_selection(self, event):
        """Handle edge dropdown selection"""
        if event.new and self.graph_controller.current_graph[0]:
            self.update_edge_info(event.new)
    
    def handle_node_attr_change(self, event):
        """Handle node attribute dataframe changes"""
        if 'node_dropdown' in self.widgets:
            node = self.widgets['node_dropdown'].value
            if node and event.new is not None:
                df = event.new
                if len(df) > 0:
                    attrs = dict(zip(df["Attribute"], df["Value"]))
                    result = self.graph_controller.update_node_attributes(node, attrs)
                    if result['success']:
                        self.update_all_visualizations()
    
    def handle_edge_attr_change(self, event):
        """Handle edge attribute dataframe changes"""
        if 'edge_dropdown' in self.widgets:
            edge_str = self.widgets['edge_dropdown'].value
            if edge_str and " - " in edge_str and event.new is not None:
                u, v = edge_str.split(" - ", 1)
                edge_tuple = (u, v)
                if edge_tuple in self.graph_controller.current_graph[0].edges:
                    df = event.new
                    if len(df) > 0:
                        attrs = dict(zip(df["Attribute"], df["Value"]))
                        for k, v in attrs.items():
                            self.graph_controller.current_graph[0].edges[edge_tuple][k] = v
                        self.update_all_visualizations()
    
    def handle_slider_change(self, event):
        """Handle graph slider value change"""
        # The basic visualization update - let the original functions handle timeline-specific updates
        self.update_all_visualizations()
    
    def handle_play_animation(self, event):
        """Handle play button click to start timeline animation"""
        if not hasattr(self, 'animation_running'):
            self.animation_running = {"value": False, "callback": None}
            
        if not self.animation_running["value"]:
            self.animation_running["value"] = True
            if 'play_button' in self.widgets:
                self.widgets['play_button'].disabled = True
            if 'pause_button' in self.widgets:
                self.widgets['pause_button'].disabled = False
            self._animate_slider()
    
    def handle_pause_animation(self, event):
        """Handle pause button click to stop timeline animation"""
        if hasattr(self, 'animation_running'):
            self.animation_running["value"] = False
            if 'play_button' in self.widgets:
                self.widgets['play_button'].disabled = False
            if 'pause_button' in self.widgets:
                self.widgets['pause_button'].disabled = True
            # Remove any pending callback immediately
            if self.animation_running["callback"] is not None:
                try:
                    pn.state.curdoc.remove_timeout_callback(self.animation_running["callback"])
                except Exception:
                    pass
                self.animation_running["callback"] = None
    
    def _animate_slider(self):
        """Internal method to handle slider animation"""
        if not hasattr(self, 'animation_running') or not self.animation_running["value"]:
            return
            
        if 'graph_slider' not in self.widgets:
            return
            
        slider = self.widgets['graph_slider']
        total_animation_time = 2000  # 2 seconds (in milliseconds)
        timeout = total_animation_time / (slider.end - slider.start) if slider.end > slider.start else 100
        
        # Increment slider value if not at end
        if slider.value < slider.end:
            slider.value += 1
            # Only schedule next callback if animation is still running
            if self.animation_running["value"]:
                self.animation_running["callback"] = pn.state.curdoc.add_timeout_callback(self._animate_slider, timeout)
        else:
            # Stop animation when reaching the end
            self.animation_running["value"] = False
            if 'play_button' in self.widgets:
                self.widgets['play_button'].disabled = False
            if 'pause_button' in self.widgets:
                self.widgets['pause_button'].disabled = True
            self.animation_running["callback"] = None
    
    def refresh_all_displays(self):
        """Refresh all UI displays after data change"""
        self.update_all_visualizations()
        self.update_dropdowns()
        # Automatically process maintenance tasks when graph is loaded
        self.auto_process_maintenance_tasks()
    
    def auto_process_maintenance_tasks(self):
        """Automatically trigger maintenance task processing if a graph is loaded"""
        try:
            if self.graph_controller.current_graph[0] is not None:
                # Call the global process_tasks_callback function if it exists
                if 'process_tasks_callback' in globals():
                    process_tasks_callback()
        except Exception as e:
            print(f"Warning: Auto maintenance processing failed: {e}")
    
    def update_all_visualizations(self):
        """Update all visualization panes"""
        if 'plot_pane' in self.widgets:
            fig = self.graph_controller.get_visualization_data('2d_type')
            if fig:
                self.widgets['plot_pane'].object = fig
        
        if 'plot_risk_pane' in self.widgets:
            fig = self.graph_controller.get_visualization_data('2d_risk')
            if fig:
                self.widgets['plot_risk_pane'].object = fig
        
        if 'three_d_pane' in self.widgets:
            fig = self.graph_controller.get_visualization_data('3d')
            if fig:
                self.widgets['three_d_pane'].object = fig
    
    def update_dropdowns(self):
        """Update node and edge dropdown options"""
        data = self.graph_controller.get_component_data()
        
        if 'node_dropdown' in self.widgets:
            self.widgets['node_dropdown'].options = data['nodes']
            if data['nodes']:
                self.widgets['node_dropdown'].value = data['nodes'][0]
        
        if 'edge_dropdown' in self.widgets:
            self.widgets['edge_dropdown'].options = data['edges']
            if data['edges']:
                self.widgets['edge_dropdown'].value = data['edges'][0]
    
    def update_node_info(self, node_id):
        """Update node info display and attribute table"""
        if not self.graph_controller.current_graph[0]:
            return
            
        if node_id and node_id in self.graph_controller.current_graph[0].nodes:
            attrs = self.graph_controller.current_graph[0].nodes[node_id]
            
            if 'node_info_pane' in self.widgets:
                self.widgets['node_info_pane'].object = f"**Node:** {node_id}"
            
            if 'node_attr_df' in self.widgets:
                if attrs:
                    df = pd.DataFrame(list(attrs.items()), columns=["Attribute", "Value"])
                    self.widgets['node_attr_df'].value = df.copy()
                else:
                    self.widgets['node_attr_df'].value = pd.DataFrame(columns=["Attribute", "Value"])
        else:
            # Handle case where node doesn't exist
            if 'node_info_pane' in self.widgets:
                self.widgets['node_info_pane'].object = f"**Node not found:** {node_id}"
            if 'node_attr_df' in self.widgets:
                self.widgets['node_attr_df'].value = pd.DataFrame(columns=["Attribute", "Value"])
            
            # Refresh dropdown to remove invalid options
            self.update_dropdowns()
    
    def update_edge_info(self, edge_str):
        """Update edge info display and attribute table"""
        if not self.graph_controller.current_graph[0]:
            return
            
        if edge_str and " - " in edge_str:
            u, v = edge_str.split(" - ", 1)
            edge_tuple = (u, v)
            if edge_tuple in self.graph_controller.current_graph[0].edges:
                attrs = self.graph_controller.current_graph[0].edges[edge_tuple]
                
                if 'edge_info_pane' in self.widgets:
                    self.widgets['edge_info_pane'].object = f"**Edge:** {edge_tuple}"
                
                if 'edge_attr_df' in self.widgets:
                    if attrs:
                        df = pd.DataFrame(list(attrs.items()), columns=["Attribute", "Value"])
                        self.widgets['edge_attr_df'].value = df.copy()
                    else:
                        self.widgets['edge_attr_df'].value = pd.DataFrame(columns=["Attribute", "Value"])
            else:
                if 'edge_info_pane' in self.widgets:
                    self.widgets['edge_info_pane'].object = f"**Edge not found:** {edge_str}"
                if 'edge_attr_df' in self.widgets:
                    self.widgets['edge_attr_df'].value = pd.DataFrame(columns=["Attribute", "Value"])

class SystemView:
    """Handles the main system overview interface"""
    
    def __init__(self, graph_controller, system_controller):
        self.graph_controller = graph_controller
        self.system_controller = system_controller
    
    def create_layout(self):
        """Create the system overview layout"""
        return pn.Column(
            self.create_file_management(),
            self.create_visualization_panel(),
            self.create_inspection_panel(),
            sizing_mode='stretch_width'
        )

    def create_file_management(self):
        """File upload and graph generation controls"""
        # File upload widget
        file_input = pn.widgets.FileInput(accept='.mepg')
        
        # Name display toggle
        name_toggle = pn.widgets.Toggle(name="Use Full Names", value=False)
        
        return pn.Column(
            "### Load MEP Graph File",
            file_input,
            pn.Row("### Display Options", name_toggle),
            sizing_mode='stretch_width'
        )

    def create_visualization_panel(self):
        """Graph visualization controls and display"""
        # Create plot panes
        plot_pane = pn.pane.Plotly(height=600, sizing_mode='stretch_width')
        plot_risk_pane = pn.pane.Plotly(height=600, sizing_mode='stretch_width')
        three_d_pane = pn.pane.Plotly(height=600, sizing_mode='stretch_width')
        
        # 2D visualization by type
        two_d_column = pn.Column(
            "### 2D Graph Visualization (Type)",
            plot_pane
        )
        
        # 2D visualization by risk
        two_d_risk_column = pn.Column(
            "### 2D Graph Visualization (Risk Score)",
            plot_risk_pane
        )
        
        # 3D visualization
        three_d_column = pn.Column(
            "### 3D Graph Visualization",
            three_d_pane
        )
        
        plots_row = pn.Row(two_d_column, two_d_risk_column, three_d_column, sizing_mode='stretch_width')
        
        return plots_row

    def create_inspection_panel(self):
        """Node/edge inspection panel"""
        selection_table_height = 400
        
        # Node selection
        node_dropdown = pn.widgets.Select(name="Select Node", options=[])
        node_info_pane = pn.pane.Markdown("No node selected.")
        node_attr_df = pn.widgets.DataFrame(
            pd.DataFrame(columns=["Attribute", "Value"]),
            editors={
                "Attribute": None,
                "Value": {"type": "string", "x": "float", "y": "float", "z": "float"}
            },
            height=selection_table_height,
            show_index=False,
        )
        
        # Edge selection
        edge_dropdown = pn.widgets.Select(name="Select Edge", options=[])
        edge_info_pane = pn.pane.Markdown("No edge selected.")
        edge_attr_df = pn.widgets.DataFrame(
            pd.DataFrame(columns=["Attribute", "Value"]),
            editors={"Attribute": None, "Value": "string"},
            height=selection_table_height,
            show_index=False,
        )
        
        node_column = pn.Column(
            "### Node Selection", 
            node_dropdown, 
            node_info_pane, 
            node_attr_df, 
            sizing_mode='stretch_width'
        )
        
        edge_column = pn.Column(
            "### Edge Selection", 
            edge_dropdown, 
            edge_info_pane, 
            edge_attr_df, 
            sizing_mode='stretch_width'
        )
        
        return pn.Row(node_column, edge_column, sizing_mode='stretch_width')

    def _generate_graph_callback(self, event):
        """Generate graph callback for SystemView"""
        # This will reference the sliders from _create_generator_accordion
        # For now, use global function - will be refactored later
        generate_graph_callback(event)

    def _create_save_section(self):
        """Create save graph section"""
        filename_input = pn.widgets.TextInput(name="Save As Filename", value=self._get_default_filename())
        save_button = pn.widgets.Button(name="Save Graph", button_type="primary")
        save_status = pn.pane.Markdown(visible=False)
        
        save_row = pn.Row(filename_input, save_button)
        return pn.Column("### Save Graph", save_row, save_status, sizing_mode='stretch_width')

    def _create_maintenance_section(self):
        """Create maintenance log upload section"""
        maintenance_log_input = pn.widgets.FileInput(accept='.csv')
        # Callback will be handled by controller
        return pn.Column(
            "### Upload Maintenance Log (.csv)",
            maintenance_log_input,
            sizing_mode='stretch_width'
        )

    def _get_default_filename(self):
        """Get default filename for saving"""
        today = datetime.datetime.now().strftime('%y%m%d')
        return f"{today}_graph.mepg"

class FailurePredictionView:
    """Handles failure prediction dashboard"""
    
    def __init__(self, graph_controller):
        self.graph_controller = graph_controller
    
    def create_layout(self):
        """Create three-panel failure prediction layout"""
        left_panel = pn.Column(
            "### System Health Overview",
            pn.pane.Markdown("Health metrics coming soon..."),
            width=300
        )
        
        center_panel = pn.Column(
            "### Failure Timeline",
            pn.pane.Markdown("Timeline visualization coming soon..."),
            sizing_mode='stretch_width'
        )
        
        right_panel = pn.Column(
            "### Component Details", 
            pn.pane.Markdown("Component analysis coming soon..."),
            width=350
        )
        
        return pn.Row(left_panel, center_panel, right_panel)

class MaintenanceView:
    """Handles maintenance management interface"""
    
    def __init__(self, graph_controller):
        self.graph_controller = graph_controller
    
    def create_layout(self):
        """Create maintenance management layout"""
        return pn.Column(
            "## Maintenance Management",
            pn.pane.Markdown("Maintenance dashboard coming soon..."),
            pn.pane.Markdown("This will integrate with Scott's scheduling system."),
            sizing_mode='stretch_width'
        )

# Initialize controllers early so callback functions can reference them
graph_controller = GraphController()
system_controller = SystemViewController(graph_controller)

# For backward compatibility with existing code
current_graph = graph_controller.current_graph

def update_dropdowns(graph):
    node_names = list(graph.nodes())
    edge_names = [f"{u} - {v}" for u, v in graph.edges()]
    node_dropdown.options = node_names
    edge_dropdown.options = edge_names
    # Set values only after both options are set
    if node_names:
        node_dropdown.value = node_names[0]
        update_node_info(node_names[0], graph)
    else:
        node_dropdown.value = None
        node_info_pane.object = "No nodes available."
    if edge_names:
        edge_dropdown.value = edge_names[0]
        # Directly update info pane instead of calling callback
        edge_str = edge_names[0]
        if edge_str and " - " in edge_str:
            u, v = edge_str.split(" - ", 1)
            edge_tuple = (u, v)
            if edge_tuple in graph.edges:
                attrs = graph.edges[edge_tuple]
                info = f"**Edge:** {edge_tuple}"
                edge_info_pane.object = info
                # Display attributes as editable table
                if attrs:
                    df = pd.DataFrame(list(attrs.items()), columns=["Attribute", "Value"])
                    df = df[["Attribute", "Value"]]
                    edge_attr_df.value = df.copy()
                else:
                    edge_attr_df.value = pd.DataFrame(columns=["Attribute", "Value"])
            else:
                edge_info_pane.object = "No edge selected."
                edge_attr_df.value = pd.DataFrame(columns=["Attribute", "Value"])
        else:
            edge_info_pane.object = "No edge selected."
            edge_attr_df.value = pd.DataFrame(columns=["Attribute", "Value"])
    else:
        edge_dropdown.value = None
        edge_info_pane.object = "No edges available."
        edge_attr_df.value = pd.DataFrame(columns=["Attribute", "Value"])

def update_node_info(node, graph):
    if node is not None and node in graph.nodes:
        attrs = graph.nodes[node]
        info = f"**Node:** {node}"
        node_info_pane.object = info
        # Display attributes as editable table
        if attrs:
            df = pd.DataFrame(list(attrs.items()), columns=["Attribute", "Value"])
            # Ensure only 'Attribute' and 'Value' columns are present
            df = df[["Attribute", "Value"]]
            node_attr_df.value = df.copy()
        else:
            node_attr_df.value = pd.DataFrame(columns=["Attribute", "Value"])
    else:
        node_info_pane.object = "No node selected."
        node_attr_df.value = pd.DataFrame(columns=["Attribute", "Value"])

def node_dropdown_callback(event):
    """Delegate to controller"""
    system_controller.handle_node_selection(event)

def edge_dropdown_callback(event):
    """Delegate to controller"""
    system_controller.handle_edge_selection(event)

def file_input_callback(event):
    """Delegate to controller"""
    system_controller.handle_file_load(event)

def autoload_example_graph():
    """Load example graph using controller"""
    global system_controller
    
    example_path = 'example_graph.mepg'
    if os.path.exists(example_path):
        try:
            with open(example_path, 'rb') as f:
                G = nx.read_graphml(f)
                # Check if the graph is a directed graph
                if not isinstance(G, nx.DiGraph):
                    raise ValueError("The example graph must be a directed graph.")
                fig = graph_controller.get_visualization_data('2d_type')
                plot_pane.object = fig
                fig_risk = graph_controller.get_visualization_data('2d_risk')
                plot_risk_pane.object = fig_risk
                three_d_fig = graph_controller.get_visualization_data('3d_type')
                three_d_pane.object = three_d_fig
                current_graph[0] = G

                # G = add_risk_scores(G)

                update_dropdowns(G)
                # Trigger the maintenance process now that the graph is loaded
                graph_controller.run_rul_simulation()

                file_bytes = f.read()
                result = graph_controller.load_graph_from_file(file_bytes)
                if result['success']:
                    system_controller.refresh_all_displays()
                    system_controller.update_dropdowns()
                    print("Example graph loaded successfully")
                else:
                    print(f"Failed to autoload example graph: {result['error']}")
        except Exception as e:
            print(f"Failed to autoload example graph: {e}")
    else:
        print(f"Example graph file '{example_path}' not found.")

# Create view instance
system_view = SystemView(graph_controller, system_controller)

# Create the main app using SystemView
app = pn.Column(
    pn.pane.Markdown("""
    # MEP System Graph Viewer
    This application allows you to visualize and interact with MEP system graphs.
    """),
    sizing_mode='stretch_width'
)

# Comment out widget registration for now
# system_controller.register_widgets({...})

# system_controller.setup_callbacks()

# File upload widget
file_input = pn.widgets.FileInput(accept='.mepg')
# Note: callback is handled by system_controller.setup_callbacks()

# Name display toggle
name_toggle = pn.widgets.Toggle(name="Use Full Names", value=False)

# Note: callback is handled by system_controller.setup_callbacks()

# --- Graph Generator Panel ---
def generate_graph_callback(event):
    """Generate graph using controller"""
    building_params = {
        'construction_year': construction_year_slider.value,
        'total_load': total_load_slider.value,
        'building_length': building_length_slider.value,
        'building_width': building_width_slider.value,
        'num_floors': num_floors_slider.value,
        'floor_height': floor_height_slider.value,
        'cluster_strength': cluster_strength_slider.value,
        'seed': seed_input.value
    }
    
    result = graph_controller.generate_new_graph(building_params)
    if result['success']:
        system_controller.refresh_all_displays()
        generator_status.object = "**Graph generated successfully!**"
        generator_status.visible = True
        
        # Save generated graph
        output_dir = 'graph_outputs'
        os.makedirs(output_dir, exist_ok=True)
        current_date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(output_dir, f"generated_graph_{current_date_str}.mepg")
        nx.write_graphml(graph_controller.current_graph[0], output_path)
    else:
        generator_status.object = f"**Error generating graph:** {result['error']}"
        generator_status.visible = True

# Generator input widgets with help text
total_load_slider = pn.widgets.IntSlider(
    name="Total Load (kW)", 
    start=50, end=5000, step=50, value=1000
)
total_load_help = pn.pane.Markdown("*Total electrical load for the entire building. Higher loads result in more complex distribution systems with transformers and multiple voltage levels.*", margin=(0, 5))

building_length_slider = pn.widgets.FloatSlider(
    name="Building Length (m)", 
    start=5.0, end=100.0, step=1.0, value=20.0
)
building_length_help = pn.pane.Markdown("*Length of the building in meters. Affects the placement and number of electrical risers needed for distribution.*", margin=(0, 5))

building_width_slider = pn.widgets.FloatSlider(
    name="Building Width (m)", 
    start=5.0, end=100.0, step=1.0, value=20.0
)
building_width_help = pn.pane.Markdown("*Width of the building in meters. Combined with length, determines the building footprint and riser distribution strategy.*", margin=(0, 5))

num_floors_slider = pn.widgets.IntSlider(
    name="Number of Floors", 
    start=1, end=20, step=1, value=4
)
num_floors_help = pn.pane.Markdown("*Number of floors in the building. More floors create taller electrical distribution systems with vertical risers.*", margin=(0, 5))

floor_height_slider = pn.widgets.FloatSlider(
    name="Floor Height (m)", 
    start=2.0, end=6.0, step=0.1, value=3.5
)
floor_height_help = pn.pane.Markdown("*Height of each floor in meters. Affects the total building height and cable run lengths in the 3D visualization.*", margin=(0, 5))

cluster_strength_slider = pn.widgets.FloatSlider(
    name="Cluster Strength", 
    start=0.0, end=1.0, step=0.05, value=0.95
)
cluster_strength_help = pn.pane.Markdown(
    "*Controls how loads are grouped together as nodes.  Does not affect load distribution, but rather how the graph visualizes loads by grouping nearby, similar loads together as single nodes.*",
    margin=(0, 5))

construction_year_slider = pn.widgets.IntSlider(
    name="Construction Year", 
    start=1950, end=2030, step=1, value=datetime.datetime.now().year
)
construction_year_help = pn.pane.Markdown("*Year the building was constructed. This affects the baseline aging and maintenance attributes of all electrical equipment in the building.*", margin=(0, 5))

seed_input = pn.widgets.TextInput(
    name="Seed (optional)", 
    placeholder="Enter number for reproducible results"
)
seed_help = pn.pane.Markdown("*Random seed for reproducible graph generation. Use the same seed to generate identical graphs with the same parameters.*", margin=(0, 5))

generate_button = pn.widgets.Button(name="Generate Graph", button_type="primary")
generate_button.on_click(generate_graph_callback)

generator_status = pn.pane.Markdown(visible=False)

generator_panel = pn.Column(
    "### Generate New MEP Graph",
    pn.Row(total_load_slider, total_load_help),
    pn.Row(num_floors_slider, num_floors_help),
    pn.Row(building_length_slider, building_length_help),
    pn.Row(building_width_slider, building_width_help),
    pn.Row(floor_height_slider, floor_height_help),
    pn.Row(cluster_strength_slider, cluster_strength_help),
    pn.Row(construction_year_slider, construction_year_help),
    pn.Row(seed_input, seed_help),
    generate_button,
    generator_status,
    sizing_mode='stretch_width'
)

generator_accordion = pn.Accordion(
    ("Generate a New MEP Graph", generator_panel),
    # active=0,
    sizing_mode='stretch_width'
)

# Node selection dropdown and info
selection_table_height = 400
node_dropdown = pn.widgets.Select(name="Select Node", options=[])
node_info_pane = pn.pane.Markdown("No node selected.")
# Editable DataFrame for node attributes
node_attr_df = pn.widgets.DataFrame(
    pd.DataFrame(columns=["Attribute", "Value"]),
    editors={
        "Attribute": None,
        "Value": {
            "type": "string",
            "x": "float",
            "y": "float",
            "z": "float"
        }
    },
    height=selection_table_height,
    show_index=False,
)
# Controllers already initialized above

def node_attr_df_callback(event):
    """Delegate to controller"""
    system_controller.handle_node_attr_change(event)

#node_attr_df.param.watch(node_attr_df_callback, 'value') # Commented out - controller handles this

# Add a dropdown for selecting an edge from the graph
edge_dropdown = pn.widgets.Select(name="Select Edge", options=[])
edge_info_pane = pn.pane.Markdown("No edge selected.")
# edge_dropdown.param.watch(edge_dropdown_callback, 'value') # Commented out - controller handles this

# Editable DataFrame for edge attributes
edge_attr_df = pn.widgets.DataFrame(
    pd.DataFrame(columns=["Attribute", "Value"]),
    editors={"Attribute": None, "Value": "string"},
    height=selection_table_height,
    show_index=False,
)

def edge_attr_df_callback(event):
    """Delegate to controller"""
    system_controller.handle_edge_attr_change(event)

# edge_attr_df.param.watch(edge_attr_df_callback, 'value')  # Commented out - controller handles this

# Create a pane to display the selected graph
current_month_pane = pn.pane.Markdown(f"**Current Month:**")
graph_pane = pn.pane.Plotly(height=600, sizing_mode='stretch_width')
bar_chart_pane = pn.pane.Plotly(height=300, sizing_mode='stretch_width')
task_list_pane = pn.pane.Plotly(height=400, sizing_mode='stretch_width')

# --- Play/Pause Animation Controls for graph_slider ---
play_button = pn.widgets.Button(name="Play", button_type="success", width=80)
pause_button = pn.widgets.Button(name="Pause", button_type="warning", width=80, disabled=True)

animation_controls = pn.Row(play_button, pause_button, width=200)

app.append(generator_accordion)

app.append(pn.Column(
    "### Load MEP Graph File",
    file_input,
    pn.Row("### Display Options", name_toggle),
    sizing_mode='stretch_width'
))

# Placeholder for the plot
# 2D visualization by type
two_d_column = pn.Column()
two_d_column.append("### 2D Graph Visualization (Type)")
plot_pane = pn.pane.Plotly(height=600, sizing_mode='stretch_width')
two_d_column.append(plot_pane)

# 2D visualization by risk
two_d_risk_column = pn.Column()
two_d_risk_column.append("### 2D Graph Visualization (Risk Score)")
plot_risk_pane = pn.pane.Plotly(height=600, sizing_mode='stretch_width')
two_d_risk_column.append(plot_risk_pane)

# 3D visualization
three_d_column = pn.Column()
three_d_column.append("### 3D Graph Visualization")
three_d_pane = pn.pane.Plotly(height=600, sizing_mode='stretch_width')
three_d_column.append(three_d_pane)

# Create a row to show all plots side by side
plots_row = pn.Row(two_d_column, two_d_risk_column, three_d_column, sizing_mode='stretch_width')
app.append(plots_row)

node_column = pn.Column("### Node Selection", node_dropdown, node_info_pane, node_attr_df, sizing_mode='stretch_width')

edge_column = pn.Column("### Edge Selection", edge_dropdown, edge_info_pane, edge_attr_df, sizing_mode='stretch_width')

# Create a row for selections
selection_row = pn.Row(node_column, edge_column, sizing_mode='stretch_width')
app.append(selection_row)

# --- Load Maintenance log ---
maintenance_log_input = pn.widgets.FileInput(accept='.csv')

def maintenance_log_callback(event):
    if event.new is not None:
        try:
            file_bytes = io.BytesIO(event.new)
            df = pd.read_csv(file_bytes)
            apply_maintenance_log_to_graph(df, current_graph[0])
            """debug code
            print("=== ALL Component Conditions After Maintenance ===")
            maintenance_processed = 0
            for node_id, attrs in current_graph[0].nodes(data=True):
                node_type = attrs.get('type', 'unknown')
                condition = attrs.get('current_condition', 1.0)
                condition_history = attrs.get('condition_history', [])
                
                # Show all equipment (skip end loads)
                if node_type != 'end_load':
                    print(f"{node_id} ({node_type}): condition = {condition:.2f}, history entries = {len(condition_history)}")
                    maintenance_processed += 1
        
            print(f"=== Total equipment processed: {maintenance_processed} ===")
            print("=== End Component Status ===")"""

            print("✅ Maintenance log applied successfully")
        except Exception as e:
            print(f"❌ Error loading maintenance log: {e}")

maintenance_log_input.param.watch(maintenance_log_callback, 'value')

app.append(pn.Column(
    "### Upload Maintenance Log (.csv)",
    maintenance_log_input,
    sizing_mode='stretch_width'
))

# --- Save Graph UI ---
import datetime

def get_default_filename():
    today = datetime.datetime.now().strftime('%y%m%d')
    return f"{today}_graph.mepg"

filename_input = pn.widgets.TextInput(name="Save As Filename", value=get_default_filename())
save_button = pn.widgets.Button(name="Save Graph", button_type="primary")
save_status = pn.pane.Markdown(visible=False)

def save_graph_callback(event):
    """Delegate to controller"""
    system_controller.handle_save_graph(event)

# Note: callback is handled by system_controller.setup_callbacks()

save_row = pn.Row(filename_input, save_button)
app.append(pn.Column("### Save Graph", save_row, save_status, sizing_mode='stretch_width'))

prioritized_schedule = None

# Process the maintenance tasks
def process_tasks_callback(event=None):
    # Check if graph is loaded
    if current_graph[0] is None:
        print("No graph loaded. Please load or generate a graph first.")
        return
    
    tasks_file_path = tasks_file_input.value
    if not tasks_file_path:
        tasks_file_path = "./tables/example_maintenance_list.csv"
    
    replacement_tasks_path = replacement_tasks_file_input.value
    if not replacement_tasks_path:
        replacement_tasks_path = "./tables/example_replacement_types.csv"

    prioritized_schedule = process_maintenance_tasks(
        tasks_file_path=tasks_file_path,
        replacement_tasks_path=replacement_tasks_path,
        graph=current_graph[0],
        monthly_budget_time=float(monthly_budget_time_input.value),
        monthly_budget_money=float(monthly_budget_money_input.value),
        months_to_schedule=int(num_months_input.value)
    )
    # except Exception as e:
    #     print(f"Error processing maintenance tasks: {e}")
    #     return

    if prioritized_schedule:
        print("Prioritized maintenance schedule generated successfully.")

        number_of_graphs = len(prioritized_schedule)
        print(f"Number of graphs in the prioritized schedule: {number_of_graphs}")

        months = list(prioritized_schedule.keys())

        # Update slider and number input
        graph_slider.end = number_of_graphs
        graph_number_input.end = number_of_graphs
        graph_number_input.start = 1
        graph_number_input.value = graph_slider.value

        # Get the max amount of tasks from any month
        max_tasks_scheduled_for_month = max(len(prioritized_schedule[month].get('tasks_scheduled_for_month', [])) for month in months)
        max_tasks_executed_for_month = max(len(prioritized_schedule[month].get('executed_tasks', [])) for month in months)
        max_tasks_deferred_for_month = max(len(prioritized_schedule[month].get('deferred_tasks', [])) for month in months)

        max_tasks = max(max_tasks_scheduled_for_month, max_tasks_executed_for_month, max_tasks_deferred_for_month)

        def visualize_rul_graph(graph, use_full_names=False, month=None, show_end_loads=False):
            """
            Visualizes a NetworkX graph in 2D with Remaining Useful Life (RUL) coloring.
            Uses the x, y coordinates of nodes for 2D positioning.
            """
            if not show_end_loads:
                # If not showing end loads, filter out nodes with 'end_load' attribute
                graph = graph.copy()
                nodes_to_remove = []
                for n in list(graph.nodes):
                    if graph.nodes[n].get('type') == 'end_load':
                        nodes_to_remove.append(n)
                for n in nodes_to_remove:
                    graph.remove_node(n)

            # Get RUL values for coloring
            rul_values = {n: graph.nodes[n].get('remaining_useful_life_days') for n in graph.nodes}
            # Get max RUL from first month's graph for consistent color scale
            first_month_graph = prioritized_schedule[months[0]].get('graph')
            first_month_rul_values = [first_month_graph.nodes[n].get('remaining_useful_life_days', 0) for n in first_month_graph.nodes]
            max_rul = max(first_month_rul_values)

            fig = _generate_2d_graph_figure(
                graph,
                use_full_names=use_full_names,
                node_color_values=rul_values,
                color_palette='Agsunset',
                colorbar_title='Remaining Useful Life (RUL)',
                showlegend=False,
                colorbar_range=[0, max_rul]
            )

            # Add a title to the figure
            fig.update_layout(title=f"Remaining Useful Life (RUL) - {month}")

            return fig

        def update_graph(event):
            # Keep number input in sync with slider
            if graph_number_input.value != event.new:
                graph_number_input.value = event.new
            graph_index = event.new - 1
            if 0 <= graph_index < number_of_graphs:
                month = months[graph_index]
                current_month_pane.object = f"**Current Month:** {month}"
                # Get the graph snapshot and convert to Plotly figure
                graph_snapshot = prioritized_schedule[month].get('graph')
                fig = visualize_rul_graph(graph_snapshot, use_full_names=name_toggle.value, month=month, show_end_loads=show_end_loads_toggle.value)
                graph_pane.object = fig

        def _generate_task_list_figure(scheduled_tasks, executed_tasks, deferred_tasks, max_tasks):
            # Create a figure for the task list
            fig = go.Figure()
            fig.add_trace(go.Bar(x=['Scheduled', 'Executed', 'Deferred'],
                                 y=[len(scheduled_tasks), len(executed_tasks), len(deferred_tasks)],
                                 marker_color=['blue', 'green', 'red']))
            fig.update_layout(title='Task List Overview', barmode='stack')

            # Set the y-axis range
            fig.update_yaxes(range=[0, max_tasks + 10])

            return fig

        def _generate_bar_chart_figure(prioritized_schedule):
            """
            Creates a bar chart figure for task status over time.
            X-axis: Time
            Y-axis: Number of Tasks
            Bars:
              - Number of Scheduled Tasks for this Month
              - Number of Executed Tasks for this Month
              - Number of Deferred Tasks for this Month
            """
            fig = go.Figure()

            numbers_of_scheduled = []
            numbers_of_executed = []
            numbers_of_deferred = []

            month_datetime_periods = prioritized_schedule.keys()
            month_names = [month.start_time.strftime("%Y-%m") for month in month_datetime_periods]
            # for m in month_names[:10]:
            #     print(f"Month: {m}")

            for month in prioritized_schedule:
                numbers_of_scheduled.append(len(prioritized_schedule[month].get('tasks_scheduled_for_month')))
                numbers_of_executed.append(len(prioritized_schedule[month].get('executed_tasks')))
                numbers_of_deferred.append(len(prioritized_schedule[month].get('deferred_tasks')))

            print(f"Most Scheduled Tasks: {max(numbers_of_scheduled)}")
            print(f"Most Executed Tasks: {max(numbers_of_executed)}")
            print(f"Most Deferred Tasks: {max(numbers_of_deferred)}")

            fig.add_trace(go.Bar(x=month_names, y=numbers_of_scheduled, name='Scheduled', marker_color='blue'))
            fig.add_trace(go.Bar(x=month_names, y=numbers_of_executed, name='Executed', marker_color='green'))
            fig.add_trace(go.Bar(x=month_names, y=numbers_of_deferred, name='Deferred', marker_color='red'))

            fig.update_layout(title='Task Status Over Time', xaxis_title='Time', yaxis_title='Number of Tasks')
            fig.update_yaxes(range=[0, max_tasks + 10])

            # Show no x axis tick marks
            fig.update_xaxes(showticklabels=False)

            return fig

        def update_task_pane(event):
            # Update the task list pane based on the selected month
            if graph_number_input.value != event.new:
                graph_number_input.value = event.new
            graph_index = event.new - 1
            if 0 <= graph_index < number_of_graphs:
                month = months[graph_index]
                tasks_scheduled_for_month = prioritized_schedule[month].get('tasks_scheduled_for_month')
                executed_tasks = prioritized_schedule[month].get('executed_tasks')
                deferred_tasks = prioritized_schedule[month].get('deferred_tasks')
                task_list_plot.object = _generate_task_list_figure(tasks_scheduled_for_month, executed_tasks, deferred_tasks, max_tasks)

        def update_number_input(event):
            # Keep slider in sync with number input
            if graph_slider.value != event.new:
                graph_slider.value = event.new
        
        # Add timeline-specific callbacks alongside controller callbacks
        def update_timeline_display(event):
            """Handle timeline-specific updates for slider changes"""
            # Keep number input in sync with slider
            if graph_number_input.value != event.new:
                graph_number_input.value = event.new
            graph_index = event.new - 1
            if 0 <= graph_index < number_of_graphs:
                month = months[graph_index]
                current_month_pane.object = f"**Current Month:** {month}"
                # Get the graph snapshot and convert to Plotly figure
                graph_snapshot = prioritized_schedule[month].get('graph')
                fig = visualize_rul_graph(graph_snapshot, use_full_names=name_toggle.value, month=month, show_end_loads=show_end_loads_toggle.value)
                graph_pane.object = fig
                
                # Update task list
                tasks_scheduled_for_month = prioritized_schedule[month].get('tasks_scheduled_for_month')
                executed_tasks = prioritized_schedule[month].get('executed_tasks')
                deferred_tasks = prioritized_schedule[month].get('deferred_tasks')
                task_list_pane.object = _generate_task_list_figure(tasks_scheduled_for_month, executed_tasks, deferred_tasks, max_tasks)
        
        # Register timeline callbacks (these work alongside the controller callbacks)
        graph_slider.param.watch(update_timeline_display, 'value')
        graph_number_input.param.watch(update_number_input, 'value')
        # Display the first graph by default
        if number_of_graphs > 0:
            month = months[0]
            current_month_pane.object = f"**Current Month:** {month}"
            graph_snapshot = prioritized_schedule[month].get('graph')
            fig = visualize_rul_graph(graph_snapshot, use_full_names=name_toggle.value, month=month, show_end_loads=show_end_loads_toggle.value)
            graph_pane.object = fig

            # Update the task list pane
            tasks_scheduled_for_month = prioritized_schedule[month].get('tasks_scheduled_for_month')
            executed_tasks = prioritized_schedule[month].get('executed_tasks')
            deferred_tasks = prioritized_schedule[month].get('deferred_tasks')
            task_list_plot.object = _generate_task_list_figure(tasks_scheduled_for_month, executed_tasks, deferred_tasks, max_tasks)

            # Update the line chart pane
            bar_chart_pane.object = _generate_bar_chart_figure(prioritized_schedule)
# Add inputs for maintenance task parameters

# Create a slider and number input for graph selection
graph_slider = pn.widgets.IntSlider(
    name="Select Graph",
    start=1,
    end=36,  # Default end value, will be updated later
    value=1,
    step=1
)
graph_number_input = pn.widgets.IntInput(
    name="Graph #",
    value=1,
    step=1,
    start=1,
    end=36
)
task_list_plot = pn.pane.Plotly(height=600, sizing_mode='stretch_width')

# Show both slider and number input together
app.append(pn.Column(
    "### Prioritized Maintenance Schedule",
    pn.Row(graph_slider, graph_number_input, animation_controls),
    current_month_pane,
    bar_chart_pane,
    pn.Row(graph_pane, task_list_plot),
    sizing_mode='stretch_width'
))

monthly_budget_time_input = pn.widgets.TextInput(name="Monthly Budget (Time)", value="50")
monthly_budget_money_input = pn.widgets.TextInput(name="Monthly Budget (Money)", value="20000")
show_end_loads_toggle = pn.widgets.Checkbox(name="Show End Loads", value=False)
num_months_input = pn.widgets.TextInput(name="Months to Schedule", value="1000")
tasks_file_input = pn.widgets.FileInput(name="Tasks File", accept='.csv')
replacement_tasks_file_input = pn.widgets.FileInput(name="Replacement Tasks File", accept='.csv')
process_tasks_button = pn.widgets.Button(name="Process Tasks", button_type="primary")

maintenance_task_panel = pn.Column(
    pn.Row(monthly_budget_time_input, monthly_budget_money_input, show_end_loads_toggle),
    pn.Row(num_months_input),
    pn.Row(tasks_file_input, replacement_tasks_file_input),
    process_tasks_button
)

# Set up the button callback
process_tasks_button.on_click(lambda event: graph_controller.run_rul_simulation())
# # Automatically process tasks when graph is loaded
# def auto_process_tasks_if_graph_loaded():
#     if current_graph[0] is not None:
#         process_tasks_callback()

# auto_process_tasks_if_graph_loaded()  # Initial call to populate the app if graph is already loaded

app.append(pn.Column(
    "### Process Maintenance Tasks",
    maintenance_task_panel,
    sizing_mode='stretch_width'
))

if current_graph[0] is not None:
    testing_section = pn.Column("### RUL Testing & Parameter Controls")
    
    # Component condition testing
    condition_test_row = pn.Row()
    
    test_component_select = pn.widgets.Select(
        name="Select Component",
        options=[n for n, d in current_graph[0].nodes(data=True) if d.get('type') != 'end_load'],
        width=250
    )
    
    test_condition_slider = pn.widgets.FloatSlider(
        name="Set Condition (0=Broken, 1=Perfect)",
        start=0.0, end=1.0, step=0.05, value=0.8, width=300
    )
    
    test_update_btn = pn.widgets.Button(name="Update Condition", button_type="primary", width=150)
    test_status = pn.pane.Markdown("Ready to test component conditions", width=400)
    
    def test_update_condition(event):
        if test_component_select.value and current_graph[0]:
            try:
                from helpers.rul_helper import update_component_condition
                success = update_component_condition(
                    current_graph[0], 
                    test_component_select.value, 
                    test_condition_slider.value,
                    "Manual test update"
                )
                if success:
                    test_status.object = f"✅ Updated {test_component_select.value} condition to {test_condition_slider.value:.2f}"
                    # Refresh visualizations
                    plot_pane.object = visualize_graph_two_d(current_graph[0], use_full_names=name_toggle.value)
                else:
                    test_status.object = "❌ Update failed"
            except Exception as e:
                test_status.object = f"❌ Error: {str(e)}"
        else:
            test_status.object = "❌ No component selected or graph missing"

    test_update_btn.on_click(test_update_condition)
    
    condition_test_row.extend([test_component_select, test_condition_slider, test_update_btn])
    
    # Parameter adjustment controls
    param_control_row = pn.Row()
    
    deferment_factor_slider = pn.widgets.FloatSlider(
        name="Task Deferment Factor", 
        start=0.01, end=0.10, step=0.01, value=0.04, width=250
    )
    
    aging_factor_slider = pn.widgets.FloatSlider(
        name="Aging Acceleration Factor",
        start=0.01, end=0.05, step=0.005, value=0.02, width=250
    )
    
    update_params_btn = pn.widgets.Button(name="Update Parameters", button_type="success", width=150)
    params_status = pn.pane.Markdown("Ready to test parameters", width=400)
    
    def update_parameters(event):
        try:
            from helpers.rul_helper import adjust_rul_parameters, apply_rul_to_graph
            changes = adjust_rul_parameters(
                TASK_DEFERMENT_FACTOR=deferment_factor_slider.value,
                AGING_ACCELERATION_FACTOR=aging_factor_slider.value
            )
            
            # Recalculate RUL with new parameters
            apply_rul_to_graph(current_graph[0])
            
            # Refresh visualization
            plot_pane.object = visualize_graph_two_d(current_graph[0], use_full_names=name_toggle.value)
            
            params_status.object = f"✅ Updated parameters and recalculated RUL"
        except Exception as e:
            params_status.object = f"❌ Error: {str(e)}"
    
    update_params_btn.on_click(update_parameters)
    
    param_control_row.extend([deferment_factor_slider, aging_factor_slider, update_params_btn])
    
    # Quick condition presets
    preset_row = pn.Row()
    
    simulate_wear_btn = pn.widgets.Button(name="Simulate Equipment Wear", button_type="light", width=200)
    reset_conditions_btn = pn.widgets.Button(name="Reset All to Perfect", button_type="warning", width=200)
    preset_status = pn.pane.Markdown("Ready for quick actions", width=400)
    
    def simulate_wear(event):
        try:
            from helpers.rul_helper import update_component_condition
            count = 0
            for node_id, attrs in current_graph[0].nodes(data=True):
                if attrs.get('type') != 'end_load':
                    # Simulate random wear between 0.3 and 0.9
                    import random
                    wear_condition = random.uniform(0.3, 0.9)
                    update_component_condition(current_graph[0], node_id, wear_condition, "Simulated wear")
                    count += 1
            
            plot_pane.object = visualize_graph_two_d(current_graph[0], use_full_names=name_toggle.value)
            preset_status.object = f"✅ Simulated wear on {count} components"
        except Exception as e:
            preset_status.object = f"❌ Error: {str(e)}"
    
    def reset_conditions(event):
        try:
            from helpers.rul_helper import reset_all_conditions
            count = reset_all_conditions(current_graph[0], 1.0, "Reset to perfect")
            plot_pane.object = visualize_graph_two_d(current_graph[0], use_full_names=name_toggle.value)
            preset_status.object = f"✅ Reset {count} components to perfect condition"
        except Exception as e:
            preset_status.object = f"❌ Error: {str(e)}"
    
    
    simulate_wear_btn.on_click(simulate_wear)
    reset_conditions_btn.on_click(reset_conditions)
    
    preset_row.extend([simulate_wear_btn, reset_conditions_btn])
    
    # Assemble testing section
    testing_section.extend([
        "**Component Condition Testing:**",
        condition_test_row,
        test_status,
        "**Parameter Controls:**", 
        param_control_row,
        params_status,
        "**Quick Actions:**",
        preset_row,
        preset_status
    ])
    
    app.append(testing_section)

# Register all widgets with the controller
system_controller.register_widgets({
    'file_input': file_input,
    'save_button': save_button,
    'save_input': filename_input,
    'save_status': save_status,
    'plot_pane': plot_pane,
    'plot_risk_pane': plot_risk_pane,
    'three_d_pane': three_d_pane,
    'name_toggle': name_toggle,
    'node_dropdown': node_dropdown,
    'edge_dropdown': edge_dropdown,
    'node_info_pane': node_info_pane,
    'edge_info_pane': edge_info_pane,
    'node_attr_df': node_attr_df,
    'edge_attr_df': edge_attr_df,
    'graph_slider': graph_slider,
    'play_button': play_button,
    'pause_button': pause_button,
    'graph_number_input': graph_number_input,
    'current_month_pane': current_month_pane,
    'graph_pane': graph_pane,
    'task_list_pane': task_list_pane
})

# Setup all event handlers
system_controller.setup_callbacks()

# Autoload example graph if present
autoload_example_graph()

print("Starting MEP System Graph Viewer...")
app.servable()
