"""Catalog-based genetic optimization for bearing thermal-risk mitigation.

This version uses design variables that are easier to explain in an
engineering portfolio than abstract scale factors:

- bearing type
- lubricant type
- wheel material
- wheel radius
- cooling airflow
- operating gap between repeated cycles

The catalog values are fictional and should be replaced with real supplier
data before using the model for any real design decision.
"""

from __future__ import annotations

from dataclasses import dataclass
import csv
import random

import numpy as np

from bearing_friction import (
    calculate_bearing_friction_torque,
    calculate_friction_heat,
    calculate_wheel_load,
)
from main import FIGURE_DIR, ROOT, load_parameters
from speed_profile import calculate_wheel_kinematics, create_speed_profile, create_time_array
from visualization import plot_line


OUTPUT_DIR = ROOT / "outputs"

BEARING_CATALOG = [
    {
        "name": "Standard deep-groove ball bearing",
        "effective_radius_m": 0.025,
        "friction_factor": 1.00,
        "load_rating_N": 3200.0,
        "cost_index": 1.00,
    },
    {
        "name": "Low-friction sealed ball bearing",
        "effective_radius_m": 0.024,
        "friction_factor": 0.78,
        "load_rating_N": 3000.0,
        "cost_index": 1.45,
    },
    {
        "name": "Hybrid ceramic ball bearing",
        "effective_radius_m": 0.023,
        "friction_factor": 0.62,
        "load_rating_N": 2800.0,
        "cost_index": 2.40,
    },
    {
        "name": "Heavy-duty roller bearing",
        "effective_radius_m": 0.030,
        "friction_factor": 1.18,
        "load_rating_N": 5200.0,
        "cost_index": 1.70,
    },
]

LUBRICANT_CATALOG = [
    {
        "name": "General-purpose grease",
        "friction_factor": 1.00,
        "temperature_margin_C": 35.0,
        "cost_index": 1.00,
    },
    {
        "name": "Low-viscosity synthetic grease",
        "friction_factor": 0.82,
        "temperature_margin_C": 45.0,
        "cost_index": 1.35,
    },
    {
        "name": "High-temperature synthetic grease",
        "friction_factor": 0.92,
        "temperature_margin_C": 70.0,
        "cost_index": 1.55,
    },
]

WHEEL_MATERIAL_CATALOG = [
    {
        "name": "Polyurethane wheel",
        "thermal_capacity_factor": 1.00,
        "heat_dissipation_factor": 1.00,
        "cost_index": 1.00,
    },
    {
        "name": "Aluminum-core polyurethane wheel",
        "thermal_capacity_factor": 1.12,
        "heat_dissipation_factor": 1.35,
        "cost_index": 1.45,
    },
    {
        "name": "Steel-core polyurethane wheel",
        "thermal_capacity_factor": 1.25,
        "heat_dissipation_factor": 1.55,
        "cost_index": 1.65,
    },
]

CONTINUOUS_BOUNDS = {
    "wheel_radius_m": (0.13, 0.19),
    "airflow_m_per_s": (0.0, 8.0),
    "cycle_gap_s": (30.0, 180.0),
}

GA_SETTINGS = {
    "seed": 7,
    "generations": 90,
    "population_size": 72,
    "elite_count": 5,
    "tournament_size": 3,
    "mutation_rate": 0.20,
    "cycle_count": 20,
    "temperature_limit_C": 27.0,
}


@dataclass
class Candidate:
    """One design candidate."""

    bearing_index: int
    lubricant_index: int
    material_index: int
    wheel_radius_m: float
    airflow_m_per_s: float
    cycle_gap_s: float
    objective: float | None = None
    max_temperature_C: float | None = None
    temperature_rise_C: float | None = None
    max_heat_W: float | None = None
    wheel_load_N: float | None = None
    design_cost: float | None = None
    constraint_penalty: float | None = None

    @property
    def bearing(self) -> dict:
        return BEARING_CATALOG[self.bearing_index]

    @property
    def lubricant(self) -> dict:
        return LUBRICANT_CATALOG[self.lubricant_index]

    @property
    def material(self) -> dict:
        return WHEEL_MATERIAL_CATALOG[self.material_index]

    def as_dict(self) -> dict:
        """Return a CSV-friendly representation."""
        return {
            "bearing": self.bearing["name"],
            "lubricant": self.lubricant["name"],
            "wheel_material": self.material["name"],
            "wheel_radius_m": self.wheel_radius_m,
            "airflow_m_per_s": self.airflow_m_per_s,
            "cycle_gap_s": self.cycle_gap_s,
            "objective": self.objective,
            "max_temperature_C": self.max_temperature_C,
            "temperature_rise_C": self.temperature_rise_C,
            "max_heat_W": self.max_heat_W,
            "wheel_load_N": self.wheel_load_N,
            "design_cost": self.design_cost,
            "constraint_penalty": self.constraint_penalty,
        }


