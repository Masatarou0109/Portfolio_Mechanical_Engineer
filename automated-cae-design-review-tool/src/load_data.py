from pathlib import Path
import json
import pandas as pd

from nastran_reader import load_nastran_cases

REQUIRED_COLUMNS = {
    'case_id', 'element_id', 'x_mm', 'y_mm', 'area_mm2',
    'stress_vm_mpa', 'displacement_mm', 'temperature_c',
    'heat_flux_w_mm2', 'block_id'
}


def load_criteria(path: str | Path) -> dict:
    path = Path(path)
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def load_case_csv(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    df = pd.read_csv(path)
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f'{path.name} is missing required columns: {sorted(missing)}')
    df['source_file'] = path.name
    return df


def load_cases(data_dir: str | Path) -> pd.DataFrame:
    data_dir = Path(data_dir)
    nastran_manifest = data_dir / 'nastran_cases.csv'
    if nastran_manifest.exists():
        return load_nastran_cases(nastran_manifest)

    files = sorted(data_dir.glob('case_*.csv'))
    if not files:
        raise FileNotFoundError(f'No nastran_cases.csv or case_*.csv files found in {data_dir}')
    frames = [load_case_csv(path) for path in files]
    return pd.concat(frames, ignore_index=True)
