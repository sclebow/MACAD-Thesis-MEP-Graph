# AssetWise - Project Paper

## Abstract
AssetWise is an advanced asset management simulation tool and synthetic data generator designed to optimize resource allocation, improve decision-making, and facilitate research through realistic scenario modeling. Building on a graph-based approach, AssetWise models asset lifecycles, calculates remaining useful life (RUL), and applies business rules for budget planning, risk management, and both reactive and preventive maintenance. The system aggregates risk, cost, and downtime metrics, supports automated scheduling, and visualizes results through an interactive interface. By enabling robust scenario analysis and comprehensive planning, AssetWise helps users optimize maintenance strategies and resource allocation for complex building systems and infrastructure networks. This paper discusses the objectives, research questions, methodology, and future work related to the project.

## Introduction
### Problem
Effective management of physical assets is critical for operational efficiency and cost control across industries. However, many organizations face challenges in modeling asset lifecycles, predicting maintenance needs, and allocating resources optimally due to a lack of data-driven decision-assistance tools.

AssetWise aims to address these challenges by providing a simulation environment that allows users to model asset behaviors, evaluate different budget strategies, and make informed decisions based on simulated outcomes.

### Objectives
1. Develop a graph-based simulation tool that models asset management scenarios, including asset lifecycles, maintenance schedules, and budget allocations.
2. Create a synthetic data generator to produce realistic datasets for testing and validating asset management strategies.
3. Enable users to visualize and analyze the impact of different asset management decisions through interactive dashboards and reports.
4. Compare the effectiveness of various budget allocation strategies in asset management through simulation experiments.
5. Optimize budget allocation strategies based on different metrics such as maximizing asset longevity, maximizing equipment condition, and minimizing monthly costs.

## Research Questions
1. How can graph-based methods support the tracking of changes and lifecycle management of building systems?
2. How can synthetic data generation be utilized to create realistic asset management scenarios for testing and validation?
3. What are the comparative advantages of different budget allocation strategies in asset management?
4. How can simulation tools be designed to facilitate user interaction and decision-making in asset management?

## Methodology
### Simulation Tool Development
- Graph-Based Modeling
    -  Utilize graph structures to represent assets, their relationships, and lifecycle
- Simulation Engine
    -  Implement a simulation engine that allows users to define scenarios, allocate budgets, and simulate asset behaviors over time.
- User Interface
    -  Design an intuitive user interface for scenario setup, simulation execution, and result visualization.
- Synthetic Data Generator
    -  Develop a module to create realistic synthetic datasets that mimic asset characteristics, failure modes, and maintenance histories for testing and validation purposes.
- Validation and Evaluation
    -  Conduct experiments to validate the simulation accuracy and evaluate the impact of different budget allocation strategies using the synthetic data.

## Synthetic Data Generation
To quickly generate realistic building data for testing and validation, we developed a synthetic data generator. This tool creates building electrical system graphs based on the following user-defined parameters:

### User-Defined Parameters
- Construction Year
  - Older buildings will allow the simulation of more failures and maintenance needs.
- Total Load (kW)
  - The total electrical load of the building, influencing the number and type of distribution equipment.
- Building Length (m)
  - The length of the building footprint, affecting spatial distribution of equipment and the number of vertical risers.
- Building Width (m)
  - The width of the building footprint, affecting spatial distribution of equipment and the number of vertical risers.
- Number of Floors
  - The total number of floors, determining vertical distribution and riser lengths.
- Floor Height (m)
  - The height of each floor, influencing vertical spacing and riser lengths.
- Cluster Strength (m)
  - This parameter determines how many end loads are grouped together in the final generated graph.  It does not affect the distribution equipment generation.  A value of 0 means that all end loads will be maximally clustered, while a value of 1 means that all end loads will be individually included.
- Random Seed
  - An optional integer seed for random number generation to ensure reproducibility of the synthetic data.

### Simulation Logic
The synthetic data generator uses the provided parameters to create a building electrical system graph. The process involves:

1. Define Building Characteristics 
   - Validate and record user-specified parameters such as total electrical load, building dimensions, number of floors, and floor height. Calculate derived attributes like total area.

2. Determine Number of Vertical Risers
    -  Calculate the number of risers required for efficient electrical distribution, based on building area and a rule of thumb (e.g., one riser per 500 square meters per floor).

3. Locate Risers
    -  Place risers within the building footprint, spaced along the longer dimension and centered along the shorter dimension, with some randomness to avoid perfect regularity.

4. Determine Building Voltage Level
    -  Select the appropriate voltage system (e.g., 120/208V or 277/480V) based on the total electrical load. If high voltage is required, include step-down transformers for distribution.

