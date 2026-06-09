"""Lumped bearing thermal response model."""

import numpy as np


def calculate_temperature_response(
    t: np.ndarray,
    heat_generation_W: np.ndarray,
    thermal_capacity_J_per_K: float,
    heat_dissipation_W_per_K: float,
    ambient_temperature_C: float,
    initial_temperature_C: float,
) -> np.ndarray:
    """
    Calculate bearing temperature with explicit Euler integration.

    C_th * dT/dt = Q_dot - hA * (T - T_amb)
    """
    if len(t) == 0:
        raise ValueError("t must not be empty")
    if len(t) != len(heat_generation_W):
        raise ValueError("t and heat_generation_W must have the same length")
    if thermal_capacity_J_per_K <= 0:
        raise ValueError("thermal_capacity_J_per_K must be positive")
    if heat_dissipation_W_per_K < 0:
        raise ValueError("heat_dissipation_W_per_K must be non-negative")

    temperature_C = np.zeros_like(t, dtype=float)
    temperature_C[0] = initial_temperature_C

    for i in range(1, len(t)):
        dt = t[i] - t[i - 1]
        dTdt = (
            heat_generation_W[i - 1]
            - heat_dissipation_W_per_K * (temperature_C[i - 1] - ambient_temperature_C)
        ) / thermal_capacity_J_per_K
        temperature_C[i] = temperature_C[i - 1] + dTdt * dt

    return temperature_C
