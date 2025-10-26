---
title: AssetPulse - Asset Management Simulation
author: Scott C. Lebow, PE and Krisztian Hajdu
date: 15 September 2025
bibliograph: ./references.json
---

# Abstract

# Introduction

# Literature Review

## Related Research

## Existing Tools

# Methodology

## Framework

The AssetPulse framework consists of two main components: a synthetic data generator for creating building electrical system graphs and a remaining useful life (RUL) simulation engine for modeling maintenance and asset management strategies. The synthetic data generator produces detailed graphs representing building electrical systems, including nodes for utility transformers, panels, switchboards, transformers, and end loads, along with their attributes and connections. The RUL simulation engine uses these graphs to simulate maintenance activities, calculate RUL for each piece of equipment, and assess risk levels based on user-defined parameters and maintenance task templates.

The following diagram illustrates the overall architecture and workflow of the AssetPulse simulation tool, including key components such as the user interface, graph controller, simulation engine, and data storage.

![Overall Architecture](images/system_architecture.png)

## User Defined Parameters

The user can specify various parameters to customize the building generation and RUL simulation processes. These parameters include building characteristics, RUL calculation factors, maintenance task templates, repair and replacement task templates, and budget constraints. The following sections detail the required parameters used in the AssetPulse framework.

### Building Electrical System Generation Parameters
| Parameter | Description | Units / Range |
|---|---|---|
| Construction Year | Older buildings allow simulation of more failures and maintenance needs. | Year |
| Total Load | Total electrical load of the building; influences number and type of distribution equipment. | VA |
| Building Length | Length of the building footprint; affects spatial distribution of equipment and number of vertical risers. | m |
| Building Width | Width of the building footprint; affects spatial distribution of equipment and number of vertical risers. | m |
| Number of Floors | Total number of floors; determines vertical distribution and riser lengths. | Integer |
| Floor Height | Height of each floor; influences vertical spacing and riser lengths. | m |
| Cluster Strength | Determines how end loads are grouped in the generated graph (0 = maximally clustered, 1 = all individual). Does not affect distribution equipment generation. | 0–1 |
| Random Seed | Optional integer seed for random number generation to ensure reproducibility of the synthetic data. | Integer (optional) |

### Remaining Useful Life (RUL) Simulation Parameters
| Parameter | Description | Type / Notes |
|---|---|---|
| `TASK_DEFERMENT_FACTOR` | Impact of each deferred maintenance task on remaining useful life (RUL) reduction. Higher values increase the penalty for deferred tasks. | Unitless multiplier |
| `OVERDUE_IMPACT_MULTIPLIER` | Multiplier for how much overdue maintenance affects RUL. Higher values make overdue tasks more detrimental. | Unitless multiplier |
| `AGING_ACCELERATION_FACTOR` | Rate at which aging increases failure probability. Higher values mean equipment ages faster. | Unitless rate |
| `MAX_AGING_MULTIPLIER` | Maximum cap on aging impact to prevent runaway aging effects. | Unitless cap |
| `DEFAULT_LIFESPANS` | Default expected lifespans (years) for different equipment types. | See "Default Lifespans" table |
| `BASE_FAILURE_RATES` | Base annual failure probabilities for different equipment types. | See "Default Base Failure Rates" table |
| `DEFAULT_INITIAL_CONDITION` | Initial condition rating for new equipment (1.0 = perfect). | Float (0–1) |
| `MIN_RUL_RATIO` | Minimum ratio of expected lifespan that RUL can be reduced to (prevents unrealistic low values). | Float (0–1) |
| `CRITICAL_RUL_THRESHOLD_YEARS` | RUL threshold (years) below which equipment is considered CRITICAL risk. | Years |
| `HIGH_RUL_THRESHOLD_YEARS` | RUL threshold (years) below which equipment is considered HIGH risk. | Years |
| `MEDIUM_RUL_THRESHOLD_YEARS` | RUL threshold (years) below which equipment is considered MEDIUM risk. | Years |
| `REPLACEMENT_THRESHOLD_YEARS` | Risk level (RUL in years) at which equipment is flagged for replacement. Set to `None` to disable automatic replacement flagging. | Years or `None` |
| `ENABLE_RUL_WARNINGS` | Enable or disable warnings for critically low RUL during calculations. | Boolean |
| `ENABLE_DEBUG_OUTPUT` | Enable or disable detailed debug output during RUL calculations. | Boolean |
| `TYPES_TO_IGNORE` | Equipment types to exclude from RUL calculations. | List of type names |