def clamp(value: float, lower: float, upper: float) -> float:
    """Clamp a value to a numeric range."""
    return min(upper, max(lower, value))


def random_candidate(rng: random.Random) -> Candidate:
    """Create a random candidate."""
    return Candidate(
        bearing_index=rng.randrange(len(BEARING_CATALOG)),
        lubricant_index=rng.randrange(len(LUBRICANT_CATALOG)),
        material_index=rng.randrange(len(WHEEL_MATERIAL_CATALOG)),
        wheel_radius_m=rng.uniform(*CONTINUOUS_BOUNDS["wheel_radius_m"]),
        airflow_m_per_s=rng.uniform(*CONTINUOUS_BOUNDS["airflow_m_per_s"]),
        cycle_gap_s=rng.uniform(*CONTINUOUS_BOUNDS["cycle_gap_s"]),
    )


def make_baseline_candidate(params: dict) -> Candidate:
    """Return the original baseline design."""
    return Candidate(
        bearing_index=0,
        lubricant_index=0,
        material_index=0,
        wheel_radius_m=params["wheel_radius_m"],
        airflow_m_per_s=0.0,
        cycle_gap_s=60.0,
    )


def simulate_single_cycle_components(params: dict, candidate: Candidate) -> dict:
    """Calculate one-cycle heat response components for fast repeated evaluation."""
    t = create_time_array(params["simulation_time_s"], params["time_step_s"])
    speed = create_speed_profile(t)
    omega, rpm = calculate_wheel_kinematics(speed, candidate.wheel_radius_m)

    wheel_load = calculate_wheel_load(
        params["vehicle_mass_kg"],
        params["passenger_mass_kg"],
        params["number_of_wheels"],
    )
    effective_mu = (
        params["bearing_equivalent_friction_coefficient"]
        * candidate.bearing["friction_factor"]
        * candidate.lubricant["friction_factor"]
    )
    friction_torque = calculate_bearing_friction_torque(
        effective_mu,
        wheel_load,
        candidate.bearing["effective_radius_m"],
    )
    heat_generation = calculate_friction_heat(friction_torque, omega)

    airflow_factor = 1.0 + 0.09 * candidate.airflow_m_per_s
    thermal_capacity = (
        params["thermal_capacity_J_per_K"] * candidate.material["thermal_capacity_factor"]
    )
    heat_dissipation = (
        params["heat_dissipation_W_per_K"]
        * candidate.material["heat_dissipation_factor"]
        * airflow_factor
    )

    dt = params["time_step_s"]
    decay = 1.0 - heat_dissipation * dt / thermal_capacity
    if decay <= 0:
        raise ValueError("time_step_s is too large for this thermal configuration")

    heat_only_rise = np.zeros_like(t, dtype=float)
    for i in range(1, len(t)):
        heat_only_rise[i] = decay * heat_only_rise[i - 1] + heat_generation[i - 1] * dt / thermal_capacity

    return {
        "t": t,
        "speed": speed,
        "rpm": rpm,
        "heat_generation": heat_generation,
        "heat_only_rise": heat_only_rise,
        "decay_from_initial": decay ** np.arange(len(t), dtype=float),
        "per_step_decay": float(decay),
        "max_heat_W": float(np.max(heat_generation)),
        "wheel_load_N": float(wheel_load),
    }


def simulate_repeated_operation(
    params: dict,
    candidate: Candidate,
    *,
    cycle_count: int,
    return_profile: bool = False,
) -> dict:
    """Simulate repeated coaster operation with cooldown gaps."""
    components = simulate_single_cycle_components(params, candidate)
    ambient = params["ambient_temperature_C"]
    dt = params["time_step_s"]
    gap_steps = int(round(candidate.cycle_gap_s / dt))
    gap_decay = components["per_step_decay"] ** gap_steps

    start_rise = 0.0
    max_rise = 0.0
    full_time = []
    full_temperature = []

    for cycle_index in range(cycle_count):
        cycle_rise = components["heat_only_rise"] + components["decay_from_initial"] * start_rise
        max_rise = max(max_rise, float(np.max(cycle_rise)))

        if return_profile:
            cycle_offset = cycle_index * (params["simulation_time_s"] + candidate.cycle_gap_s)
            full_time.extend((components["t"] + cycle_offset).tolist())
            full_temperature.extend((ambient + cycle_rise).tolist())

        end_rise = float(cycle_rise[-1])
        if return_profile and gap_steps > 0:
            gap_time = cycle_offset + params["simulation_time_s"] + np.arange(1, gap_steps + 1) * dt
            gap_decay_curve = components["per_step_decay"] ** np.arange(1, gap_steps + 1, dtype=float)
            gap_rise = end_rise * gap_decay_curve
            full_time.extend(gap_time.tolist())
            full_temperature.extend((ambient + gap_rise).tolist())

        start_rise = end_rise * gap_decay

    result = {
        "max_heat_W": components["max_heat_W"],
        "wheel_load_N": components["wheel_load_N"],
        "max_temperature_C": ambient + max_rise,
        "temperature_rise_C": max_rise,
    }
    if return_profile:
        result["t"] = np.array(full_time)
        result["temperature"] = np.array(full_temperature)
    return result


