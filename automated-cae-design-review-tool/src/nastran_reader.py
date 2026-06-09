from pathlib import Path
import math
import re

import numpy as np
import pandas as pd


NASTRAN_CASE_COLUMNS = {
    'case_id',
    'bdf_path',
    'result_path',
}

NUMBER_RE = re.compile(r'[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[EDed][-+]?\d+)?')


def parse_nastran_number(value: str) -> float:
    return float(value.replace('D', 'E').replace('d', 'e'))


def split_bulk_fields(line: str) -> list[str]:
    content = line.split('$', 1)[0].strip()
    if not content:
        return []
    if ',' in content:
        return [field.strip() for field in content.split(',')]
    return content.split()


def triangle_area(p1: np.ndarray, p2: np.ndarray, p3: np.ndarray) -> float:
    return float(0.5 * np.linalg.norm(np.cross(p2 - p1, p3 - p1)))


def polygon_area(points: list[np.ndarray]) -> float:
    if len(points) == 3:
        return triangle_area(points[0], points[1], points[2])
    if len(points) == 4:
        return triangle_area(points[0], points[1], points[2]) + triangle_area(points[0], points[2], points[3])
    return np.nan


def load_bdf_geometry(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    grids: dict[int, np.ndarray] = {}
    elements: dict[int, list[int]] = {}

    with path.open('r', encoding='utf-8', errors='ignore') as f:
        for raw_line in f:
            fields = split_bulk_fields(raw_line)
            if not fields:
                continue
            card = fields[0].upper().rstrip('*')
            if card == 'GRID' and len(fields) >= 6:
                grid_id = int(fields[1])
                grids[grid_id] = np.array([
                    parse_nastran_number(fields[3]),
                    parse_nastran_number(fields[4]),
                    parse_nastran_number(fields[5]),
                ])
            elif card == 'CTRIA3' and len(fields) >= 6:
                elements[int(fields[1])] = [int(fields[3]), int(fields[4]), int(fields[5])]
            elif card == 'CQUAD4' and len(fields) >= 7:
                elements[int(fields[1])] = [int(fields[3]), int(fields[4]), int(fields[5]), int(fields[6])]

    rows = []
    for element_id, grid_ids in sorted(elements.items()):
        points = [grids[grid_id] for grid_id in grid_ids if grid_id in grids]
        if len(points) != len(grid_ids):
            continue
        centroid = np.mean(points, axis=0)
        rows.append({
            'element_id': element_id,
            'x_mm': float(centroid[0]),
            'y_mm': float(centroid[1]),
            'area_mm2': polygon_area(points),
            'block_id': max(1, element_id // 100),
            'grid_ids': tuple(grid_ids),
        })

    if not rows:
        raise ValueError(f'No supported shell elements were found in {path.name}')
    return pd.DataFrame(rows)


def numbers_from_line(line: str) -> list[float]:
    return [parse_nastran_number(match.group(0)) for match in NUMBER_RE.finditer(line)]


def first_integer_token(line: str) -> int | None:
    tokens = [int(token) for token in re.findall(r'[-+]?\d+', line)]
    if not tokens:
        return None
    if tokens[0] == 0 and len(tokens) > 1:
        return tokens[1]
    return tokens[0]


def parse_result_line(line: str, mode: str | None) -> tuple[int, float] | None:
    values = numbers_from_line(line)
    if not mode or len(values) < 2:
        return None

    entity_id = first_integer_token(line)
    if entity_id is None:
        return None

    if mode == 'displacement':
        if len(values) >= 4:
            offset = 2 if values[0] == 0 and len(values) >= 5 else 1
            return entity_id, math.sqrt(values[offset] ** 2 + values[offset + 1] ** 2 + values[offset + 2] ** 2)
        return None
    if mode in {'temperature', 'stress', 'heat_flux'}:
        return entity_id, values[-1]
    return None


def load_nastran_text_results(path: str | Path) -> dict[str, dict[int, float]]:
    path = Path(path)
    results = {
        'grid_displacement_mm': {},
        'grid_temperature_c': {},
        'element_stress_vm_mpa': {},
        'element_heat_flux_w_mm2': {},
    }
    mode: str | None = None

    with path.open('r', encoding='utf-8', errors='ignore') as f:
        for raw_line in f:
            line = raw_line.strip()
            upper = line.upper()
            if not line:
                continue
            compact_upper = upper.replace(' ', '')
            if 'DISPLACEMENTVECTOR' in compact_upper or upper.startswith('$DISPLACEMENT'):
                mode = 'displacement'
                continue
            if 'TEMPERATURE' in upper and ('GRID' in upper or upper.startswith('$TEMP')):
                mode = 'temperature'
                continue
            if 'VON MISES' in upper or 'VON_MISES' in upper or upper.startswith('$ELEMENT_STRESS'):
                mode = 'stress'
                continue
            if 'HEAT FLUX' in upper or 'HEAT_FLUX' in upper or upper.startswith('$ELEMENT_HEAT'):
                mode = 'heat_flux'
                continue
            if upper.startswith(('PAGE', 'SUBCASE', 'LOAD STEP')):
                continue

            parsed = parse_result_line(line, mode)
            if parsed is None:
                continue
            entity_id, value = parsed
            if mode == 'displacement':
                results['grid_displacement_mm'][entity_id] = value
            elif mode == 'temperature':
                results['grid_temperature_c'][entity_id] = value
            elif mode == 'stress':
                results['element_stress_vm_mpa'][entity_id] = value
            elif mode == 'heat_flux':
                results['element_heat_flux_w_mm2'][entity_id] = value

    return results


def average_grid_result(grid_ids: tuple[int, ...], values: dict[int, float]) -> float:
    grid_values = [values[grid_id] for grid_id in grid_ids if grid_id in values]
    return float(np.mean(grid_values)) if grid_values else np.nan


def load_nastran_case(case: pd.Series, base_dir: Path) -> pd.DataFrame:
    bdf_path = base_dir / str(case['bdf_path'])
    result_path = base_dir / str(case['result_path'])
    geometry = load_bdf_geometry(bdf_path)
    results = load_nastran_text_results(result_path)

    rows = []
    for _, element in geometry.iterrows():
        element_id = int(element['element_id'])
        grid_ids = element['grid_ids']
        rows.append({
            'case_id': case['case_id'],
            'case_description': case.get('case_description', ''),
            'element_id': element_id,
            'x_mm': element['x_mm'],
            'y_mm': element['y_mm'],
            'area_mm2': element['area_mm2'],
            'stress_vm_mpa': results['element_stress_vm_mpa'].get(element_id, np.nan),
            'displacement_mm': average_grid_result(grid_ids, results['grid_displacement_mm']),
            'temperature_c': average_grid_result(grid_ids, results['grid_temperature_c']),
            'heat_flux_w_mm2': results['element_heat_flux_w_mm2'].get(element_id, 0.0),
            'block_id': element['block_id'],
            'source_file': result_path.name,
        })

    df = pd.DataFrame(rows)
    required_results = ['stress_vm_mpa', 'displacement_mm', 'temperature_c']
    missing = [column for column in required_results if df[column].isna().all()]
    if missing:
        raise ValueError(f'{result_path.name} does not contain readable result columns: {missing}')
    return df


def load_nastran_cases(manifest_path: str | Path) -> pd.DataFrame:
    manifest_path = Path(manifest_path)
    manifest = pd.read_csv(manifest_path)
    missing = NASTRAN_CASE_COLUMNS - set(manifest.columns)
    if missing:
        raise ValueError(f'{manifest_path.name} is missing required columns: {sorted(missing)}')

    frames = [load_nastran_case(case, manifest_path.parent) for _, case in manifest.iterrows()]
    return pd.concat(frames, ignore_index=True)