#### Default Lifespans

These values are used if the user does not provide custom lifespans.

| Equipment Type       | Default Lifespan (years) |
|----------------------|--------------------------|
| Utility Transformer  | 35                       |
| Transformer          | 30                       |
| Switchboard          | 25                       |
| Panelboard           | 20                       |
| End Load             | 15                       |

#### Default Base Failure Rates

These values are used if the user does not provide custom base failure rates.

| Equipment Type       | Base Failure Rate (annual) |
|----------------------|---------------------------|
| Utility Transformer  | 1.5%                      |
| Transformer          | 2.0%                      |
| Switchboard          | 2.5%                      |
| Panelboard           | 3.0%                      |
| End Load             | 5.0%                      |

### Maintenance Task Templates

Maintenance tasks are defined using a template that specifies the type of task, associated equipment types, frequency, time and money costs, and priority. These template helps standardize maintenance activities across different equipment. The simulation engine uses the uploaded maintenance task template to generate and schedule maintenance tasks for each piece of equipment in the building graph.

When the simulation engine processes maintenance tasks, it generates detailed tasks based on the equipment type and the recommended frequency specified in the template. Each task is linked to a specific equipment node and scheduled accordingly. Tasks are prioritized based on risk score and template priority, with repair and replacement tasks for critical equipment considered before routine maintenance.

For example, a maintenance task template might specify that all "panel" equipment requires a "grounding test" every 12 months with a time cost of 2 hours and a money cost of $150. The simulation engine will create individual grounding test tasks for each panel in the building graph, scheduled based on their installation date and the recommended frequency.

Each month could include a mix of scheduled tasks, executed tasks, and deferred tasks. The scheduled tasks list will show all tasks that were planned for that month, including those that were deferred from previous months. The executed tasks list will show which of those scheduled tasks were actually completed, while the deferred tasks list will indicate which tasks could not be completed due to budget constraints or other factors.

#### Maintenance Task Template Fields

| Task Template Field            | Description                                         |
|-------------------------------|-----------------------------------------------------|
| task_id                       | The unique identifier for the maintenance task. When the tasks for each piece of equipment are generated from the template, this field is concatenated with the equipment ID to ensure uniqueness. |
| equipment_type                | The type of equipment this maintenance task applies to (e.g., "panel", "transformer"). |
| task_type                     | The category of maintenance task (e.g., "inspection", "cleaning", "testing"). Repair and replacement tasks are handled separately using the Repair and Replacement Task Templates. |
| recommended_frequency_months  | The recommended interval (in months) between recurring maintenance tasks. Tasks will be scheduled based on this frequency starting from the equipment installation date. When a task is deferred, the next occurrence will be scheduled based on the deferral date. |
| description                   | A brief explanation of the maintenance task's purpose and activities. This field is optional and can be left blank. |
| default_priority              | The default priority level assigned to the task for scheduling and resource allocation. Lower numbers indicate higher priority. Tasks with the same priority are scheduled based on the node's risk score. |
| time_cost                     | Estimated time required to complete the task (in hours). |
| money_cost                     | Estimated monetary cost to perform the task (in dollars). |
| notes                         | Additional information or special instructions related to the task. This field is optional and can be left blank. |

### Repair and Replacement Task Templates
Repair and replacement tasks are defined using templates that specify the type of task, associated equipment types, time and money costs, and condition thresholds. The simulation engine uses the uploaded repair and replacement task templates to generate and schedule these tasks for equipment flagged for repair or replacement based on RUL and condition.