def design_change_cost(params: dict, candidate: Candidate) -> float:
    """Estimate fictional implementation and operating cost."""
    baseline_radius = params["wheel_radius_m"]
    radius_change = abs(candidate.wheel_radius_m - baseline_radius) / baseline_radius
    airflow_cost = (candidate.airflow_m_per_s / CONTINUOUS_BOUNDS["airflow_m_per_s"][1]) ** 2
    gap_cost = max(0.0, (candidate.cycle_gap_s - 60.0) / 120.0) ** 2

    return (
        candidate.bearing["cost_index"]
        + candidate.lubricant["cost_index"]
        + candidate.material["cost_index"]
        + 2.5 * radius_change**2
        + 1.4 * airflow_cost
        + 1.8 * gap_cost
    )


def evaluate(candidate: Candidate, params: dict, settings: dict, baseline_rise_C: float) -> Candidate:
    """Evaluate one candidate and assign objective and constraints."""
    result = simulate_repeated_operation(params, candidate, cycle_count=settings["cycle_count"])
    cost = design_change_cost(params, candidate)

    over_limit_C = max(0.0, result["max_temperature_C"] - settings["temperature_limit_C"])
    load_over_rating_N = max(0.0, result["wheel_load_N"] - candidate.bearing["load_rating_N"])
    lubricant_over_margin_C = max(
        0.0,
        result["max_temperature_C"]
        - (params["ambient_temperature_C"] + candidate.lubricant["temperature_margin_C"]),
    )

    constraint_penalty = (
        120.0 * over_limit_C**2
        + 0.0008 * load_over_rating_N**2
        + 50.0 * lubricant_over_margin_C**2
    )
    normalized_rise = result["temperature_rise_C"] / max(baseline_rise_C, 1e-9)
    objective = normalized_rise + 0.08 * cost + constraint_penalty

    candidate.objective = objective
    candidate.max_temperature_C = result["max_temperature_C"]
    candidate.temperature_rise_C = result["temperature_rise_C"]
    candidate.max_heat_W = result["max_heat_W"]
    candidate.wheel_load_N = result["wheel_load_N"]
    candidate.design_cost = cost
    candidate.constraint_penalty = constraint_penalty
    return candidate


def tournament_select(population: list[Candidate], rng: random.Random, size: int) -> Candidate:
    """Select the best candidate from a random tournament."""
    competitors = rng.sample(population, size)
    return min(competitors, key=lambda c: c.objective)


def crossover(a: Candidate, b: Candidate, rng: random.Random) -> Candidate:
    """Mix categorical and continuous design variables."""
    values = {
        "bearing_index": rng.choice([a.bearing_index, b.bearing_index]),
        "lubricant_index": rng.choice([a.lubricant_index, b.lubricant_index]),
        "material_index": rng.choice([a.material_index, b.material_index]),
    }
    for field, (lower, upper) in CONTINUOUS_BOUNDS.items():
        av = getattr(a, field)
        bv = getattr(b, field)
        span = abs(av - bv)
        raw = rng.uniform(min(av, bv) - 0.35 * span, max(av, bv) + 0.35 * span)
        values[field] = clamp(raw, lower, upper)
    return Candidate(**values)


def mutate(candidate: Candidate, rng: random.Random, rate: float, generation_ratio: float) -> Candidate:
    """Mutate categorical choices and continuous values."""
    if rng.random() < rate:
        candidate.bearing_index = rng.randrange(len(BEARING_CATALOG))
    if rng.random() < rate:
        candidate.lubricant_index = rng.randrange(len(LUBRICANT_CATALOG))
    if rng.random() < rate:
        candidate.material_index = rng.randrange(len(WHEEL_MATERIAL_CATALOG))

    shrink = 1.0 - 0.65 * generation_ratio
    for field, (lower, upper) in CONTINUOUS_BOUNDS.items():
        if rng.random() < rate:
            width = upper - lower
            mutated = getattr(candidate, field) + rng.gauss(0.0, width * 0.12 * shrink)
            setattr(candidate, field, clamp(mutated, lower, upper))

    return candidate


