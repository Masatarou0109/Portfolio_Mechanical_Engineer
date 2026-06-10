from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def save_node_temperature_plot(node_results: pd.DataFrame, output_path: str | Path) -> None:
    output_path = Path(output_path)
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.bar(node_results['node_id'], node_results['temperature_c'])
    ax.plot(node_results['node_id'], node_results['temp_limit_c'], marker='o', color='crimson', label='Temperature limit')
    ax.set_ylabel('Temperature [deg C]')
    ax.set_xlabel('Thermal node')
    ax.set_title('Baseline Node Temperatures')
    ax.tick_params(axis='x', rotation=25)
    ax.grid(axis='y', alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def save_design_option_plot(summary: pd.DataFrame, output_path: str | Path) -> None:
    output_path = Path(output_path)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(summary['option_id'], summary['max_temperature_c'])
    ax.set_ylabel('Max temperature [deg C]')
    ax.set_xlabel('Design option')
    ax.set_title('Thermal Design Option Comparison')
    ax.tick_params(axis='x', rotation=25)
    ax.grid(axis='y', alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def save_bottleneck_plot(bottlenecks: pd.DataFrame, output_path: str | Path, top_n: int = 5) -> None:
    output_path = Path(output_path)
    top = bottlenecks.head(top_n)
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.bar(top['link_id'], top['delta_t_c'].abs())
    ax.set_ylabel('Absolute temperature drop [deg C]')
    ax.set_xlabel('Thermal link')
    ax.set_title('Top Thermal Bottlenecks')
    ax.grid(axis='y', alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)