Repair and replacement tasks are prioritized before routine maintenance tasks and are scheduled when equipment is flagged for repair or replacement due to low RUL or poor condition, subject to budget constraints. These tasks can be deferred if budgets do not allow for immediate action, but they will be tracked until completed.

If multiple pieces of equipment are flagged for repair or replacement in the same month, the simulation engine will prioritize these tasks based on risk level and available budget. This can cause scenarios where for many consecutive months, all available budget is consumed by repair and replacement tasks, leading to deferral of routine maintenance tasks. This behavior reflects real-world scenarios where critical repairs and replacements take precedence over regular upkeep.

#### Repair and Replacement Task Template Fields

| Repair/Replacement Task Template Field | Description                                         |
|---------------------------------------|-----------------------------------------------------|
| task_id                              | The unique identifier for the repair or replacement task. When the tasks for each piece of equipment are generated from the template, this field is concatenated with the equipment ID to ensure uniqueness. |
| equipment_type                       | The type of equipment this repair or replacement task applies to (e.g., "panel", "transformer"). |
| task_name                            | The name of the repair or replacement task (e.g., "replace breaker", "repair transformer"). |
| description                          | A brief explanation of the task's purpose and activities. This field is optional and can be left blank. |
| time_cost                            | Estimated time required to complete the task (in hours). |
| money_cost                           | Estimated monetary cost to perform the task (in dollars). |
| condition_level                      | The condition threshold (0.0 to 1.0) below which the equipment is flagged for this task. For example, a value of 0.3 means the task is triggered when the equipment condition falls below 30%. |
| condition_improvement_amount         | The amount by which the equipment's condition improves after completing the task (e.g., 0.05 means a piece of equipment that is at 0.85 will improve to 0.90). |
| base_expected_lifespan_improvement_percentage | The percentage increase in expected lifespan after completing the task (e.g., 0.10 means a piece of equipment with a baseline expected lifespan of 20 years will increase to 22 years). |
| notes                                | Additional information or special instructions related to the task. This field is optional and can be left blank. |

### Budget Parameters
The simulation engine allows users to define monthly budgets for maintenance tasks, including time and money constraints. These budgets influence which tasks can be executed each month, with higher-priority tasks being scheduled first. Users can also enable budget rollover, allowing unused budget from one month to carry over to the next.

We see these as the key parameters for getting useful simulation results.  In the real world, budgets may vary month to month, and our simulation engine and analysis tools can allow operators to explore the impact of different budget scenarios on asset management outcomes.  

The budget parameters are:

| Parameter | Description | Units / Range |
|---|---|---|
| Monthly Budget (Hours) | Set the monthly hour budget for maintenance tasks. This limits how many maintenance activities can be performed each month. | Hours |
| Monthly Budget (Dollars) | Set the monthly dollar budget for maintenance tasks. This limits the total cost of maintenance activities each month. | Dollars |
| Enable Budget Rollover | Allow unused budget from one month to carry over to the next, providing flexibility in scheduling. | Boolean |
| Weeks to Schedule Ahead | Set how many weeks past the current date the maintenance scheduler should plan tasks. | Weeks |

## Building Electrical System Generation Logic
The generator uses the user-specified building parameters to compute derived attributes like total area.

It calculates the number of vertical risers as one riser per 500 square meters of floor area, rounding up to ensure adequate distribution.  This is a simplification; in practice, riser count may depend on building codes and design practices.  Risers are located within the footprint, spaced along the longer dimension and centered along the shorter dimension, with some randomness to avoid perfectly regular placement.

The system voltage level is chosen based on total electrical load and step-down transformers are included where high-voltage distribution requires them, using standard three‑phase voltage levels (e.g., 480Y/277V or 208Y/120V). 

Total load is allocated across floors with random variation (±10%) and end loads (lighting, receptacles, HVAC, etc.) are assigned to floors and located at the nearest riser; each end load receives a type, power rating, and voltage level consistent with the building system. 