def run_ga(params: dict, settings: dict = GA_SETTINGS) -> tuple[Candidate, list[dict], list[Candidate]]:
    """Run the genetic algorithm."""
    rng = random.Random(settings["seed"])
    baseline = evaluate(make_baseline_candidate(params), params, settings, baseline_rise_C=1.0)
    baseline_rise_C = baseline.temperature_rise_C

    population = [make_baseline_candidate(params)]
    population.extend(random_candidate(rng) for _ in range(settings["population_size"] - 1))
    population = [evaluate(candidate, params, settings, baseline_rise_C) for candidate in population]

    history = []
    for generation in range(settings["generations"] + 1):
        population.sort(key=lambda c: c.objective)
        best = population[0]
        history.append(
            {
                "generation": generation,
                "best_objective": best.objective,
                "mean_objective": float(np.mean([c.objective for c in population])),
                "best_max_temperature_C": best.max_temperature_C,
                "best_design_cost": best.design_cost,
                "best_bearing": best.bearing["name"],
                "best_lubricant": best.lubricant["name"],
                "best_material": best.material["name"],
            }
        )

        if generation == settings["generations"]:
            break

        next_population = population[: settings["elite_count"]]
        generation_ratio = generation / max(settings["generations"], 1)
        while len(next_population) < settings["population_size"]:
            parent_a = tournament_select(population, rng, settings["tournament_size"])
            parent_b = tournament_select(population, rng, settings["tournament_size"])
            child = mutate(crossover(parent_a, parent_b, rng), rng, settings["mutation_rate"], generation_ratio)
            next_population.append(evaluate(child, params, settings, baseline_rise_C))

        population = next_population

    population.sort(key=lambda c: c.objective)
    return population[0], history, population


def save_history_csv(history: list[dict]) -> str:
    """Save GA convergence history."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    path = OUTPUT_DIR / "ga_convergence_history.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(history[0].keys()))
        writer.writeheader()
        writer.writerows(history)
    return str(path)


def save_population_csv(population: list[Candidate]) -> str:
    """Save final population."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    path = OUTPUT_DIR / "ga_final_population.csv"
    rows = [candidate.as_dict() for candidate in population]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return str(path)


def save_best_temperature_profile(params: dict, best: Candidate, settings: dict) -> str:
    """Save the repeated-cycle temperature profile for the best design."""
    result = simulate_repeated_operation(
        params,
        best,
        cycle_count=settings["cycle_count"],
        return_profile=True,
    )
    path = plot_line(
        result["t"],
        result["temperature"],
        "Time [s]",
        "Bearing temperature [deg C]",
        "Optimized Repeated-Cycle Temperature Profile",
        "ga_best_temperature_profile.png",
        FIGURE_DIR,
    )
    return str(path)


def main() -> None:
    params = load_parameters()
    best, history, population = run_ga(params)
    baseline = evaluate(make_baseline_candidate(params), params, GA_SETTINGS, baseline_rise_C=1.0)

    history_path = save_history_csv(history)
    population_path = save_population_csv(population)
    profile_path = save_best_temperature_profile(params, best, GA_SETTINGS)
    convergence_path = plot_line(
        np.array([row["generation"] for row in history]),
        np.array([row["best_objective"] for row in history]),
        "Generation",
        "Best objective",
        "GA Convergence",
        "ga_convergence.png",
        FIGURE_DIR,
    )

    print("=== Catalog-Based Genetic Optimization ===")
    print(f"Repeated operation: {GA_SETTINGS['cycle_count']} cycles")
    print(f"Temperature limit: {GA_SETTINGS['temperature_limit_C']:.2f} deg C")
    print(f"Baseline max temperature: {baseline.max_temperature_C:.2f} deg C")
    print(f"Best max temperature: {best.max_temperature_C:.2f} deg C")
    print(f"Best temperature rise: {best.temperature_rise_C:.3f} deg C")
    print(f"Best objective: {best.objective:.4f}")
    print(f"Design cost index: {best.design_cost:.3f}")
    print(f"Bearing: {best.bearing['name']}")
    print(f"Lubricant: {best.lubricant['name']}")
    print(f"Wheel material: {best.material['name']}")
    print(f"Wheel radius: {best.wheel_radius_m:.3f} m")
    print(f"Cooling airflow: {best.airflow_m_per_s:.2f} m/s")
    print(f"Cycle gap: {best.cycle_gap_s:.1f} s")
    print(f"History CSV saved to: {history_path}")
    print(f"Final population CSV saved to: {population_path}")
    print(f"Convergence figure saved to: {convergence_path}")
    print(f"Best profile figure saved to: {profile_path}")


if __name__ == "__main__":
    main()
