"""Bearing load, friction torque, and heat generation calculations."""

import numpy as np


def calculate_wheel_load(
    vehicle_mass_kg: float,
    passenger_mass_kg: float,
    number_of_wheels: int,
) -> float:
    """Calculate static wheel load assuming evenly distributed mass."""
    if vehicle_mass_kg < 0:
        raise ValueError("vehicle_mass_kg must be non-negative")
    if passenger_mass_kg < 0:
        raise ValueError("passenger_mass_kg must be non-negative")
    if number_of_wheels <= 0:
        raise ValueError("number_of_wheels must be positive")

    g = 9.80665
    total_mass = vehicle_mass_kg + passenger_mass_kg
    return total_mass * g / number_of_wheels


def calculate_bearing_friction_torque(
    mu_equiv: float,
    wheel_load_N: float,
    bearing_radius_m: float,
) -> float:
    """Calculate simplified bearing friction torque: M_f = mu * F * r."""
    if mu_equiv < 0:
        raise ValueError("mu_equiv must be non-negative")
    if wheel_load_N < 0:
        raise ValueError("wheel_load_N must be non-negative")
    if bearing_radius_m <= 0:
        raise ValueError("bearing_radius_m must be positive")

    return mu_equiv * wheel_load_N * bearing_radius_m


def calculate_friction_heat(
    friction_torque_Nm: float,
    wheel_omega_rad_per_s: np.ndarray,
) -> np.ndarray:
    """Calculate frictional heat generation: Q_dot = M_f * omega."""
    if friction_torque_Nm < 0:
        raise ValueError("friction_torque_Nm must be non-negative")

    return friction_torque_Nm * wheel_omega_rad_per_s
