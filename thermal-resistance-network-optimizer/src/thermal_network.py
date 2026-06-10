from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def load_network_inputs(data_dir: str | Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    data_dir = Path(data_dir)
    nodes = pd.read_csv(data_dir / 'nodes.csv')
    links = pd.read_csv(data_dir / 'thermal_links.csv')
    heat_loads = pd.read_csv(data_dir / 'heat_loads.csv')
    boundaries = pd.read_csv(data_dir / 'boundary_conditions.csv')
    nodes['temp_limit_c'] = nodes['temp_limit_c'].astype(float)
    links['resistance_k_per_w'] = links['resistance_k_per_w'].astype(float)
    heat_loads['heat_w'] = heat_loads['heat_w'].astype(float)
    boundaries['temperature_c'] = boundaries['temperature_c'].astype(float)
    return nodes, links, heat_loads, boundaries


def validate_network(nodes: pd.DataFrame, links: pd.DataFrame, heat_loads: pd.DataFrame, boundaries: pd.DataFrame) -> None:
    node_ids = set(nodes['node_id'])
    linked_nodes = set(links['from_node']) | set(links['to_node'])
    unknown_link_nodes = linked_nodes - node_ids
    if unknown_link_nodes:
        raise ValueError(f'Links reference unknown nodes: {sorted(unknown_link_nodes)}')

    unknown_heat_nodes = set(heat_loads['node_id']) - node_ids
    if unknown_heat_nodes:
        raise ValueError(f'Heat loads reference unknown nodes: {sorted(unknown_heat_nodes)}')

    unknown_boundary_nodes = set(boundaries['node_id']) - node_ids
    if unknown_boundary_nodes:
        raise ValueError(f'Boundary conditions reference unknown nodes: {sorted(unknown_boundary_nodes)}')

    if (links['resistance_k_per_w'] <= 0).any():
        raise ValueError('All thermal resistances must be positive')


def solve_steady_state(
    nodes: pd.DataFrame,
    links: pd.DataFrame,
    heat_loads: pd.DataFrame,
    boundaries: pd.DataFrame,
) -> pd.DataFrame:
    validate_network(nodes, links, heat_loads, boundaries)

    node_ids = list(nodes['node_id'])
    fixed_temperatures = dict(zip(boundaries['node_id'], boundaries['temperature_c']))
    unknown_nodes = [node_id for node_id in node_ids if node_id not in fixed_temperatures]
    unknown_index = {node_id: i for i, node_id in enumerate(unknown_nodes)}

    conductance = np.zeros((len(unknown_nodes), len(unknown_nodes)), dtype=float)
    rhs = np.zeros(len(unknown_nodes), dtype=float)

    heat_by_node = heat_loads.groupby('node_id')['heat_w'].sum().to_dict()
    for node_id, heat_w in heat_by_node.items():
        if node_id in unknown_index:
            rhs[unknown_index[node_id]] += heat_w

    for _, link in links.iterrows():
        node_a = link['from_node']
        node_b = link['to_node']
        g = 1.0 / float(link['resistance_k_per_w'])

        a_unknown = node_a in unknown_index
        b_unknown = node_b in unknown_index

        if a_unknown and b_unknown:
            i = unknown_index[node_a]
            j = unknown_index[node_b]
            conductance[i, i] += g
            conductance[j, j] += g
            conductance[i, j] -= g
            conductance[j, i] -= g
        elif a_unknown and node_b in fixed_temperatures:
            i = unknown_index[node_a]
            conductance[i, i] += g
            rhs[i] += g * fixed_temperatures[node_b]
        elif b_unknown and node_a in fixed_temperatures:
            j = unknown_index[node_b]
            conductance[j, j] += g
            rhs[j] += g * fixed_temperatures[node_a]

    if len(unknown_nodes) == 0:
        temperatures = {}
    else:
        temperatures = dict(zip(unknown_nodes, np.linalg.solve(conductance, rhs)))
    temperatures.update(fixed_temperatures)

    result = nodes.copy()
    result['temperature_c'] = result['node_id'].map(temperatures)
    result['heat_load_w'] = result['node_id'].map(heat_by_node).fillna(0.0)
    result['margin_to_limit_c'] = result['temp_limit_c'] - result['temperature_c']
    result['status'] = np.where(result['margin_to_limit_c'] >= 0.0, 'OK', 'NG')
    return result


def calculate_link_heat_flows(links: pd.DataFrame, node_temperatures: pd.DataFrame) -> pd.DataFrame:
    temperature_by_node = dict(zip(node_temperatures['node_id'], node_temperatures['temperature_c']))
    rows = []
    for _, link in links.iterrows():
        from_temp = temperature_by_node[link['from_node']]
        to_temp = temperature_by_node[link['to_node']]
        delta_t = from_temp - to_temp
        heat_flow = delta_t / float(link['resistance_k_per_w'])
        rows.append({
            'link_id': link['link_id'],
            'from_node': link['from_node'],
            'to_node': link['to_node'],
            'description': link['description'],
            'resistance_k_per_w': link['resistance_k_per_w'],
            'from_temperature_c': from_temp,
            'to_temperature_c': to_temp,
            'delta_t_c': delta_t,
            'heat_flow_w': heat_flow,
            'abs_heat_flow_w': abs(heat_flow),
        })
    return pd.DataFrame(rows)


def rank_bottlenecks(link_heat_flows: pd.DataFrame) -> pd.DataFrame:
    ranked = link_heat_flows.copy()
    ranked['thermal_drop_score'] = ranked['delta_t_c'].abs()
    return ranked.sort_values(['thermal_drop_score', 'abs_heat_flow_w'], ascending=[False, False])
