import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from nastran_reader import load_bdf_geometry, load_nastran_cases, parse_nastran_number


class TestNastranReader(unittest.TestCase):
    def test_parse_nastran_number_accepts_d_exponents(self):
        self.assertAlmostEqual(parse_nastran_number('1.25D+02'), 125.0)

    def test_demo_bdf_geometry_has_expected_shell_elements(self):
        geometry = load_bdf_geometry(PROJECT_ROOT / 'data' / 'nastran_demo' / 'demo_model.bdf')

        self.assertEqual(list(geometry['element_id']), [101, 102])
        self.assertAlmostEqual(float(geometry.loc[0, 'area_mm2']), 100.0)
        self.assertAlmostEqual(float(geometry.loc[1, 'area_mm2']), 100.0)

    def test_demo_nastran_manifest_loads_review_columns(self):
        df = load_nastran_cases(PROJECT_ROOT / 'data' / 'nastran_cases.example.csv')

        self.assertEqual(len(df), 4)
        self.assertIn('stress_vm_mpa', df.columns)
        self.assertIn('temperature_c', df.columns)
        self.assertGreater(df['stress_vm_mpa'].max(), 180.0)
        self.assertGreater(df['temperature_c'].max(), 100.0)


if __name__ == '__main__':
    unittest.main()
