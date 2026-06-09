from pathlib import Path

from load_data import load_cases, load_criteria
from metrics import add_derived_columns, summarize_cases, calculate_improvements, evaluate_block_average_error
from decision_rules import add_judgement, recommend_best_case
from reporting import write_excel_report, write_markdown_report
from visualization import save_case_comparison_plots, save_risk_map

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data'
OUTPUT_DIR = ROOT / 'outputs'
CRITERIA_PATH = ROOT / 'config' / 'design_criteria.json'


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    criteria = load_criteria(CRITERIA_PATH)

    # 1) Load Nastran result files when a manifest exists; otherwise load sample CSV files.
    df = load_cases(DATA_DIR)

    # 2) Add derived engineering columns, such as heat flow and local safety factor.
    df = add_derived_columns(df, criteria)

    # 3) Summarize each design case and compare against the baseline case.
    summary = summarize_cases(df, criteria)
    summary = calculate_improvements(summary, baseline_case='case_01_baseline')
    summary = add_judgement(summary, criteria)

    # 4) Quantify error introduced by replacing fine heat-flux data with coarse block averages.
    block_eval, block_summary = evaluate_block_average_error(df)

    # 5) Extract risk elements for engineering review.
    risk_elements = df[
        df['temperature_exceeded'] | df['stress_exceeded'] | df['displacement_exceeded']
    ].copy()
    risk_elements = risk_elements.sort_values(
        ['case_id', 'temperature_c', 'stress_vm_mpa'], ascending=[True, False, False]
    )

    # 6) Write tabular outputs.
    summary.to_csv(OUTPUT_DIR / 'case_summary.csv', index=False)
    risk_elements.to_csv(OUTPUT_DIR / 'risk_elements.csv', index=False)
    block_eval.to_csv(OUTPUT_DIR / 'block_average_evaluated_elements.csv', index=False)
    block_summary.to_csv(OUTPUT_DIR / 'block_average_error_summary.csv', index=False)

    # 7) Write reports.
    recommendation = recommend_best_case(summary)
    write_excel_report(summary, block_summary, risk_elements, OUTPUT_DIR / 'design_review_report.xlsx')
    write_markdown_report(summary, block_summary, recommendation, OUTPUT_DIR / 'design_review_report.md')

    # 8) Save figures.
    save_case_comparison_plots(summary, OUTPUT_DIR)
    best_case = summary.sort_values(
        by=['design_status', 'max_temperature_c'],
        key=lambda s: s.map({'OK': 0, 'Warning': 1, 'NG': 2}) if s.name == 'design_status' else s
    ).iloc[0]['case_id']
    save_risk_map(df, OUTPUT_DIR, 'case_01_baseline', 'temperature_c', 'Baseline Temperature Map', 'baseline_temperature_map.png')
    save_risk_map(df, OUTPUT_DIR, best_case, 'temperature_c', f'{best_case} Temperature Map', 'recommended_case_temperature_map.png')

    print('CAE design review completed.')
    print(f'Report: {OUTPUT_DIR / "design_review_report.xlsx"}')
    print(f'Markdown summary: {OUTPUT_DIR / "design_review_report.md"}')


if __name__ == '__main__':
    main()
