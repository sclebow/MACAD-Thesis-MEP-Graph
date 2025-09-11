# This is a panel python application to view the the maintenance building system graphs, and run simulations.
# We start with just defining the ui and layout
# Actual processes will be stored in separate modules

import panel as pn
import pandas as pd

from helpers.panel.button_callbacks import update_current_date, run_simulation, generate_graph

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
from helpers.panel.pages.graph_generator import layout_graph_generator
from helpers.panel.pages.budget_goal_seeker import layout_budget_goal_seeker
from helpers.panel.pages.side_by_side_comparison import layout_side_by_side_comparison

pn.extension('plotly')

TEST_DATA_INDEX = 0

TEST_DATA = [
    {
        "DEFAULT_BUILDING_PARAMS": {
            "construction_year": pd.Timestamp.now().year - 25,
            "total_load": 1000,  # in kW
            "building_length": 20.0,  # in meters
            "building_width": 20.0,   # in meters
            "num_floors": 4,
            "floor_height": 3.5,      # in meters
            "cluster_strength": 0.95, # between 0 and 1
            "seed": 42
        },
        "DEFAULT_SIMULATION_PARAMS": {
            "budget_hours": 40,
            "budget_money": 10000,
            "weeks_to_schedule": 360
        }
    },
    {
        "DEFAULT_BUILDING_PARAMS": {
            "construction_year": pd.Timestamp.now().year - 25,
            "total_load": 200,  # in kW
            "building_length": 20.0,  # in meters
            "building_width": 20.0,   # in meters
        "num_floors": 1,
        "floor_height": 3.5,      # in meters
        "cluster_strength": 0.95, # between 0 and 1
            "seed": 42
        },
        "DEFAULT_SIMULATION_PARAMS": {
            "budget_hours": 1,
            "budget_money": 10000,
            "weeks_to_schedule": 360
        }
    },
]

DEFAULT_BUILDING_PARAMS = TEST_DATA[TEST_DATA_INDEX]["DEFAULT_BUILDING_PARAMS"]
DEFAULT_SIMULATION_PARAMS = TEST_DATA[TEST_DATA_INDEX]["DEFAULT_SIMULATION_PARAMS"]

graph_controller = GraphController()

# Create containers for each tab
system_view_container = pn.GridSpec(nrows=10, ncols=3, mode="error")
failure_prediction_container = pn.Column()
maintenance_container = pn.Column()
analytics_container = pn.Column()
settings_container = pn.Column()
graph_generator_container = pn.Column()
budget_goal_seeker_container = pn.Column()
side_by_side_comparison_container = pn.Column()

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
    ("Graph Generator", graph_generator_container),
    ("Budget Goal Seeker", budget_goal_seeker_container),
    ("Side-by-Side Comparison", side_by_side_comparison_container),
    dynamic=True,
    tabs_location="left",
    stylesheets=[stylesheet]
)

# run_simulation_button = pn.widgets.Button(name="Run Simulation", button_type="primary", icon="play", on_click=lambda event: run_simulation(event, graph_controller), align="center")

default_current_date = pd.Timestamp.now()
graph_controller.current_date = default_current_date

current_date_input = pn.widgets.DatePicker(name="Current Date", value=default_current_date, align="center")
# Watch for changes to the date input
current_date_input.param.watch(lambda event: update_current_date(event.new, graph_controller), 'value')

app_status_container = pn.Row(
    align="center",
)
pn.state.cache['app_status_container'] = app_status_container

# Create main application layout
app = pn.Column(
    pn.Row(
        pn.Column(
            pn.pane.PNG('assetpulse_logo.png', width=120, height=120, align='start'),
            sizing_mode='fixed',
            width=120
        ),
    pn.pane.Markdown("<span style='font-size:16px;font-weight:400;line-height:1.2;'>From Data to<br>Foresight</span>", sizing_mode='fixed', width=120, height=80),
        # run_simulation_button,
        current_date_input,
        app_status_container,
    ),
    main_tabs,
)
pn.state.cache["app"] = app

# Layout the System View
layout_system_view(system_view_container, graph_controller)

# Layout the Failure Prediction tab
layout_failure_prediction(failure_prediction_container, graph_controller)

# Layout Maintenance Tabs
layout_maintenance(maintenance_container, graph_controller)

# Layout Analytics
layout_analytics(analytics_container, graph_controller)

# Layout Settings
layout_settings(settings_container, graph_controller, DEFAULT_SIMULATION_PARAMS)

# Layout Graph Generator
layout_graph_generator(graph_generator_container, graph_controller, DEFAULT_BUILDING_PARAMS)

# Layout Budget Goal Seeker
layout_budget_goal_seeker(budget_goal_seeker_container, graph_controller)

# Layout Side-by-Side Comparison
layout_side_by_side_comparison(side_by_side_comparison_container, graph_controller)

# DEBUG Set default tabs
main_tabs.active = 7

print("Starting Application...")

# Make the app servable for panel serve command
app.servable()

# Generate a default graph on startup and run simulation (inside the graph generation)
generate_graph(None, graph_controller, DEFAULT_BUILDING_PARAMS)

# Allow running directly with Python for debugging
if __name__ == "__main__":
    # Run the app in debug mode when executed directly.
    # Never bind to known-unsafe ports (6000 is unsafe in many browsers).
    import os
    import sys
    app.show()
    # def _choose_safe_port(default_port: int = 5006) -> int:
    #     """Choose a port that is in the SAFE_PORTS list and is allowed by the environment.

    #     Priority: PANEL_PORT env var -> PORT env var -> default_port.
    #     If the resolved port is not in SAFE_PORTS, it will be replaced by the closest safe port.
    #     """
    #     port = None
    #     for env in ("PANEL_PORT", "PORT"):
    #         val = os.getenv(env)
    #         if val:
    #             try:
    #                 port = int(val)
    #                 break
    #             except ValueError:
    #                 # ignore malformed env values
    #                 pass
    #     if port is None:
    #         port = default_port
    #     if port in unsafe:
    #         print(f"Refusing to bind to unsafe port {port}; falling back to {default_port}")
    #         port = default_port
    #     return port

    # port = _choose_safe_port(5006)
    # try:
    #     app.show(port=port)
    # except OSError as e:
    #     # If the chosen port is in use or fails to bind, try a nearby safe port and exit if that fails.
    #     print(f"Failed to start Panel on port {port}: {e}")
    #     fallback = 5006 if port != 5006 else 5056
    #     if fallback == 6000:
    #         fallback = 5006
    #     print(f"Attempting fallback port {fallback}")
    #     try:
    #         app.show(port=fallback)
    #     except Exception as e2:
    #         print(f"Failed to start Panel on fallback port {fallback}: {e2}")
    #         sys.exit(1)
