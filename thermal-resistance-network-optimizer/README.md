# Thermal Resistance Network Optimizer

This Python project solves a steady-state thermal resistance network for a rotating machinery component and compares design options for reducing temperature.

The example model represents a simplified bearing, shaft, housing, cooling airflow, and ambient thermal path. It is designed as a portfolio-safe demonstration of thermal path modeling, bottleneck detection, and design optimization.

![Design option comparison](figures/design_option_comparison.png)

---

## Overview

Mechanical thermal problems are often governed by a small number of dominant heat paths. Before detailed CFD or FEA, a thermal resistance network can quickly estimate temperatures, heat flows, and bottlenecks.

This tool demonstrates how Python can be used to:

- solve a thermal resistance network
- calculate node temperatures and heat flow through each link
- rank thermal bottlenecks
- compare cooling and heat-reduction design options
- generate CSV, Markdown, and PNG outputs

---

## Model Concept

```text
friction heat source
        ↓
bearing inner race
        ↓
bearing outer race / shaft
        ↓
housing
        ↓
ambient and cooling airflow
```

The governing relationship for each thermal link is:

```text
Q = (T_hot - T_cold) / R_th
```

At each unknown node, the solver enforces steady-state heat balance.

---

## Input Files

| File | Purpose |
|---|---|
| `data/nodes.csv` | Thermal nodes and temperature limits |
| `data/thermal_links.csv` | Thermal resistance links between nodes |
| `data/heat_loads.csv` | Heat generation applied to nodes |
| `data/boundary_conditions.csv` | Fixed-temperature boundary nodes |
| `data/design_options.json` | Cooling and heat-reduction design options |

---

## How to Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/main.py
python -m unittest discover -s tests
```

---

## Outputs

| Output | Description |
|---|---|
| `outputs/baseline_node_temperatures.csv` | Baseline node temperatures and margins |
| `outputs/baseline_link_heat_flows.csv` | Heat flow through each thermal link |
| `outputs/thermal_bottleneck_ranking.csv` | Ranked thermal bottleneck list |
| `outputs/design_option_summary.csv` | Design option comparison table |
| `outputs/thermal_network_report.md` | Markdown summary report |
| `figures/baseline_node_temperatures.png` | Baseline node temperature chart |
| `figures/thermal_bottlenecks.png` | Thermal bottleneck chart |
| `figures/design_option_comparison.png` | Design option comparison chart |

---

## Portfolio Value

This project complements the other thermal engineering portfolio tools:

- `coaster-bearing-thermal-lab`: transient bearing heat generation and temperature response
- `automated-cae-design-review-tool`: thermal CAE post-processing and design review reporting
- `thermal-resistance-network-optimizer`: thermal path modeling, bottleneck detection, and design optimization

Together, they show a focused workflow for thermal simulation, thermal CAE review, and thermal design improvement for rotating machinery components.

---

## Notes

This is a simplified portfolio model. Thermal resistances, heat loads, boundary conditions, and design option effects are fictional and should be replaced with validated data before any real engineering use.
