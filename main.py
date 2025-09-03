# This is a panel python application to view the the maintenance building system graphs, and run simulations.
# We start with just defining the ui and layout
# Actual processes will be stored in separate modules

import panel as pn
import pandas as pd

from helpers.panel.button_callbacks import *

# Enable Panel debug mode
# pn.config.debug = True

# Create the graph controller
from helpers.controllers.graph_controller import GraphController

# Import the pages
from helpers.panel.pages.system_view import layout_system_view
from helpers.panel.pages.failure_prediction import layout_failure_prediction
from helpers.panel.pages.maintenance import layout_maintenance
from helpers.panel.pages.analytics import layout_analytics
from helpers.panel.pages.settings import layout_settings

graph_controller = GraphController()

# Create containers for each tab
system_view_container = pn.GridSpec(nrows=10, ncols=3, mode="error")
failure_prediction_container = pn.Column()
maintenance_container = pn.Column()
analytics_container = pn.Column()
settings_container = pn.Column()

# Create main tabs page
# Create a stylesheet for the tabs
stylesheet = """
    .bk-tab {
        text-align: left;
    }
"""

# Create main tabs
main_tabs = pn.Tabs(
    ("System View", system_view_container),
    ("Failure Prediction", failure_prediction_container),
    ("Maintenance", maintenance_container),
    ("Analytics", analytics_container),
    ("Settings", settings_container),
    dynamic=True,
    tabs_location="left",
    stylesheets=[stylesheet]
)

run_simulation_button = pn.widgets.Button(name="Run Simulation", button_type="primary", icon="play", on_click=lambda event: run_simulation(event, graph_controller), align="center")

default_current_date = pd.Timestamp.now() + pd.DateOffset(years=25)
graph_controller.current_date = default_current_date

current_date_input = pn.widgets.DatePicker(name="Current Date", value=default_current_date)
# Watch for changes to the date input
current_date_input.param.watch(lambda event: update_current_date(event, graph_controller), 'value')

# Create main application layout
app = pn.Column(
    pn.Row(
        pn.pane.Markdown("## MEP Digital Twin\nBuilding Systems Management"),
        run_simulation_button,
        current_date_input
    ),
    main_tabs,
)

# Layout the System View
layout_system_view(system_view_container, graph_controller, app)

# Layout the Failure Prediction tab
layout_failure_prediction(failure_prediction_container, graph_controller)

# Layout Maintenance Tabs
layout_maintenance(maintenance_container, graph_controller)

# Layout Analytics
layout_analytics(analytics_container, graph_controller)

# Layout Settings
layout_settings(settings_container, graph_controller)

# DEBUG Set default tabs
main_tabs.active = 3

print("Starting Application...")

# Make the app servable for panel serve command
app.servable()

# Auto-run simulation on load
run_simulation(None, graph_controller)

# Allow running directly with Python for debugging
if __name__ == "__main__":
    # Run the app in debug mode when executed directly
    app.show(port=5008)
