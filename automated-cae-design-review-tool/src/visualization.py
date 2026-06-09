from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd


def save_case_comparison_plots(summary: pd.DataFrame, output_dir: str | Path) -> None:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    metrics = [
        ('max_temperature_c', 'Max Temperature [C]', 'case_comparison_temperature.png'),
        ('max_stress_vm_mpa', 'Max von Mises Stress [MPa]', 'case_comparison_stress.png'),
        ('max_displacement_mm', 'Max Displacement [mm]', 'case_comparison_displacement.png'),
        ('temperature_exceeded_area_percent', 'Temperature Exceeded Area [%]', 'case_comparison_exceeded_area.png'),
    ]
    for column, ylabel, filename in metrics:
        fig, ax = plt.subplots(figsize=(9, 4.8))
        ax.bar(summary['case_id'], summary[column])
        ax.set_ylabel(ylabel)
        ax.set_xlabel('CAE Case')
        ax.set_title(ylabel + ' by Case')
        ax.tick_params(axis='x', rotation=25)
        ax.grid(axis='y', alpha=0.3)
        fig.tight_layout()
        fig.savefig(output_dir / filename, dpi=180)
        plt.close(fig)


def save_risk_map(df: pd.DataFrame, output_dir: str | Path, case_id: str, value_col: str, title: str, filename: str) -> None:
    output_dir = Path(output_dir)
    g = df[df['case_id'] == case_id]
    fig, ax = plt.subplots(figsize=(7, 5.2))
    sc = ax.scatter(g['x_mm'], g['y_mm'], c=g[value_col], s=10)
    fig.colorbar(sc, ax=ax, label=value_col)
    ax.set_xlabel('x [mm]')
    ax.set_ylabel('y [mm]')
    ax.set_title(title)
    ax.set_aspect('equal', adjustable='box')
    fig.tight_layout()
    fig.savefig(output_dir / filename, dpi=180)
    plt.close(fig)
