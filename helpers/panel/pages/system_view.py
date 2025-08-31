import panel as pn
from helpers.panel.button_callbacks import export_graph, reset_graph, run_simulation, update_node_details, update_graph_container_visualization

def layout_system_view(system_view_container, graph_controller, app):
    # upload_file_dropper = pn.widgets.FileDropper(name="Upload Graph", accepted_filetypes=['.mepg', '.graphml'])
    upload_file_dropper = pn.widgets.FileInput(name="Upload Graph")

    visualization_type_dict = {
        "2D Equipment": "2d_type",
        "2D Risk": "2d_risk",
        "3D": "3d"
    }
    graph_container = pn.pane.Plotly(sizing_mode="scale_both")

    radio_visualization_selector = pn.widgets.RadioButtonGroup(
        name="Visualization Type",
        options=["2D Equipment", "2D Risk", "3D"],
        button_type="default"
    )

    # Simple approach: Add a floating legend button using Panel's overlay
    legend_settings_button = pn.widgets.Button(
        name="⚙️",
        button_type="light",
        width=40,
        height=40,
        margin=(5, 5)
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
        orientation="vertical",
        button_type="primary",
        margin=0  # Remove margin around buttons
    )
    
    # Map display names to internal values
    preset_mapping = {
        "Top-Right": "compact_tr",
        "Top-Left": "compact_tl",
        "Bottom-Right": "compact_br",
        "Bottom-Left": "compact_bl",
        "Hidden": "hidden"
    }
    
    # Create a simple popup with just the radio buttons - positioned closer to settings button
    legend_popup = pn.Column(
        legend_preset_radio,
        visible=False,
        width=180,
        height=150,
        margin=0,  # Remove margin
        styles={
            'position': 'fixed',
            'top': '60px',  # Closer to settings button
            'right': '15px',  # Closer to settings button
            'z-index': '1000',
            'background': 'rgba(255,255,255,0.95)',
            'border': '1px solid #ccc',
            'border-radius': '6px',
            'padding': '10px',  # Reduced padding
            'box-shadow': '0 4px 8px rgba(0,0,0,0.2)'
        }
    )

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

    legend_preset_radio.param.watch(update_legend_preset, 'value')
    
    # Button handlers
    def show_legend_modal(event):
        legend_popup.visible = True
    
    def close_legend_modal(event):
        legend_popup.visible = False
    
    legend_settings_button.on_click(show_legend_modal)

    # Add watcher for the radio button group
    radio_visualization_selector.param.watch(
        lambda event: update_graph_container_visualization(event, graph_controller, visualization_type_dict, graph_container), 
        'value'
    )

    header_row = pn.Row(
        pn.pane.Markdown("### System Network View"),
        upload_file_dropper,
        pn.widgets.Button(name="Export Graph", button_type="default", icon="download", on_click=lambda event: export_graph(event, graph_controller, app)),
        pn.widgets.Button(name="Reset", button_type="warning", icon="refresh", on_click=lambda event: reset_graph(event, graph_controller)),
        pn.widgets.Button(name="Run Simulation", button_type="primary", icon="play", on_click=lambda event: run_simulation(event, graph_controller)),
        radio_visualization_selector
    )


    equipment_details_container = pn.Column(
        pn.pane.Markdown("### Equipment Details"),
        pn.pane.Markdown("Click on a node to view its details")
    )

    # Function to handle file upload
    def handle_file_upload(event):
        """Handle file upload from FileDropper"""
        if upload_file_dropper.value is not None and len(upload_file_dropper.value) > 0:
            file_bytes = upload_file_dropper.value
            filename = upload_file_dropper.filename if upload_file_dropper.filename else "uploaded_file.mepg"
            
            from helpers.panel.button_callbacks import upload_graph_from_file
            upload_graph_from_file(file_bytes, filename, graph_controller, graph_container)

    upload_file_dropper.param.watch(handle_file_upload, 'value')

    # Create a simpler approach using Panel's JavaScript callback
    # Add a hidden button that can be triggered from JavaScript
    hidden_trigger_button = pn.widgets.Button(
        name="Hidden Trigger",
        visible=False
    )
    
    def trigger_popup_from_js(event):
        legend_popup.visible = not legend_popup.visible
    
    hidden_trigger_button.on_click(trigger_popup_from_js)

    # Create a real Panel button that works reliably - positioned in legend area
    settings_button = pn.widgets.Button(
        name="⚙️", 
        width=30, 
        height=30,
        button_type="default",
        margin=0  # Remove margin around button
    )
    
    def toggle_legend_popup(event):
        legend_popup.visible = not legend_popup.visible
        
    settings_button.on_click(toggle_legend_popup)

    # Watch for click events
    graph_container.param.watch(lambda event: update_node_details(graph_controller, graph_container, equipment_details_container), 'click_data')

    # Simple approach - put button in the top-right area next to the graph
    system_view_container[0, 0:2 ] = header_row
    system_view_container[1:, 0:2 ] = pn.Column(
        pn.Row(
            graph_container,
            pn.Column(
                settings_button,
                pn.Spacer(),
                width=40,
                margin=0
            ),
            sizing_mode="stretch_width",
            margin=0
        ),
        legend_popup,
        sizing_mode="stretch_both"
    )
    system_view_container[:,   2 ] = equipment_details_container

