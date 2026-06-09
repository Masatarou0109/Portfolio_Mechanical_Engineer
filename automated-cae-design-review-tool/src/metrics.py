import numpy as np
import pandas as pd


def area_weighted_average(value: pd.Series, area: pd.Series) -> float:
    total_area = area.sum()
    if total_area == 0:
        return np.nan
    return float((value * area).sum() / total_area)


def percent_change(base_value: float, new_value: float) -> float:
    if pd.isna(base_value) or abs(base_value) <= 1e-12:
        return np.nan
    return float(100 * (new_value - base_value) / base_value)


def add_derived_columns(df: pd.DataFrame, criteria: dict) -> pd.DataFrame:
    df = df.copy()
    df['heat_flow_w'] = df['heat_flux_w_mm2'] * df['area_mm2']
    df['temperature_exceeded'] = df['temperature_c'] > criteria['temperature_limit_c']
    df['temperature_warning'] = df['temperature_c'] > criteria['temperature_warning_c']
    df['stress_exceeded'] = df['stress_vm_mpa'] > criteria['stress_allowable_mpa']
    df['displacement_exceeded'] = df['displacement_mm'] > criteria['displacement_limit_mm']
    df['safety_factor_local'] = criteria['stress_yield_mpa'] / df['stress_vm_mpa']
    return df


def summarize_cases(df: pd.DataFrame, criteria: dict) -> pd.DataFrame:
    rows = []
    for case_id, g in df.groupby('case_id', sort=True):
        total_area = g['area_mm2'].sum()
        temp_ex_area = g.loc[g['temperature_exceeded'], 'area_mm2'].sum()
        temp_warn_area = g.loc[g['temperature_warning'], 'area_mm2'].sum()
        stress_ex_area = g.loc[g['stress_exceeded'], 'area_mm2'].sum()
        disp_ex_area = g.loc[g['displacement_exceeded'], 'area_mm2'].sum()
        max_stress = g['stress_vm_mpa'].max()
        rows.append({
            'case_id': case_id,
            'description': str(g['case_description'].iloc[0]) if 'case_description' in g else '',
            'n_elements': len(g),
            'total_area_mm2': total_area,
            'max_temperature_c': g['temperature_c'].max(),
            'area_weighted_temperature_c': area_weighted_average(g['temperature_c'], g['area_mm2']),
            'temperature_exceeded_area_percent': 100 * temp_ex_area / total_area if total_area else np.nan,
            'temperature_warning_area_percent': 100 * temp_warn_area / total_area if total_area else np.nan,
            'max_stress_vm_mpa': max_stress,
            'area_weighted_stress_vm_mpa': area_weighted_average(g['stress_vm_mpa'], g['area_mm2']),
            'stress_exceeded_area_percent': 100 * stress_ex_area / total_area if total_area else np.nan,
            'minimum_safety_factor': criteria['stress_yield_mpa'] / max_stress if max_stress else np.nan,
            'max_displacement_mm': g['displacement_mm'].max(),
            'area_weighted_displacement_mm': area_weighted_average(g['displacement_mm'], g['area_mm2']),
            'displacement_exceeded_area_percent': 100 * disp_ex_area / total_area if total_area else np.nan,
            'total_heat_flow_w': g['heat_flow_w'].sum(),
            'area_weighted_heat_flux_w_mm2': area_weighted_average(g['heat_flux_w_mm2'], g['area_mm2'])
        })
    return pd.DataFrame(rows)


def calculate_improvements(summary: pd.DataFrame, baseline_case: str | None = None) -> pd.DataFrame:
    summary = summary.copy()
    if baseline_case is None:
        baseline_case = summary['case_id'].iloc[0]
    base = summary.loc[summary['case_id'] == baseline_case].iloc[0]
    summary['temperature_improvement_percent'] = summary['max_temperature_c'].apply(
        lambda value: -percent_change(base['max_temperature_c'], value)
    )
    summary['stress_improvement_percent'] = summary['max_stress_vm_mpa'].apply(
        lambda value: -percent_change(base['max_stress_vm_mpa'], value)
    )
    summary['displacement_improvement_percent'] = summary['max_displacement_mm'].apply(
        lambda value: -percent_change(base['max_displacement_mm'], value)
    )
    summary['heat_flow_change_percent'] = summary['total_heat_flow_w'].apply(
        lambda value: percent_change(base['total_heat_flow_w'], value)
    )
    return summary


def evaluate_block_average_error(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = df.copy()
    block_avg = (
        df.groupby(['case_id', 'block_id'])
        .apply(
            lambda g: (g['heat_flux_w_mm2'] * g['area_mm2']).sum() / g['area_mm2'].sum()
            if g['area_mm2'].sum() else np.nan,
            include_groups=False,
        )
        .rename('block_avg_heat_flux_w_mm2')
        .reset_index()
    )
    evaluated = df.merge(block_avg, on=['case_id', 'block_id'], how='left')
    evaluated['block_heat_flow_w'] = evaluated['block_avg_heat_flux_w_mm2'] * evaluated['area_mm2']
    evaluated['heat_flux_error_w_mm2'] = evaluated['block_avg_heat_flux_w_mm2'] - evaluated['heat_flux_w_mm2']
    evaluated['heat_flux_abs_error_w_mm2'] = evaluated['heat_flux_error_w_mm2'].abs()
    evaluated['heat_flux_relative_error_percent'] = np.where(
        evaluated['heat_flux_w_mm2'].abs() > 1e-12,
        100 * evaluated['heat_flux_error_w_mm2'] / evaluated['heat_flux_w_mm2'],
        np.nan,
    )
    rows = []
    for case_id, g in evaluated.groupby('case_id', sort=True):
        original_heat = g['heat_flow_w'].sum()
        block_heat = g['block_heat_flow_w'].sum()
        rows.append({
            'case_id': case_id,
            'original_total_heat_flow_w': original_heat,
            'block_total_heat_flow_w': block_heat,
            'heat_flow_conservation_percent': 100 * block_heat / original_heat if original_heat else np.nan,
            'mean_abs_heat_flux_error_w_mm2': g['heat_flux_abs_error_w_mm2'].mean(),
            'p95_abs_heat_flux_error_w_mm2': g['heat_flux_abs_error_w_mm2'].quantile(0.95),
            'max_abs_heat_flux_error_w_mm2': g['heat_flux_abs_error_w_mm2'].max(),
            'mean_abs_relative_error_percent': g['heat_flux_relative_error_percent'].abs().mean(),
            'max_abs_relative_error_percent': g['heat_flux_relative_error_percent'].abs().max(),
        })
    return evaluated, pd.DataFrame(rows)
