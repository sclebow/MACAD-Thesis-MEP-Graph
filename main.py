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
analytics_container = pn.GridSpec(nrows=5, ncols=4, mode="error")
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

# Create main application layout
app = pn.Column(
    pn.pane.Markdown("## MEP Digital Twin\nBuilding Systems Management"),
    main_tabs
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
main_tabs.active = 0

print("Starting Application...")

# Make the app servable for panel serve command
app.servable()

# Allow running directly with Python for debugging
if __name__ == "__main__":
    # Run the app in debug mode when executed directly
    app.show(port=5008)
