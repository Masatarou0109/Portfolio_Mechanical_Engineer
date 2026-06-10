from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from thermal_network import calculate_link_heat_flows, rank_bottlenecks, solve_steady_state


def load_design_options(path: str | Path) -> list[dict]:
    with Path(path).open('r', encoding='utf-8') as f:
        return json.load(f)


def apply_design_option(
    links: pd.DataFrame,
    heat_loads: pd.DataFrame,
    option: dict,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    modified_links = links.copy()
    modified_heat_loads = heat_loads.copy()

    for link_id, multiplier in option.get('link_resistance_multipliers', {}).items():
        mask = modified_links['link_id'] == link_id
        modified_links.loc[mask, 'resistance_k_per_w'] *= float(multiplier)

    for node_id, multiplier in option.get('heat_load_multipliers', {}).items():
        mask = modified_heat_loads['node_id'] == node_id
        modified_heat_loads.loc[mask, 'heat_w'] *= float(multiplier)

    return modified_links, modified_heat_loads


def evaluate_design_options(
    nodes: pd.DataFrame,
    links: pd.DataFrame,
    heat_loads: pd.DataFrame,
    boundaries: pd.DataFrame,
    options: list[dict],
    cost_weight: float = 1.5,
) -> tuple[pd.DataFrame, dict[str, pd.DataFrame], dict[str, pd.DataFrame]]:
    rows = []
    node_results = {}
    flow_results = {}

    for option in options:
        modified_links, modified_heat_loads = apply_design_option(links, heat_loads, option)
        temperatures = solve_steady_state(nodes, modified_links, modified_heat_loads, boundaries)
        flows = calculate_link_heat_flows(modified_links, temperatures)
        bottlenecks = rank_bottlenecks(flows)

        max_temperature = temperatures['temperature_c'].max()
        minimum_margin = temperatures['margin_to_limit_c'].min()
        total_heat_load = modified_heat_loads['heat_w'].sum()
        objective = max_temperature + cost_weight * float(option.get('cost_index', 0.0))

        rows.append({
            'option_id': option['option_id'],
            'description': option['description'],
            'cost_index': option.get('cost_index', 0.0),
            'total_heat_load_w': total_heat_load,
            'max_temperature_c': max_temperature,
            'minimum_margin_to_limit_c': minimum_margin,
            'worst_node': temperatures.sort_values('margin_to_limit_c').iloc[0]['node_id'],
            'top_bottleneck_link': bottlenecks.iloc[0]['link_id'],
            'objective': objective,
            'status': 'OK' if minimum_margin >= 0.0 else 'NG',
        })
        node_results[option['option_id']] = temperatures
        flow_results[option['option_id']] = flows

    summary = pd.DataFrame(rows).sort_values(['status', 'objective', 'minimum_margin_to_limit_c'])
    return summary, node_results, flow_results
