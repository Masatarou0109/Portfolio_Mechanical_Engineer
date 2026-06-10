import sys
import unittest
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from bearing_friction import (
    calculate_bearing_friction_torque,
    calculate_friction_heat,
    calculate_wheel_load,
)
from speed_profile import calculate_wheel_kinematics, create_time_array
from thermal_model import calculate_temperature_response


class TestEngineeringCalculations(unittest.TestCase):
    def test_wheel_load_and_friction_heat_are_positive(self):
        wheel_load = calculate_wheel_load(1600.0, 400.0, 8)
        torque = calculate_bearing_friction_torque(0.0015, wheel_load, 0.025)
        heat = calculate_friction_heat(torque, np.array([0.0, 100.0]))

        self.assertGreater(wheel_load, 0.0)
        self.assertGreater(torque, 0.0)
        self.assertAlmostEqual(float(heat[0]), 0.0)
        self.assertGreater(float(heat[1]), 0.0)

    def test_wheel_kinematics_matches_expected_rpm(self):
        omega, rpm = calculate_wheel_kinematics(np.array([10.0]), 0.2)

        self.assertAlmostEqual(float(omega[0]), 50.0)
        self.assertAlmostEqual(float(rpm[0]), 477.464829, places=5)

    def test_temperature_response_rises_with_constant_heat(self):
        t = create_time_array(10.0, 1.0)
        heat = np.full_like(t, 20.0, dtype=float)
        temperature = calculate_temperature_response(t, heat, 500.0, 1.0, 25.0, 25.0)

        self.assertEqual(len(temperature), len(t))
        self.assertGreater(float(temperature[-1]), 25.0)


if __name__ == '__main__':
    unittest.main()
