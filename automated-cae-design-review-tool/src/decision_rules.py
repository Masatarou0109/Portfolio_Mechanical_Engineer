import pandas as pd


def judge_case(row: pd.Series, criteria: dict) -> tuple[str, str]:
    reasons = []
    severe = False
    warning = False

    if row['max_temperature_c'] > criteria['temperature_limit_c']:
        reasons.append(f"Max temperature {row['max_temperature_c']:.1f} C exceeds limit {criteria['temperature_limit_c']:.1f} C")
        severe = True
    elif row['max_temperature_c'] > criteria['temperature_warning_c']:
        reasons.append(f"Max temperature {row['max_temperature_c']:.1f} C is above warning level {criteria['temperature_warning_c']:.1f} C")
        warning = True

    if row['temperature_exceeded_area_percent'] > criteria['max_exceeded_area_percent_warning']:
        reasons.append(f"Temperature exceedance area {row['temperature_exceeded_area_percent']:.2f}% is too wide")
        severe = True
    elif row['temperature_exceeded_area_percent'] > criteria['max_exceeded_area_percent_ok']:
        reasons.append(f"Temperature exceedance area {row['temperature_exceeded_area_percent']:.2f}% requires review")
        warning = True

    if row['max_stress_vm_mpa'] > criteria['stress_allowable_mpa']:
        reasons.append(f"Max von Mises stress {row['max_stress_vm_mpa']:.1f} MPa exceeds allowable {criteria['stress_allowable_mpa']:.1f} MPa")
        severe = True

    if row['minimum_safety_factor'] < criteria['minimum_safety_factor']:
        reasons.append(f"Minimum safety factor {row['minimum_safety_factor']:.2f} is below target {criteria['minimum_safety_factor']:.2f}")
        severe = True

    if row['max_displacement_mm'] > criteria['displacement_limit_mm']:
        reasons.append(f"Max displacement {row['max_displacement_mm']:.3f} mm exceeds limit {criteria['displacement_limit_mm']:.3f} mm")
        severe = True

    if severe:
        status = 'NG'
    elif warning:
        status = 'Warning'
    else:
        status = 'OK'
        reasons.append('All primary criteria are within target limits')
    return status, '; '.join(reasons)


def add_judgement(summary: pd.DataFrame, criteria: dict) -> pd.DataFrame:
    summary = summary.copy()
    judgements = summary.apply(lambda row: judge_case(row, criteria), axis=1)
    summary['design_status'] = [j[0] for j in judgements]
    summary['decision_comment'] = [j[1] for j in judgements]
    return summary


def recommend_best_case(summary: pd.DataFrame) -> str:
    ranked = summary.copy()
    status_rank = {'OK': 0, 'Warning': 1, 'NG': 2}
    ranked['status_rank'] = ranked['design_status'].map(status_rank).fillna(3)
    ranked = ranked.sort_values(
        by=['status_rank', 'max_temperature_c', 'max_stress_vm_mpa', 'max_displacement_mm'],
        ascending=[True, True, True, True]
    )
    best = ranked.iloc[0]
    return (
        f"Recommended case: {best['case_id']} ({best['description']}). "
        f"Status: {best['design_status']}. "
        f"Max temperature = {best['max_temperature_c']:.1f} C, "
        f"max stress = {best['max_stress_vm_mpa']:.1f} MPa, "
        f"max displacement = {best['max_displacement_mm']:.3f} mm."
    )
