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
## User Defined Parameters

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

### Simulation Parameters
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

## Building Electrical System Generation Logic
The generator uses the user-specified building parameters to compute derived attributes like total area.

It calculates the number of vertical risers as one riser per 500 square meters of floor area, rounding up to ensure adequate distribution.  This is a simplification; in practice, riser count may depend on building codes and design practices.  Risers are located within the footprint, spaced along the longer dimension and centered along the shorter dimension, with some randomness to avoid perfectly regular placement.

The system voltage level is chosen based on total electrical load and step-down transformers are included where high-voltage distribution requires them, using standard three‑phase voltage levels (e.g., 480Y/277V or 208Y/120V). 

Total load is allocated across floors with random variation (±10%) and end loads (lighting, receptacles, HVAC, etc.) are assigned to floors and located at the nearest riser; each end load receives a type, power rating, and voltage level consistent with the building system. 

For each riser on each floor the generator summarizes total power per end load type and voltage to support sizing of distribution equipment and to understand load distribution. 

Distribution equipment (main panels, sub‑panels, transformers) is placed for each riser and floor according to end loads and voltage requirements, including step‑down transformers and multiple panels as needed, and the graph is built by connecting utility transformers to main panels, main panels to risers, risers to distribution equipment, and distribution equipment to end loads. 

Finally, helper modules assign risk scores and remaining useful life (RUL) values to each node, a summary report of the generated building is produced (total load, equipment counts, end load breakdown, per‑floor/riser details), and the graph is saved in GraphML for further analysis.

## Simulation Process
# Results
# Discussion
# Conclusion
# References

::: {#refs}
:::