For each riser on each floor the generator summarizes total power per end load type and voltage to support sizing of distribution equipment and to understand load distribution. 

Distribution equipment (main panels, sub‑panels, transformers) is placed for each riser and floor according to end loads and voltage requirements, including step‑down transformers and multiple panels as needed, and the graph is built by connecting utility transformers to main panels, main panels to risers, risers to distribution equipment, and distribution equipment to end loads. 

Finally, helper modules assign risk scores and remaining useful life (RUL) values to each node, a summary report of the generated building is produced (total load, equipment counts, end load breakdown, per‑floor/riser details), and the graph is saved in GraphML for further analysis.

## Remaining Useful Life (RUL) Simulation Logic

### Risk Assessment

Before calculating RUL, the simulation engine assesses the risk level of failure for each piece of equipment based on its graph attributes.  This assessment uses the load seen at each node and the quantity of total downstream equipment nodes in the graph to determine a risk score.  Equipment with higher loads and more downstream dependencies will have higher risk scores, indicating that their failure would have a more significant impact on the overall system performance.

We use the following formula to calculate the risk score for each piece of equipment:

```
propagated_power = graph.nodes[node].get('propagated_power', 0) or 0
norm_power = propagated_power / total_load if total_load else 0
descendants_count = filtered_descendants_count(graph, node)
norm_descendants = descendants_count / max_descendants
risk = (norm_power + norm_descendants) / 2
```

The filtered_descendants_count function counts the number of downstream equipment nodes, excluding end loads, to focus on critical distribution components. The risk score is then normalized between 0 and 1, with higher values indicating greater risk.

### Remaining Useful Life (RUL) Simulation
Once the user sets the RUL simulation parameters, the simulation engine uses these values to calculate the Remaining Useful Life (RUL) for each piece of equipment in the building graph over each month of the simulation period. The process begins with task generation, where maintenance tasks are generated from the building graph and generic/replacement task templates, with each task linked to a specific equipment node and scheduled based on installation date and recommended frequency.

The simulation engine then initializes RUL parameters by loading user-defined values, including equipment lifespans, failure rates, aging factors, maintenance impact factors, and risk thresholds. During the simulation period, the engine iterates over each month, updating the current date and recalculating RUL for all equipment nodes in the graph.

For each equipment node, the engine calculates RUL by determining its installation date, expected lifespan, and operating history. It computes the baseline RUL as the difference between expected lifespan and operating time, then adjusts RUL for deferred maintenance tasks using the task deferment factor and overdue impact multiplier. The engine applies aging acceleration and caps aging impact using the aging acceleration factor and maximum aging multiplier, adjusts RUL based on current equipment condition while ensuring a minimum condition factor is applied, and ensures RUL does not fall below a minimum ratio of expected lifespan.

The simulation assesses risk level and failure probability for each node by calculating annual failure probability using base failure rates, aging factor, and condition. It assigns a risk level (LOW, MEDIUM, HIGH, CRITICAL) based on RUL thresholds and condition, and flags equipment for replacement if the risk level meets the replacement threshold. The calculated RUL (in days and years), risk level, failure probability, and condition history are stored in each node's attributes, with optional warnings for critically low RUL or high failure risk if enabled.

Maintenance task scheduling and execution occurs monthly, where the simulation engine generates a prioritized schedule of maintenance tasks for equipment nodes using generic and replacement task templates. Tasks are scheduled based on recommended frequency, equipment installation date, and current risk level, with each task including time and money cost estimates, priority, and status. Monthly budgets for time and money are enforced, with tasks exceeding the budget deferred to future months, and unused budget carrying forward if rollover is enabled.

The system can generate synthetic maintenance logs for each node to simulate observed condition changes, using randomized condition values and log entries that include a date, condition rating (0.0–1.0), and description. These synthetic logs use a random seed for reproducibility and employ a beta distribution to model realistic condition changes using the formula `new_condition = round(random.betavariate(alpha=5, beta=1) * current_condition, 1)`. The beta distribution function, with alpha=5 and beta=1, skews the distribution towards higher condition values, simulating realistic maintenance outcomes as shown in the figure below.

