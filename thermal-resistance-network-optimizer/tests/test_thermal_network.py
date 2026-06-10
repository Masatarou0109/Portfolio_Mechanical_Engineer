import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from optimizer import evaluate_design_options, load_design_options
from thermal_network import calculate_link_heat_flows, load_network_inputs, solve_steady_state


class TestThermalNetwork(unittest.TestCase):
    def setUp(self):
        self.nodes, self.links, self.heat_loads, self.boundaries = load_network_inputs(PROJECT_ROOT / 'data')

    def test_baseline_solution_has_hotter_bearing_than_ambient(self):
        result = solve_steady_state(self.nodes, self.links, self.heat_loads, self.boundaries)
        bearing_temp = float(result.loc[result['node_id'] == 'bearing_inner', 'temperature_c'].iloc[0])
        ambient_temp = float(result.loc[result['node_id'] == 'ambient', 'temperature_c'].iloc[0])

        self.assertGreater(bearing_temp, ambient_temp)

    def test_link_heat_flow_conserves_heat_direction(self):
        result = solve_steady_state(self.nodes, self.links, self.heat_loads, self.boundaries)
        flows = calculate_link_heat_flows(self.links, result)

        self.assertEqual(len(flows), len(self.links))
        self.assertGreater(flows['abs_heat_flow_w'].sum(), 0.0)

    def test_design_options_include_cooling_improvement(self):
        options = load_design_options(PROJECT_ROOT / 'data' / 'design_options.json')
        summary, _, _ = evaluate_design_options(self.nodes, self.links, self.heat_loads, self.boundaries, options)

        baseline_temp = float(summary.loc[summary['option_id'] == 'baseline', 'max_temperature_c'].iloc[0])
        best_temp = float(summary['max_temperature_c'].min())
        self.assertLess(best_temp, baseline_temp)


if __name__ == '__main__':
    unittest.main()
