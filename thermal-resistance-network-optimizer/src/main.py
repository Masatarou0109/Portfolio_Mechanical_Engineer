from pathlib import Path

from optimizer import evaluate_design_options, load_design_options
from reporting import write_markdown_report
from thermal_network import calculate_link_heat_flows, load_network_inputs, rank_bottlenecks, solve_steady_state
from visualization import save_bottleneck_plot, save_design_option_plot, save_node_temperature_plot


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data'
OUTPUT_DIR = ROOT / 'outputs'
FIGURE_DIR = ROOT / 'figures'


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    nodes, links, heat_loads, boundaries = load_network_inputs(DATA_DIR)
    baseline_nodes = solve_steady_state(nodes, links, heat_loads, boundaries)
    baseline_flows = calculate_link_heat_flows(links, baseline_nodes)
    bottlenecks = rank_bottlenecks(baseline_flows)

    options = load_design_options(DATA_DIR / 'design_options.json')
    option_summary, _, _ = evaluate_design_options(nodes, links, heat_loads, boundaries, options)

    baseline_nodes.to_csv(OUTPUT_DIR / 'baseline_node_temperatures.csv', index=False)
    baseline_flows.to_csv(OUTPUT_DIR / 'baseline_link_heat_flows.csv', index=False)
    bottlenecks.to_csv(OUTPUT_DIR / 'thermal_bottleneck_ranking.csv', index=False)
    option_summary.to_csv(OUTPUT_DIR / 'design_option_summary.csv', index=False)

    save_node_temperature_plot(baseline_nodes, FIGURE_DIR / 'baseline_node_temperatures.png')
    save_bottleneck_plot(bottlenecks, FIGURE_DIR / 'thermal_bottlenecks.png')
    save_design_option_plot(option_summary, FIGURE_DIR / 'design_option_comparison.png')
    write_markdown_report(baseline_nodes, bottlenecks, option_summary, OUTPUT_DIR / 'thermal_network_report.md')

    best = option_summary.iloc[0]
    print('Thermal resistance network optimization completed.')
    print(f"Recommended option: {best['option_id']} ({best['description']})")
    print(f"Max temperature: {best['max_temperature_c']:.2f} deg C")
    print(f"Minimum margin: {best['minimum_margin_to_limit_c']:.2f} deg C")
    print(f'Report: {OUTPUT_DIR / "thermal_network_report.md"}')


if __name__ == '__main__':
    main()