![Beta Distribution](images/beta_distribution.png)

Replacement tasks are triggered for equipment with low condition or high risk and are prioritized before routine tasks. For each executed task, the equipment node's condition is improved and the maintenance history is updated, while deferred tasks increase the deferred count, impacting future RUL calculations.

Finally, the simulation provides comprehensive reporting and analysis capabilities. After each month, the engine records the scheduled, executed, and deferred tasks, maintenance logs, and replacement actions. The updated graph state, including RUL, condition, and risk, is saved for each month to enable time-series analysis. System-wide summaries include total tasks scheduled, executed, deferred, and replaced, as well as budget utilization and risk distribution, while detailed component-level metrics and maintenance histories are available for further analysis and visualization.

## Simulation Output
The simulation engine outputs each month's RUL and risk assessment results in a dictionary format, with keys representing the month (e.g., "2023-01"). Each monthly record provides a comprehensive snapshot of the system's maintenance activities, budget utilization, and equipment status. The output includes scheduled tasks for the month, which encompasses all planned activities regardless of their execution status, including tasks deferred from previous months that require continued tracking until completion. Budget information captures both the monthly allocation and any rollover amounts from previous periods when budget rollover is enabled, providing visibility into resource availability and utilization patterns. The system maintains the complete building graph in NetworkX format, reflecting all changes made during the month including executed maintenance tasks, condition updates, and equipment replacements, enabling detailed time-series analysis and visualization capabilities.

| Output Component | Description |
|---|---|
| Month identifier | Month key in format "YYYY-MM" (e.g., "2023-01") |
| tasks_scheduled | Complete list of all tasks planned for the month, including deferred tasks from previous months |
| rollover_time_budget | Unused time budget carried forward from the previous month (if rollover enabled) |
| rollover_money_budget | Unused money budget carried forward from the previous month (if rollover enabled) |
| time_budget | Monthly time budget allocation added to rollover amount for total available hours |
| money_budget | Monthly money budget allocation added to rollover amount for total available funds |
| graph | Updated NetworkX building graph with current RUL, risk levels, conditions, and structural information |
| executed_tasks | Tasks successfully completed during the month with details on type, equipment, costs, and status |
| deferred_tasks | Tasks postponed during the month including deferral reasons and scheduling impacts |
| maintenance_logs | Synthetic maintenance activity records for inspections, repairs, and replacements (if enabled) |
| replacement_tasks_executed | Completed equipment replacement tasks with component and cost details |
| replacement_tasks_not_executed | Planned replacement tasks that were not completed with reasons for non-execution |

# Results

## Simulation Outputs



## Optimization

Using the simulation engine, we can optimize maintenance scheduling and budget allocation strategies for building electrical systems. As a proof of concept, we built a multi-variable goal seeking optimization model using the RUL simulation engine to adjust monthly time and money budgets to minimize total deferred maintenance tasks over a one-year simulation period.  In many scenarios, we found that increasing the monthly budgets reduced deferred tasks, however in some cases lower budgets resulted in fewer deferred tasks because equipment failures triggered necessary repairs and replacements that improved overall system condition and reduced future maintenance needs.

We ran multiple simulations across various generated building electrical systems, adjusting monthly time and money budgets to observe their impact on deferred maintenance tasks. However, without tuning the simulation parameters and maintenance task templates to reflect real-world practices, the results may not accurately represent actual maintenance outcomes.  Future work will involve calibrating the simulation engine with real-world data to enhance its predictive capabilities.

# Discussion

## User Input

In reality maintenance and replacement tasks would be determined by the specific equipment and manufacturer recommendations.  For the purposes of this simulation, we use generic maintenance, repair/replacement tasks that apply to broad equipment categories.  Users can customize both maintenance and repair/replacement task templates to better reflect their specific asset management practices.

