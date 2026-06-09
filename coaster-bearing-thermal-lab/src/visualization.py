"""Plotting helpers for the coaster bearing thermal lab."""

from pathlib import Path
import os

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parents[1] / ".matplotlib"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def plot_line(
    x: np.ndarray,
    y: np.ndarray,
    xlabel: str,
    ylabel: str,
    title: str,
    filename: str,
    figure_dir: Path,
) -> Path:
    """Plot and save a line graph."""
    figure_dir.mkdir(exist_ok=True)
    output_path = figure_dir / filename

    plt.figure(figsize=(9, 5))
    plt.plot(x, y, linewidth=2)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()

    return output_path


def plot_bar(
    labels: list[str],
    values: list[float],
    ylabel: str,
    title: str,
    filename: str,
    figure_dir: Path,
) -> Path:
    """Plot and save a bar chart."""
    figure_dir.mkdir(exist_ok=True)
    output_path = figure_dir / filename

    plt.figure(figsize=(9, 5))
    plt.bar(labels, values)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.xticks(rotation=20, ha="right")
    plt.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()

    return output_path
