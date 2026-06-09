"""Compare simple thermal-risk mitigation scenarios."""

from pathlib import Path
import csv

import numpy as np

from bearing_friction import (
    calculate_bearing_friction_torque,
    calculate_friction_heat,
    calculate_wheel_load,
)
from main import FIGURE_DIR, ROOT, load_parameters
from speed_profile import (
    calculate_wheel_kinematics,
    create_speed_profile,
    create_time_array,
)
from thermal_model import calculate_temperature_response
from visualization import plot_bar


OUTPUT_DIR = ROOT / "outputs"


def simulate_case(
    params: dict,
    *,
    name: str,
    friction_scale: float = 1.0,
    heat_dissipation_scale: float = 1.0,
    load_scale: float = 1.0,
    speed_scale: float = 1.0,
) -> dict:
    """Run one mitigation scenario and return summary metrics."""
    t = create_time_array(params["simulation_time_s"], params["time_step_s"])
    speed = create_speed_profile(t, speed_scale=speed_scale)
    omega, rpm = calculate_wheel_kinematics(speed, params["wheel_radius_m"])

    wheel_load = calculate_wheel_load(
        params["vehicle_mass_kg"],
        params["passenger_mass_kg"],
        params["number_of_wheels"],
    ) * load_scale
    friction_torque = calculate_bearing_friction_torque(
        params["bearing_equivalent_friction_coefficient"] * friction_scale,
        wheel_load,
        params["bearing_effective_radius_m"],
    )
    heat_generation = calculate_friction_heat(friction_torque, omega)
    temperature = calculate_temperature_response(
        t,
        heat_generation,
        params["thermal_capacity_J_per_K"],
        params["heat_dissipation_W_per_K"] * heat_dissipation_scale,
        params["ambient_temperature_C"],
        params["initial_bearing_temperature_C"],
    )

    return {
        "name": name,
        "max_speed_m_per_s": float(np.max(speed)),
        "max_rpm": float(np.max(rpm)),
        "wheel_load_N": float(wheel_load),
        "friction_torque_Nm": float(friction_torque),
        "max_heat_W": float(np.max(heat_generation)),
        "max_temperature_C": float(np.max(temperature)),
        "temperature_rise_C": float(np.max(temperature) - params["ambient_temperature_C"]),
    }


def run_study(params: dict) -> list[dict]:
    """Run baseline and four mitigation scenarios."""
    scenarios = [
        {"name": "Baseline"},
        {"name": "Lower friction", "friction_scale": 0.70},
        {"name": "Better cooling", "heat_dissipation_scale": 1.50},
        {"name": "Lower load", "load_scale": 0.85},
        {"name": "Reduced speed", "speed_scale": 0.90},
    ]
    return [simulate_case(params, **scenario) for scenario in scenarios]


def save_results_csv(results: list[dict]) -> Path:
    """Save mitigation summary table."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / "mitigation_study_results.csv"
    fieldnames = list(results[0].keys())

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    return output_path


def main() -> None:
    params = load_parameters()
    results = run_study(params)
    csv_path = save_results_csv(results)
    baseline_temperature = results[0]["max_temperature_C"]

    plot_bar(
        [row["name"] for row in results],
        [row["max_temperature_C"] for row in results],
        "Maximum bearing temperature [deg C]",
        "Mitigation Scenario Comparison",
        "mitigation_temperature_comparison.png",
        FIGURE_DIR,
    )
    plot_bar(
        [row["name"] for row in results],
        [row["temperature_rise_C"] for row in results],
        "Temperature rise above ambient [deg C]",
        "Mitigation Scenario Temperature Rise",
        "mitigation_temperature_rise.png",
        FIGURE_DIR,
    )
    plot_bar(
        [row["name"] for row in results],
        [baseline_temperature - row["max_temperature_C"] for row in results],
        "Temperature reduction from baseline [deg C]",
        "Mitigation Scenario Improvement",
        "mitigation_temperature_reduction.png",
        FIGURE_DIR,
    )

    print("=== Mitigation Study ===")
    for row in results:
        print(
            f"{row['name']}: max T = {row['max_temperature_C']:.2f} deg C, "
            f"max heat = {row['max_heat_W']:.2f} W"
        )
    print(f"CSV saved to: {csv_path}")
    print(f"Figure saved to: {FIGURE_DIR / 'mitigation_temperature_comparison.png'}")
    print(f"Figure saved to: {FIGURE_DIR / 'mitigation_temperature_rise.png'}")
    print(f"Figure saved to: {FIGURE_DIR / 'mitigation_temperature_reduction.png'}")


if __name__ == "__main__":
    main()