Increased simulation accuracy may even require more granular equipment types in the graph to ensure that the correct tasks are applied.  For example, if a user wants to differentiate between different sizes or models of transformers, they may need to create separate equipment types in the graph (e.g., "transformer_small", "transformer_large") and define corresponding tasks for each type.  This allows for more precise control over maintenance and repair/replacement strategies based on the specific characteristics of the equipment.  

We see this as an area for future improvement, where future researchers can explore more detailed equipment classifications and their impact on asset management strategies, based on real-world data and practices.

## Building Generation

Because the synthetic data generator produces a complete building electrical system graph with detailed attributes, it can be used to test and validate the RUL simulation and maintenance scheduling features of AssetPulse.  The generated graph includes all necessary node types, connections, and attributes required for the RUL simulation engine to function effectively.

The generated electrical system logic first distributes loads through an approximation of a building, then sizes and places distribution equipment based on the load requirements and building layout and assigns the loads to the appropriate distribution equipment.  Finally, it connects all nodes in a logical hierarchy from utility transformer to end load.

This allows us to determine the electrical load (amperage and power) at each node, which is later used for assessing the risk score for each piece of equipment.  When calculating the remaining useful life (RUL) during the simulation, the risk score is used to prioritize maintenance tasks and influence failure probabilities.

This allows us to determine which equipment should be maintained in situations where budget constraints prevent all maintenance from being performed.  Equipment with higher risk scores, such as main panels and switchboards, will be prioritized for maintenance tasks, while lower-risk equipment may have tasks deferred.

Should the lower risk equipment fail due to deferred maintenance, the resulting failure event should affect less of the overall system performance, as the higher risk equipment will have been maintained and is less likely to fail.

### Other System Graphs
The synthetic data generator can be adapted to create other types of system graphs beyond building electrical systems. For example, with modification it could generate water distribution networks, HVAC systems, or transportation infrastructure graphs by modifying the node types, connections, and attributes according to the specific domain requirements. This flexibility allows AssetPulse to be applied to a wide range of asset management scenarios across different industries.

The key parameters used in the remaining useful life (RUL) simulation are described in the next section.  To apply the RUL simulation to a different type of system graph, the user would need to define appropriate equipment types, lifespans, failure rates, and maintenance tasks relevant to that domain, however the core simulation logic would remain the same.

For example, in a water distribution network, equipment types might include pumps, valves, and pipes, each with their own lifespans and failure modes. Maintenance tasks could involve inspections, cleaning, and replacements specific to water systems. By adjusting these parameters and templates, the RUL simulation can be effectively applied to various asset management contexts.

One would also need to ensure that the graph nodes include load information to determine risk scores, or alternatively develop a different method for assessing risk based on the specific attributes of the equipment in that domain.

The required node attributes for the RUL simulation are:

| Attribute Name       | Description               |
|----------------------|---------------------------|
| type                 | Type of equipment (e.g., "transformer", "panel", "switchboard", "end load") |
| installation_date    | Date when the equipment was installed (format: "YYYY-MM-DD") |
| expected_lifespan    | Expected lifespan of the equipment in years (optional; if not provided, defaults will be used based on type) |
| replacement_cost     | Cost to replace the equipment, allows for varying costs based on unique instances of an equipment type.  For example, a larger transformer may cost more to replace than a smaller one of the same type. |
| current_condition    | Current condition of the equipment, on a scale from 0.0 (failed) to 1.0 (new). If not provided, defaults to 1.0. |

# Conclusion

The synthetic data generator and the RUL simulation provide a framework for testing and validating asset management strategies in complex systems. By accurately modeling the relationships and attributes of various equipment types, AssetPulse can help organizations optimize their maintenance schedules, reduce costs, and improve overall system reliability.

Future work will focus on refining the simulation parameters, incorporating real-world data for calibration, and expanding the framework to accommodate additional types of infrastructure systems.  We also plan to enhance data export capabilities to allow integration with BIM and asset management software for practical applications.

# References

::: {#refs}
:::
