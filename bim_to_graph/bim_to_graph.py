# This is a Revit Dynamo script to convert the Electrical Equipment elements in a BIM model to a graph representation.

import os
import sys
import clr
import datetime

clr.AddReference('ProtoGeometry')
from Autodesk.DesignScript.Geometry import *

clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Electrical import *

clr.AddReference('RevitServices')
import RevitServices
from RevitServices.Persistence import DocumentManager

def get_equipment_id_from_name(equipment_list, name):
    for eq in equipment_list:
        if eq.LookupParameter("Panel Name") is None:
            continue
        eq_name = eq.LookupParameter("Panel Name").AsString()
        if eq_name == name:
            return eq.Id.Value
    return None

output_directory = IN[0]  # Input from Dynamo: directory to save the output file

print("\n" * 10)

current_revit_year = int(DocumentManager.Instance.CurrentDBDocument.Application.VersionNumber)
print(f"Current Revit Year: {current_revit_year}")

# Get all electrical equipment in the model
doc = DocumentManager.Instance.CurrentDBDocument
collector = FilteredElementCollector(doc)
electrical_equipment = collector.OfCategory(BuiltInCategory.OST_ElectricalEquipment).WhereElementIsNotElementType().ToElements()

print("Number of electrical equipment elements found: {}".format(len(electrical_equipment)))

# Get Project Information 
project_info = doc.ProjectInformation
project_name = project_info.Name
project_number = project_info.Number
issue_date = project_info.IssueDate

# Format issue date to YYYY-MM-DD
if issue_date:
    try:
        issue_date_dt = datetime.datetime.strptime(issue_date, "%m/%d/%Y")
        issue_date = issue_date_dt.strftime("%Y-%m-%d")
    except Exception:
        # If parsing fails, keep the original string
        pass

print(f"Project Name: {project_name}, Project Number: {project_number}, Issue Date: {issue_date}")

# Create a directed graph
nodes = {}
edges = {}

ALLOWABLE_NODE_TYPES = ["Panelboard", "Switchboard"]
OUTPUT_ALL_NODE_PARAMS = False  # Set to True to output all parameters of nodes

# Add nodes for each electrical equipment element
for eq in electrical_equipment:
    symbol = doc.GetElement(eq.GetTypeId())

    try:
        part_type = symbol.LookupParameter("Part Type").AsValueString()
    except:
        part_type = symbol.Family.LookupParameter("Part Type").AsValueString()

    print(f"Processing equipment ID {eq.Id.Value} of type {part_type}")

    if part_type not in ALLOWABLE_NODE_TYPES:
        print(f"Skipping equipment ID {eq.Id.Value} of type {part_type}")
        continue

    # Check for required parameters
    if eq.LookupParameter("Panel Name") is None or eq.LookupParameter("Supply From") is None:
        print(f"Skipping equipment ID {eq.Id.Value} due to missing required parameters")
        continue

    # Check if "Panel Name" is empty or "Supply From" is empty
    panel_name = eq.LookupParameter("Panel Name").AsString()

    if not panel_name:
        print(f"Skipping equipment ID {eq.Id.Value} due to empty required parameters")
        continue

    node_dict = {}

    if part_type == "Panelboard":
        node_type = "Panelboard"
        name = eq.LookupParameter("Panel Name").AsString()
        supply_from_name = eq.LookupParameter("Supply From").AsString()
        supply_from_id = get_equipment_id_from_name(electrical_equipment, supply_from_name)
        node_dict = {
            "type": node_type,
            "name": name,
            "supply_from_name": supply_from_name,
            "supply_from_id": supply_from_id
        }

    elif part_type == "Switchboard":
        node_type = "Switchboard"
        name = eq.LookupParameter("Panel Name").AsString()
        supply_from_name = eq.LookupParameter("Supply From").AsString()
        supply_from_id = get_equipment_id_from_name(electrical_equipment, supply_from_name)
        node_dict = {
            "type": node_type,
            "name": name,
            "supply_from_name": supply_from_name,
            "supply_from_id": supply_from_id
        }

    installation_date = issue_date  # Using project issue date as installation date
    node_dict["installation_date"] = installation_date

    if OUTPUT_ALL_NODE_PARAMS:
        for param in eq.Parameters:
            try:
                param_name = param.Definition.Name
                if param.StorageType == StorageType.String:
                    param_value = param.AsString()
                elif param.StorageType == StorageType.Double:
                    param_value = param.AsDouble()
                elif param.StorageType == StorageType.Integer:
                    param_value = param.AsInteger()
                elif param.StorageType == StorageType.ElementId:
                    param_value = str(param.AsElementId().IntegerValue)
                else:
                    param_value = None
                node_dict[param_name] = param_value
            except Exception as e:
                print(f"Error retrieving parameter {param.Definition.Name} for equipment ID {eq.Id.Value}: {e}")

    nodes[eq.Id.Value] = node_dict
    print(f"Added node: {node_dict}")

print(f"Nodes created: {len(nodes)}")

# Add edges based on supply relationships
for node_id, node_data in nodes.items():
    supply_from_id = node_data["supply_from_id"]
    if supply_from_id and supply_from_id in nodes:
        edges.setdefault(supply_from_id, []).append(node_id)
        node_name = node_data["name"]
        supply_from_name = nodes[supply_from_id]["name"]
        print(f"Creating edge from {supply_from_name} (ID: {supply_from_id}) to {node_name} (ID: {node_id})")

print(f"Edges created: {sum(len(v) for v in edges.values())}")

# Output the graph in GraphML format
graphml_header = """<?xml version='1.0' encoding='utf-8'?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">
"""
graphml_footer = "</graphml>"

node_key_defs = []
edge_key_defs = []

# Define keys for node attributes
node_attributes = set()
for node_id, node_data in nodes.items():
    for attr in node_data.keys():
        node_attributes.add(attr)

# Define keys for edge attributes
edge_attributes = set()
for source, targets in edges.items():
    for target in targets:
        edge_attributes.add("source")
        edge_attributes.add("target")

for attr in node_attributes:
    node_key_defs.append(f'<key id="d{len(node_key_defs)+1}" for="node" attr.name="{attr}" attr.type="string"/>')

for attr in edge_attributes:
    edge_key_defs.append(f'<key id="d{len(edge_key_defs)+1 + len(node_key_defs)}" for="edge" attr.name="{attr}" attr.type="string"/>')

graphml_content = graphml_header + "\n".join(node_key_defs) + "\n".join(edge_key_defs) + '<graph id="G" edgedefault="directed">\n'

# Add nodes to graphml
for node_id, node_data in nodes.items():
    graphml_content += f'  <node id="n{node_id}">\n'
    for attr, value in node_data.items():
        graphml_content += f'    <data key="d{list(node_attributes).index(attr)+1}">{value}</data>\n'
    graphml_content += '  </node>\n'

# Add edges to graphml
for source, targets in edges.items():
    for target in targets:
        graphml_content += f'  <edge source="n{source}" target="n{target}">\n'
        graphml_content += f'    <data key="d{len(node_attributes)+1}">Edge from {source} to {target}</data>\n'
        graphml_content += '  </edge>\n'
graphml_content += '</graph>\n' + graphml_footer
print("GraphML content generated.")

# Save to file (optional)
SAVE_TO_FILE = True

if SAVE_TO_FILE:
    output_path = os.path.join(output_directory, "output_graph.graphml")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(graphml_content)
    print(f"GraphML file saved to {output_path}")

OUT = graphml_content