import pandas as pd
import panel as pn
import datetime

from helpers.panel.button_callbacks import generate_graph

def layout_graph_generator(graph_generator_container, graph_controller):
    graph_generator_container.append(
        pn.pane.Markdown("## Graph Generator", sizing_mode="stretch_width"),
    )
    
    construction_year_input = pn.widgets.IntInput(name="Construction Year", value=datetime.datetime.now().year, step=1)
    total_load_input = pn.widgets.FloatInput(name="Total Load (kW)", value=1000, step=50)
    building_length_input = pn.widgets.FloatInput(name="Building Length (m)", value=20.0, step=1.0)
    building_width_input = pn.widgets.FloatInput(name="Building Width (m)", value=20.0, step=1.0)
    num_floors_input = pn.widgets.IntInput(name="Number of Floors", value=4, step=1)
    floor_height_input = pn.widgets.FloatInput(name="Floor Height (m)", value=3.5, step=0.1)
    cluster_strength_input = pn.widgets.FloatInput(name="Cluster Length (m)", value=0.95, step=0.05)
    seed_input = pn.widgets.IntInput(name="Random Seed", value=42, step=1)
    
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