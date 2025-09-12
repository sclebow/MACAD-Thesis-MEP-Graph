import pandas as pd
import panel as pn
import datetime

from helpers.panel.button_callbacks import generate_graph

def layout_graph_generator(graph_generator_container, graph_controller, DEFAULT_BUILDING_PARAMS):
    graph_generator_container.append(
        pn.pane.Markdown("## Graph Generator", sizing_mode="stretch_width"),
    )
    construction_year_input = pn.widgets.IntInput(
            name="Construction Year", 
            value=DEFAULT_BUILDING_PARAMS["construction_year"], 
            step=1,
        )
    total_load_input = pn.widgets.FloatInput(
            name="Total Load (kW)", 
            value=DEFAULT_BUILDING_PARAMS["total_load"], 
            step=50,
        )
    building_length_input = pn.widgets.FloatInput(
            name="Building Length (m)", 
            value=DEFAULT_BUILDING_PARAMS["building_length"], 
            step=1.0,
        )
    building_width_input = pn.widgets.FloatInput(
            name="Building Width (m)", 
            value=DEFAULT_BUILDING_PARAMS["building_width"], 
            step=1.0,
        )
    num_floors_input = pn.widgets.IntInput(
            name="Number of Floors", 
            value=DEFAULT_BUILDING_PARAMS["num_floors"], 
            step=1,
        )
    floor_height_input = pn.widgets.FloatInput(
            name="Floor Height (m)", 
            value=DEFAULT_BUILDING_PARAMS["floor_height"], 
            step=0.1,
        )
    cluster_strength_input = pn.widgets.FloatInput(
            name="Cluster Strength", 
            value=DEFAULT_BUILDING_PARAMS["cluster_strength"], 
            step=0.05,
        )
    seed_input = pn.widgets.IntInput(
            name="Random Seed", 
            value=DEFAULT_BUILDING_PARAMS["seed"], 
            step=1,
        )

    generate_button = pn.widgets.Button(name="Generate Graph", button_type="primary", icon="cogs")
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
        pn.Row(
            construction_year_input,
            pn.pane.Markdown("Older buildings will allow the simulation of more failures and maintenance needs.")
        ),
        pn.Row(
            total_load_input,
            pn.pane.Markdown("The total electrical load of the building, influencing the number and type of distribution equipment.")
        ),
        pn.Row(
            building_length_input,
            pn.pane.Markdown("The length of the building footprint, affecting spatial distribution of equipment and the number of vertical risers.")
        ),
        pn.Row(
            building_width_input,
            pn.pane.Markdown("The width of the building footprint, affecting spatial distribution of equipment and the number of vertical risers.")
        ),
        pn.Row(
            num_floors_input,
            pn.pane.Markdown("The total number of floors, determining vertical distribution and riser lengths.")
        ),
        pn.Row(
            floor_height_input,
            pn.pane.Markdown("The height of each floor, influencing vertical spacing and riser lengths.")
        ),
        pn.Row(
            cluster_strength_input,
            pn.pane.Markdown("Determines how many end loads are grouped together in the final graph. 0 means maximal clustering; 1 means all end loads are individual.")
        ),
        pn.Row(
            seed_input,
            pn.pane.Markdown("An optional integer seed for random number generation to ensure reproducibility of the synthetic data.")
        ),
        generate_button
    )

    graph_generator_container.append(inputs_column)