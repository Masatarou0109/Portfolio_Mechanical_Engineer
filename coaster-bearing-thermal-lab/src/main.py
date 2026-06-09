"""
Coaster Bearing Thermal Lab

Version 0.2 baseline calculation for a fictional roller coaster wheel bearing.
"""

from pathlib import Path
import json

import numpy as np

from bearing_friction import (
    calculate_bearing_friction_torque,
    calculate_friction_heat,
    calculate_wheel_load,
)
from speed_profile import (
    calculate_wheel_kinematics,
    create_speed_profile,
    create_time_array,
)
from thermal_model import calculate_temperature_response
from visualization import plot_line


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
FIGURE_DIR = ROOT / "figures"


def load_parameters() -> dict:
    """Load design parameters from JSON."""
    with open(DATA_DIR / "design_parameters.json", "r", encoding="utf-8") as f:
        return json.load(f)


def run_baseline(params: dict) -> dict:
    """Run the baseline bearing thermal simulation."""
    t = create_time_array(params["simulation_time_s"], params["time_step_s"])
    speed = create_speed_profile(t)
    omega, rpm = calculate_wheel_kinematics(speed, params["wheel_radius_m"])

    wheel_load = calculate_wheel_load(
        params["vehicle_mass_kg"],
        params["passenger_mass_kg"],
        params["number_of_wheels"],
    )
    friction_torque = calculate_bearing_friction_torque(
        params["bearing_equivalent_friction_coefficient"],
        wheel_load,
        params["bearing_effective_radius_m"],
    )
    heat_generation = calculate_friction_heat(friction_torque, omega)
    temperature = calculate_temperature_response(
        t,
        heat_generation,
        params["thermal_capacity_J_per_K"],
        params["heat_dissipation_W_per_K"],
        params["ambient_temperature_C"],
        params["initial_bearing_temperature_C"],
    )

    return {
        "t": t,
        "speed": speed,
        "omega": omega,
        "rpm": rpm,
        "wheel_load": wheel_load,
        "friction_torque": friction_torque,
        "heat_generation": heat_generation,
        "temperature": temperature,
    }


def save_baseline_figures(result: dict) -> None:
    """Save baseline plots."""
    plot_line(
        result["t"],
        result["speed"],
        "Time [s]",
        "Vehicle speed [m/s]",
        "Fictional Roller Coaster Speed Profile",
        "speed_profile.png",
        FIGURE_DIR,
    )
    plot_line(
        result["t"],
        result["rpm"],
        "Time [s]",
        "Wheel rotational speed [rpm]",
        "Wheel Rotational Speed",
        "wheel_rpm.png",
        FIGURE_DIR,
    )
    plot_line(
        result["t"],
        result["heat_generation"],
        "Time [s]",
        "Frictional heat generation [W]",
        "Bearing Frictional Heat Generation",
        "friction_heat.png",
        FIGURE_DIR,
    )
    plot_line(
        result["t"],
        result["temperature"],
        "Time [s]",
        "Bearing temperature [deg C]",
        "Simplified Bearing Temperature Response",
        "temperature_response.png",
        FIGURE_DIR,
    )


def main() -> None:
    params = load_parameters()
    result = run_baseline(params)
    save_baseline_figures(result)

    print("=== Coaster Bearing Thermal Lab: Version 0.2 ===")
    print(f"Wheel load per wheel: {result['wheel_load']:.1f} N")
    print(f"Bearing friction torque: {result['friction_torque']:.4f} N*m")
    print(f"Maximum speed: {np.max(result['speed']):.2f} m/s")
    print(f"Maximum wheel speed: {np.max(result['rpm']):.1f} rpm")
    print(f"Maximum heat generation: {np.max(result['heat_generation']):.2f} W")
    print(f"Maximum bearing temperature: {np.max(result['temperature']):.2f} deg C")
    print(f"Figures saved to: {FIGURE_DIR}")


if __name__ == "__main__":
    main()
