import hashlib
import tempfile
import unittest
from pathlib import Path

from simulation_agent.combat_benchmark import check, finite, literal_assignment, sum_duplicate_column, verify_sources


class ComBatAuditTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1] / "work" / "tests"
        root.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=root)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_duplicate_atomic_sites_are_summed(self):
        path = self.root / "cn.csv"
        path.write_text(',O (DME),O (DME),O (TFSI)\n0,1.5,1.6,0.1\n')
        self.assertAlmostEqual(sum_duplicate_column(path, "O (DME)"), 3.1)

    def test_missing_species_fails_instead_of_zero(self):
        path = self.root / "cn.csv"
        path.write_text(',O (DME)\n0,1.5\n')
        with self.assertRaises(ValueError):
            sum_duplicate_column(path, "S out (PS)")

    def test_multiple_rows_not_silently_discarded(self):
        path = self.root / "cn.csv"
        path.write_text(',O (DME)\n0,1.5\n1,1.6\n')
        with self.assertRaises(ValueError):
            sum_duplicate_column(path, "O (DME)")

    def test_nonfinite_values_rejected(self):
        for value in ('NaN', 'inf', '-inf'):
            with self.assertRaises(ValueError):
                finite(value)

    def test_unit_scale_mismatch_is_not_passed(self):
        self.assertFalse(check('diffusion', 2.5e-6, 2.5e-10, 'm2/s', 1e-18)['passed'])

    def test_changed_reference_rejected(self):
        path = self.root / "raw.json"
        path.write_bytes(b'original')
        lock = {'files': [{'path': 'raw.json', 'sha256': hashlib.sha256(b'original').hexdigest()}]}
        verify_sources(self.root, lock)
        path.write_bytes(b'modified')
        with self.assertRaises(ValueError):
            verify_sources(self.root, lock)

    def test_author_script_is_parsed_without_execution(self):
        path = self.root / "author.py"
        path.write_text("raise RuntimeError('must never execute')\nsettings = {'route': 'GD3'}\n")
        self.assertEqual(literal_assignment(path, 'settings'), {'route': 'GD3'})

    def test_nonliteral_settings_are_not_executed(self):
        path = self.root / "author.py"
        path.write_text("settings = dict(route='GD3')\n")
        with self.assertRaises(ValueError):
            literal_assignment(path, 'settings')


if __name__ == '__main__':
    unittest.main()
