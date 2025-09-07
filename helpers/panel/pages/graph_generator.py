import pandas as pd
import panel as pn
import datetime

from helpers.panel.button_callbacks import generate_graph

def layout_graph_generator(graph_generator_container, graph_controller, DEFAULT_BUILDING_PARAMS):
    graph_generator_container.append(
        pn.pane.Markdown("## Graph Generator", sizing_mode="stretch_width"),
    )

    construction_year_input = pn.widgets.IntInput(name="Construction Year", value=DEFAULT_BUILDING_PARAMS["construction_year"], step=1)
    total_load_input = pn.widgets.FloatInput(name="Total Load (kW)", value=DEFAULT_BUILDING_PARAMS["total_load"], step=50)
    building_length_input = pn.widgets.FloatInput(name="Building Length (m)", value=DEFAULT_BUILDING_PARAMS["building_length"], step=1.0)
    building_width_input = pn.widgets.FloatInput(name="Building Width (m)", value=DEFAULT_BUILDING_PARAMS["building_width"], step=1.0)
    num_floors_input = pn.widgets.IntInput(name="Number of Floors", value=DEFAULT_BUILDING_PARAMS["num_floors"], step=1)
    floor_height_input = pn.widgets.FloatInput(name="Floor Height (m)", value=DEFAULT_BUILDING_PARAMS["floor_height"], step=0.1)
    cluster_strength_input = pn.widgets.FloatInput(name="Cluster Strength", value=DEFAULT_BUILDING_PARAMS["cluster_strength"], step=0.05)
    seed_input = pn.widgets.IntInput(name="Random Seed", value=DEFAULT_BUILDING_PARAMS["seed"], step=1)

    generate_button = pn.widgets.Button(name="Generate Graph", button_type="primary", icon="cogs", align="center")
    generate_button.on_click(lambda event: generate_graph(event, graph_controller, {
        "construction_year": construction_year_input.value,
        "total_load": total_load_input.value,
        "building_length": building_length_input.value,
        "building_width": building_width_input.value,
        "num_floors": num_floors_input.value,
        "floor_height": floor_height_input.value,
        "cluster_strength": cluster_strength_input.value,
        "seed": seed_input.value
    }))

    inputs_column = pn.Column(
        pn.pane.Markdown("### Graph Parameters"),
        construction_year_input,
        total_load_input,
        building_length_input,
        building_width_input,
        num_floors_input,
        floor_height_input,
        cluster_strength_input,
        seed_input,
        generate_button
    )

    graph_generator_container.append(inputs_column)