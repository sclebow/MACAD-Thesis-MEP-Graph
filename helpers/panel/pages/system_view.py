import panel as pn
from helpers.panel.button_callbacks import export_graph, reset_graph, run_simulation

def layout_system_view(system_view_container, graph_controller, app):
    # upload_file_dropper = pn.widgets.FileDropper(name="Upload Graph", accepted_filetypes=['.mepg', '.graphml'])
    upload_file_dropper = pn.widgets.FileInput(name="Upload Graph")

    header_row = pn.Row(
        pn.pane.Markdown("### System Network View"),
        upload_file_dropper,
        pn.widgets.Button(name="Export Graph", button_type="default", icon="download", on_click=lambda event: export_graph(event, graph_controller, app)),
        pn.widgets.Button(name="Reset", button_type="warning", icon="refresh", on_click=lambda event: reset_graph(event, graph_controller)),
        pn.widgets.Button(name="Run Simulation", button_type="primary", icon="play", on_click=lambda event: run_simulation(event, graph_controller)),
    )

    graph_container = pn.pane.Plotly(sizing_mode="scale_both")

    # Function to handle file upload (defined after graph_container is created)
    def handle_file_upload(event):
        """Handle file upload from FileDropper"""
        if upload_file_dropper.value is not None and len(upload_file_dropper.value) > 0:
            # Get the first uploaded file
            file_bytes = upload_file_dropper.value
            filename = upload_file_dropper.filename if upload_file_dropper.filename else "uploaded_file.mepg"
            
            # Call the upload function
            from helpers.panel.button_callbacks import upload_graph_from_file
            upload_graph_from_file(file_bytes, filename, graph_controller, graph_container)

    # Watch for file uploads
    upload_file_dropper.param.watch(handle_file_upload, 'value')

    equipment_details_container = pn.Column(
        pn.pane.Markdown("### Equipment Details"),
    )

    system_view_container[0, 0:2 ] = header_row
    system_view_container[1:, 0:2 ] = graph_container
    system_view_container[:,   2 ] = equipment_details_container

