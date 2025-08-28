# This is a helper function for the button callbacks
import panel as pn
import networkx as nx
import datetime
import base64

from helpers.controllers.graph_controller import GraphController

def upload_graph_from_file(file_content, filename, graph_controller, graph_container):
    """Handle file upload and update graph visualization"""
    print(f"Uploading file: {filename}")
    
    # Load graph using GraphController
    result = graph_controller.load_graph_from_file(file_content)
    
    if result['success']:
        # Update the graph visualization
        fig = graph_controller.get_visualization_data()
        graph_container.object = fig
        print(f"Graph loaded successfully from {filename}")

def export_graph(event, graph_controller: GraphController, app):
    now = datetime.datetime.now()
    now_str = now.strftime("%Y%m%d_%H%M%S")
    filename = f"exported_graph_{now_str}.mepg"

    graph = graph_controller.current_graph[0]

    # Get the graphml representation
    graphml_generator = nx.generate_graphml(graph)

    print(graphml_generator)

    lines = []

    for line in graphml_generator:
        lines.append(line)

    file_string = "\n".join(lines)

    # Encode the file content
    file_bytes = file_string.encode('utf-8')
    b64_content = base64.b64encode(file_bytes).decode('utf-8')
    
    # Create download HTML
    download_html = f"""
    <script>
    var element = document.createElement('a');
    element.setAttribute('href', 'data:text/plain;charset=utf-8;base64,{b64_content}');
    element.setAttribute('download', '{filename}');
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
    </script>
    """
    
    # Display the download HTML (this triggers the download)
    download_pane = pn.pane.HTML(download_html)
    
    # You can add this to a temporary container or use a notification
    print(f"Exporting graph as {filename}")
    app.append(download_pane)

def reset_graph(event, graph_controller):
    # Reset the panel application
    pn.state.location.reload = False
    pn.state.location.reload = True

def run_simulation(event, graph_controller):
    print("Run Simulation button clicked")

def failure_timeline_reset_view(event):
    print("Failure Timeline Reset View button clicked")

def failure_timeline_zoom_in(event):
    print("Failure Timeline Zoom In button clicked")

def failure_timeline_zoom_out(event):
    print("Failure Timeline Zoom Out button clicked")

def export_failure_schedule(event):
    print("Export Failure Schedule button clicked")

def export_annual_budget_forecast(event):
    print("Export Annual Budget Forecast button clicked")

def reset_lifecycle_analysis_controls(event):
    print("Reset Lifecycle Analysis Controls button clicked")

def run_lifecycle_analysis_simulation(event):
    print("Run Lifecycle Analysis Simulation button clicked")

def save_settings(event):
    print("Save Settings button clicked")

def import_data(event):
    print("Import Data button clicked")

def export_data(event):
    print("Export Data button clicked")

def clear_all_data(event):
    print("Clear All Data button clicked")