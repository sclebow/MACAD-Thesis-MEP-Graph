# Copyright (C) 2025  Scott Lebow and Krisztian Hajdu

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Author contact:
# Scott Lebow: scott.lebow@student.iaac.net
# Krisztian Hajdu: krisztian.hajdu@students.iaac.net

import pandas as pd
import panel as pn
import datetime

from helpers.panel.button_callbacks import generate_graph

def layout_graph_generator(graph_generator_container, graph_controller, TEST_DATA, TEST_DATA_INDEX):
    graph_generator_container.sizing_mode = "stretch_width"
    # Add a selection widget for test data
    test_data_selector = pn.widgets.Select(
        name="Test Data",
        options=list(TEST_DATA.keys()),
        value=TEST_DATA_INDEX,
        width=300,
    )

    # Update inputs when test data selection changes
    def _update_inputs(event):
        nonlocal DEFAULT_BUILDING_PARAMS
        DEFAULT_BUILDING_PARAMS = TEST_DATA[event.new]["DEFAULT_BUILDING_PARAMS"]
        construction_year_input.value = DEFAULT_BUILDING_PARAMS.get("construction_year", construction_year_input.value)
        total_load_input.value = DEFAULT_BUILDING_PARAMS.get("total_load", total_load_input.value)
        building_length_input.value = DEFAULT_BUILDING_PARAMS.get("building_length", building_length_input.value)
        building_width_input.value = DEFAULT_BUILDING_PARAMS.get("building_width", building_width_input.value)
        num_floors_input.value = DEFAULT_BUILDING_PARAMS.get("num_floors", num_floors_input.value)
        floor_height_input.value = DEFAULT_BUILDING_PARAMS.get("floor_height", floor_height_input.value)
        cluster_strength_input.value = DEFAULT_BUILDING_PARAMS.get("cluster_strength", cluster_strength_input.value)
        seed_input.value = DEFAULT_BUILDING_PARAMS.get("seed", seed_input.value)

    test_data_selector.param.watch(_update_inputs, 'value')

    DEFAULT_BUILDING_PARAMS = TEST_DATA[TEST_DATA_INDEX]["DEFAULT_BUILDING_PARAMS"]
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
        pn.pane.Markdown("## Graph Generator"),
        test_data_selector,
        pn.pane.Markdown("### Graph Parameters"),
        pn.Row(
            construction_year_input,
            pn.pane.Markdown("Older buildings will allow the simulation of more failures and maintenance needs.", width=400)
        ),
        pn.Row(
            total_load_input,
            pn.pane.Markdown("The total electrical load of the building, influencing the number and type of distribution equipment.", width=400)
        ),
        pn.Row(
            building_length_input,
            pn.pane.Markdown("The length of the building footprint, affecting spatial distribution of equipment and the number of vertical risers.", width=400)
        ),
        pn.Row(
            building_width_input,
            pn.pane.Markdown("The width of the building footprint, affecting spatial distribution of equipment and the number of vertical risers.", width=400)
        ),
        pn.Row(
            num_floors_input,
            pn.pane.Markdown("The total number of floors, determining vertical distribution and riser lengths.", width=400)
        ),
        pn.Row(
            floor_height_input,
            pn.pane.Markdown("The height of each floor, influencing vertical spacing and riser lengths.", width=400)
        ),
        pn.Row(
            cluster_strength_input,
            pn.pane.Markdown("Determines how many end loads are grouped together in the final graph. 0 means maximal clustering; 1 means all end loads are individual.", width=400)
        ),
        pn.Row(
            seed_input,
            pn.pane.Markdown("An optional integer seed for random number generation to ensure reproducibility of the synthetic data.", width=400)
        ),
        generate_button
    )

    generated_graph_viewer = pn.pane.Plotly(sizing_mode="stretch_width")
    pn.state.cache["generated_graph_viewer"] = generated_graph_viewer

    generated_graph_viewer_3d = pn.pane.Plotly(sizing_mode="stretch_width", height=300)
    pn.state.cache["generated_graph_viewer_3d"] = generated_graph_viewer_3d

    graph_generator_container.append(
        pn.Row(
            inputs_column,
            pn.Column(
                generated_graph_viewer,
                generated_graph_viewer_3d,
                # sizing_mode="stretch_both"
            ),
        )
    )