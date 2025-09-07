import panel as pn
from helpers.panel.button_callbacks import upload_graph_from_file, export_graph, reset_graph, run_simulation, update_node_details, update_graph_container_visualization

def layout_system_view(system_view_container, graph_controller):
    graph_container = pn.pane.Plotly(sizing_mode="scale_both")
    pn.state.cache["graph_container"] = graph_container
    # upload_file_dropper = pn.widgets.FileDropper(name="Upload Graph", accepted_filetypes=['.mepg', '.graphml'])
    upload_file_dropper = pn.widgets.FileInput(name="Upload Graph")
    upload_file_dropper.param.watch(lambda event: upload_graph_from_file(event.new, upload_file_dropper.filename, graph_controller), 'value')

    # # Upload a default file
    # default_file_path = "example_graph.mepg"
    # default_file = open(default_file_path, "rb").read()
    # upload_file_dropper.value = default_file

    visualization_type_dict = {
        "2D Equipment": "2d_type",
        "2D Risk": "2d_risk",
        "3D": "3d"
    }

    radio_visualization_selector = pn.widgets.RadioButtonGroup(
        name="Visualization Type",
        options=["2D Equipment", "2D Risk", "3D"],
        button_type="default"
    )

    legend_preset_radio = pn.widgets.RadioButtonGroup(
        name="Choose Legend Style:",
        options=[
            "Top-Right",
            "Top-Left",
            "Bottom-Right",
            "Bottom-Left",
            "Hidden"
        ],
        value="Top-Right",
        orientation="horizontal",
        button_type="default",
    )
    
    # Map display names to internal values
    preset_mapping = {
        "Top-Right": "compact_tr",
        "Top-Left": "compact_tl",
        "Bottom-Right": "compact_br",
        "Bottom-Left": "compact_bl",
        "Hidden": "hidden"
    }

    # Add watcher for legend preset changes
    def update_legend_preset(event):
        """Update legend preset and refresh visualization"""
        internal_value = preset_mapping[event.new]
        graph_controller.legend_preset = internal_value
        # Trigger visualization update
        current_viz_type = radio_visualization_selector.value
        if current_viz_type:
            update_graph_container_visualization(
                type('MockEvent', (), {'new': current_viz_type})(), 
                graph_controller, 
                visualization_type_dict, 
                graph_container
            )

    legend_preset_radio.param.watch(lambda event: update_legend_preset(event), 'value')
    
    # Add watcher for the radio button group
    radio_visualization_selector.param.watch(
        lambda event: update_graph_container_visualization(event, graph_controller, visualization_type_dict, graph_container), 
        'value'
    )

    header_row = pn.Column(
        pn.Row(
            pn.pane.Markdown("### System Network View"),
            upload_file_dropper,
            pn.widgets.Button(name="Export Graph", button_type="default", icon="download", on_click=lambda event: export_graph(event, graph_controller)),
            pn.widgets.Button(name="Reset", button_type="warning", icon="refresh", on_click=lambda event: reset_graph(event, graph_controller)),
            pn.widgets.Button(name="Run Simulation", button_type="primary", icon="play", on_click=lambda event: run_simulation(event, graph_controller)),
            radio_visualization_selector,
        ),
        pn.Row(
            pn.pane.Markdown("### Legend Settings: "),
            legend_preset_radio
        )
    )

    equipment_details_container = pn.Column(
        pn.pane.Markdown("### Equipment Details"),
        pn.pane.Markdown("Click on a node to view its details")
    )

    # Watch for click events
    graph_container.param.watch(lambda event: update_node_details(graph_controller, graph_container, equipment_details_container), 'click_data')

    # Simple approach - put button in the top-right area next to the graph
    system_view_container[0, 0:2 ] = header_row
    system_view_container[1:, 0:2 ] = pn.Column(
        pn.Row(
            graph_container,
            pn.Column(
                pn.Spacer(),
                width=40,
                margin=0
            ),
            sizing_mode="stretch_width",
            margin=0
        ),
        sizing_mode="stretch_both"
    )
    system_view_container[:,   2 ] = equipment_details_container

