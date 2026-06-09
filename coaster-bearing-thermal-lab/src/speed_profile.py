"""Speed profile and wheel kinematics utilities."""

import numpy as np


def create_time_array(total_time_s: float, dt_s: float) -> np.ndarray:
    """Create a simulation time array including the final time."""
    if total_time_s <= 0:
        raise ValueError("total_time_s must be positive")
    if dt_s <= 0:
        raise ValueError("dt_s must be positive")
    return np.arange(0.0, total_time_s + dt_s, dt_s)


def create_speed_profile(t: np.ndarray, speed_scale: float = 1.0) -> np.ndarray:
    """
    Create a fictional roller coaster speed profile.

    The profile is public-safe and not based on any real ride. ``speed_scale``
    can be used for mitigation studies.
    """
    if speed_scale < 0:
        raise ValueError("speed_scale must be non-negative")

    v = np.zeros_like(t, dtype=float)

    mask = (t >= 0) & (t < 40)
    v[mask] = 22.0 * (0.5 - 0.5 * np.cos(np.pi * t[mask] / 40.0))

    mask = (t >= 40) & (t < 100)
    v[mask] = 22.0 + 3.0 * np.sin(2.0 * np.pi * (t[mask] - 40.0) / 60.0)

    mask = (t >= 100) & (t < 150)
    tau = (t[mask] - 100.0) / 50.0
    v[mask] = 22.0 + (8.0 - 22.0) * (0.5 - 0.5 * np.cos(np.pi * tau))

    mask = (t >= 150) & (t < 230)
    v[mask] = 8.0 + 2.0 * np.sin(2.0 * np.pi * (t[mask] - 150.0) / 80.0)

    mask = (t >= 230) & (t < 270)
    tau = (t[mask] - 230.0) / 40.0
    v[mask] = 10.0 + (18.0 - 10.0) * (0.5 - 0.5 * np.cos(np.pi * tau))

    mask = t >= 270
    tau = np.clip((t[mask] - 270.0) / 30.0, 0.0, 1.0)
    v[mask] = 18.0 * (0.5 + 0.5 * np.cos(np.pi * tau))

    return v * speed_scale


def calculate_wheel_kinematics(
    speed_m_per_s: np.ndarray,
    wheel_radius_m: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Calculate wheel angular speed and rpm from vehicle speed."""
    if wheel_radius_m <= 0:
        raise ValueError("wheel_radius_m must be positive")

    omega_rad_per_s = speed_m_per_s / wheel_radius_m
    rpm = omega_rad_per_s * 60.0 / (2.0 * np.pi)
    return omega_rad_per_s, rpm
