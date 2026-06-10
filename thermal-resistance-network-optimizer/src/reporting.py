from pathlib import Path

import pandas as pd


def write_markdown_report(
    baseline_nodes: pd.DataFrame,
    bottlenecks: pd.DataFrame,
    option_summary: pd.DataFrame,
    output_path: str | Path,
) -> None:
    output_path = Path(output_path)
    best = option_summary.iloc[0]
    lines = [
        '# Thermal Resistance Network Optimization Report',
        '',
        '## Executive Summary',
        '',
        (
            f"Recommended option: **{best['option_id']}** - {best['description']}. "
            f"Maximum temperature = {best['max_temperature_c']:.2f} deg C, "
            f"minimum margin = {best['minimum_margin_to_limit_c']:.2f} deg C, "
            f"cost index = {best['cost_index']:.2f}."
        ),
        '',
        '## Baseline Node Temperatures',
        '',
        baseline_nodes[['node_id', 'description', 'temperature_c', 'temp_limit_c', 'margin_to_limit_c', 'status']]
        .round(3)
        .to_markdown(index=False),
        '',
        '## Thermal Bottleneck Ranking',
        '',
        bottlenecks[['link_id', 'description', 'delta_t_c', 'heat_flow_w', 'resistance_k_per_w']]
        .round(4)
        .to_markdown(index=False),
        '',
        '## Design Option Comparison',
        '',
        option_summary[
            [
                'option_id',
                'description',
                'cost_index',
                'max_temperature_c',
                'minimum_margin_to_limit_c',
                'top_bottleneck_link',
                'objective',
                'status',
            ]
        ].round(4).to_markdown(index=False),
        '',
        '## Notes',
        '',
        '- This is a portfolio demonstration based on a simplified steady-state thermal resistance network.',
        '- Thermal resistance values, heat loads, and design options are fictional and should be replaced with validated engineering data for real projects.',
    ]
    output_path.write_text('\n'.join(lines), encoding='utf-8')