5. Distribute Loads Across Floors
    -  Allocate the total electrical load across all floors, introducing random variation (±10") to simulate realistic load distribution. Assign end loads (lighting, receptacles, HVAC, etc.) to each floor, ensuring the sum matches the total load.

6. Assign End Loads to Risers
    -  For each end load, determine its location and assign it to the nearest riser. Each end load is given a type, power rating, and voltage level based on building system.

7. Determine Riser Attributes on Each Floor
    -  For each riser on each floor, summarize the total power per end load type and voltage. This helps in sizing distribution equipment and understanding load distribution.

8. Place Distribution Equipment
    -  For each riser and floor, place distribution equipment (main panels, sub-panels, transformers) according to the end loads and voltage requirements. Include step-down transformers and multiple distribution panels as needed.

9.  Connect Nodes
    -  Build the graph by connecting utility transformers to main panels, main panels to risers, risers to distribution equipment, and distribution equipment to end loads. Ensure logical hierarchy and connectivity.

10. Apply Risk and Remaining Useful Life (RUL) Scores
    -  Use helper modules to assign risk scores and RUL values to each node in the graph, simulating equipment aging and maintenance needs.

11. Reporting and Output
    -  Print a summary report of the generated building, including total load, equipment counts, end load breakdown, and per-floor/riser details. Save the graph in GraphML format for further analysis or visualization.

## RUL Simulation Parameters
Once the synthetic building data is generated, users can simulate the Remaining Useful Life (RUL) of equipment based on various parameters. These parameters allow users to customize how maintenance deferrals, aging, and equipment types affect RUL calculations.

### User-Defined Parameters
- TASK_DEFERMENT_FACTOR
  - Impact of each deferred maintenance task on RUL reduction. Higher values increase the penalty for deferred tasks.
- OVERDUE_IMPACT_MULTIPLIER
  - Multiplier for how much overdue maintenance affects RUL. Higher values make overdue tasks more detrimental.
- AGING_ACCELERATION_FACTOR
  - Rate at which aging increases failure probability. Higher values mean equipment ages faster.
- MAX_AGING_MULTIPLIER
  - Maximum cap on aging impact. Prevents runaway aging effects.
- DEFAULT_LIFESPANS
  - Default expected lifespans (in years) for different equipment types.
- BASE_FAILURE_RATES
  - Base annual failure probabilities for different equipment types.
- DEFAULT_INITIAL_CONDITION
  - Initial condition rating for new equipment (1.0 = perfect).
- MIN_RUL_RATIO
  - Minimum ratio of expected lifespan that RUL can be reduced to prevent unrealistic low values.
- CRITICAL_RUL_THRESHOLD_YEARS
  - RUL threshold (in years) below which equipment is considered CRITICAL risk.
- HIGH_RUL_THRESHOLD_YEARS
  - RUL threshold (in years) below which equipment is considered HIGH risk.
- MEDIUM_RUL_THRESHOLD_YEARS
  - RUL threshold (in years) below which equipment is considered MEDIUM risk.
- REPLACEMENT_THRESHOLD_YEARS
  - Risk level at which equipment is flagged for replacement. Set to None to disable.
- ENABLE_RUL_WARNINGS
  - Enable or disable warnings for critically low RUL during calculations.
- ENABLE_DEBUG_OUTPUT
  - Enable or disable detailed debug output during RUL calculations.
- TYPES_TO_IGNORE
  - Equipment types to exclude from RUL calculations.

#### Default Lifespans
| Equipment Type       | Default Lifespan (years) |
|----------------------|--------------------------|
| Utility Transformer  | 35                       |
| Transformer          | 30                       |
| Switchboard          | 25                       |
| Panelboard           | 20                       |
| End Load             | 15                       |

#### Default Base Failure Rates

| Equipment Type       | Base Failure Rate (annual) |
|----------------------|---------------------------|
| Utility Transformer  | 1.5%                      |
| Transformer          | 2.0%                      |
| Switchboard          | 2.5%                      |
| Panelboard           | 3.0%                      |
| End Load             | 5.0%                      |

#### Maintenance Task Templates

#### Replacement Task Templates

### Simulation Logic

Once the user sets the RUL simulation parameters, the simulation engine uses these values to calculate the Remaining Useful Life (RUL) for each piece of equipment in the building graph over each month of the simulation period. The process involves:

1. Initialize RUL Parameters
   - The simulation engine loads user-defined RUL parameters, including equipment lifespans, failure rates, aging factors, maintenance impact factors, and risk thresholds.

2. Iterate Over Simulation Period
    - For each month in the simulation period, the engine updates the current date and recalculates RUL for all equipment nodes in the graph.

3. Calculate RUL for Each Node
   - For each equipment node, determine its installation date, expected lifespan, and operating history.
   - Compute the baseline RUL as the difference between expected lifespan and operating time.
   - Adjust RUL for deferred maintenance tasks using the task deferment factor and overdue impact multiplier.
   - Apply aging acceleration and cap aging impact using the aging acceleration factor and maximum aging multiplier.
   - Adjust RUL based on current equipment condition, ensuring a minimum condition factor is applied.
   - Ensure RUL does not fall below a minimum ratio of expected lifespan.

4. Assess Risk Level and Failure Probability
   - For each node, calculate annual failure probability using base failure rates, aging factor, and condition.
   - Assign a risk level (LOW, MEDIUM, HIGH, CRITICAL) based on RUL thresholds and condition.
   - Flag equipment for replacement if risk level meets the replacement threshold.

5. Update Graph Attributes
   - Store calculated RUL (in days and years), risk level, failure probability, and condition history in each node's attributes.
   - Optionally, print warnings for critically low RUL or high failure risk if enabled.


6. Maintenance Task Scheduling and Execution
   - For each month, the simulation engine generates a prioritized schedule of maintenance tasks for equipment nodes, using generic and replacement task templates.
   - Tasks are scheduled based on recommended frequency, equipment installation date, and current risk level.
   - Each task includes time and money cost estimates, priority, and status (pending, in progress, complete).
   - Monthly budgets for time and money are enforced; tasks exceeding the budget are deferred to future months. If budget rollover is enabled, unused budget carries forward.
   - Synthetic maintenance logs can be generated for each node to simulate observed condition changes, using randomized condition values and log entries.
     - Synthetic logs include a date, condition rating (0.0–1.0), and description.
     - Synthetic logs use a random seed for reproducibility and employ a beta distribution to model realistic condition changes:
       - `new_condition = round(random.betavariate(alpha=5, beta=1) * current_condition, 1)`
   - Replacement tasks are triggered for equipment with low condition or high risk, prioritized before routine tasks.
   - For each executed task, the equipment node's condition is improved, and the maintenance history is updated. Deferred tasks increase the deferred count, impacting future RUL calculations.

7. Reporting and Analysis
   - After each month, the simulation engine records the scheduled, executed, and deferred tasks, maintenance logs, and replacement actions.
   - The updated graph state (including RUL, condition, and risk) is saved for each month, enabling time-series analysis.
   - System-wide summaries include total tasks scheduled, executed, deferred, and replaced, as well as budget utilization and risk distribution.
   - Detailed component-level metrics and maintenance histories are available for further analysis and visualization.

### Simulation Output
The simulation engine outputs each month's RUL and risk assessment results in a dictionary format, with keys representing the month (e.g., "2023-01"). Each month's record contains:
- Month identifier (e.g., "2023-01")
- List of tasks scheduled for the month
  - This list includes all tasks that were scheduled, regardless of whether they end up executed or deferred.  Tasks that were deferred from previous months will also appear in this list, since they will need to be tracked until they are completed.
- rollover_time_budget
  - Unused time budget carried over from previous month (if rollover is enabled)
- rollover_money_budget
  - Unused money budget carried over from previous month (if rollover is enabled)
- time_budget
  - Total time budget allocated for the month
  - This is added to the rollover_time_budget to determine the total time available for maintenance tasks in the month.
  - The time budget is refreshed at the start of each month based on user settings.
- money_budget
  - Total money budget allocated for the month
  - This is added to the rollover_money_budget to determine the total money available for maintenance tasks in the month.
  - The money budget is refreshed at the start of each month based on user settings.
- graph
  - The updated building graph with current RUL, risk levels, and condition for all equipment nodes, other metadata, and structural information, enabling detailed time-series analysis and visualization.
  - This graph reflects all changes made during the month, including executed maintenance tasks, condition updates, and any replacements.
  - The graph is stored in NetworkX format for compatibility with various analysis and visualization tools.
- executed_tasks
  - List of tasks that were successfully executed during the month, including details such as task type, associated equipment, time and money costs, and completion status.
- deferred_tasks
  - List of tasks that were deferred during the month, including reasons for deferral and any impacts on future scheduling.
- maintenance_logs
  - Records of all maintenance activities performed during the month, including inspections, repairs, and replacements.
  - These are synthetic logs generated to simulate real-world maintenance records if synthetic log generation is enabled.
- replacement_tasks_executed
  - List of equipment replacement tasks completed during the month, with details on replaced components and associated costs.
- replacement_tasks_not_executed
  - List of planned replacement tasks that were not executed, including reasons.

## Future Work
Future enhancements to AssetWise could include:
1. Using real-world asset history and maintenance data to determine accurate simulation parameters, refine simulation logic, and validate synthetic data generation.
2. Incorporating more complex asset interactions and dependencies in the graph model to better simulate real-world scenarios.
3. Incorporate remodeling and expansion scenarios to simulate changes in building systems over time.
4. Integrate machine learning techniques to predict failures and optimize maintenance schedules based on historical data.
5. Expand the user interface to include more advanced visualization and reporting features, enabling deeper insights into asset management strategies.
6. Expand the user interface to include more advanced system graph interaction and editing capabilities, allowing users to modify the building graph directly within the application.
7. Incorporate real-time data integration from building management systems (BMS) or Internet of Things (IoT) sensors to inform RUL calculations and maintenance scheduling.
8. Develop a collaborative platform where multiple users can work on the same asset management scenarios, sharing insights and strategies.