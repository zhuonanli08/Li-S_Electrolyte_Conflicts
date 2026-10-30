"""Invented log fragments test rejection logic; these are not engine results."""

import hashlib
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from simulation_agent.frequency_qc import inspect_frequency, inspect_frequency_files
from simulation_agent.__main__ import main


class FrequencyScreenTests(unittest.TestCase):
    def spec(self):
        return {"atom_count": 3, "linear": False, "charge": 0, "multiplicity": 1,
                "route": "B3LYP/6-31+G* Freq EmpiricalDispersion=GD3",
                "reference_energy_hartree": -76.0, "energy_tolerance_hartree": 1e-5}

    def log(self):
        return ("Gaussian 16: ES64L-G16RevC.01\n"
                " -------------------\n # B3LYP/6-31+G* Freq\n EmpiricalDispersion=GD3\n -------------------\n"
                " Charge = 0 Multiplicity = 1\n NAtoms= 3\n"
                " SCF Done: E(RB3LYP) = -76.000000000 A.U.\n"
                " Harmonic frequencies (cm**-1), IR intensities\n"
                " Low frequencies --- -0.0002 0.0001 0.0002\n"
                "                      1 2 3\n                      A A A\n"
                " Frequencies -- 100.0 200.0 300.0\n"
                " Normal termination of Gaussian 16\n")

    def test_screen_success_never_scientific_pass(self):
        result = inspect_frequency(self.log(), self.spec())
        self.assertEqual(result['status'], 'SCREEN_PASSED_PENDING_REVIEW')
        self.assertFalse(result['usable_for_analysis'])
        self.assertEqual(result['scientific_qc'], 'PENDING_REVIEW')
        self.assertEqual(result['frequencies'], [100, 200, 300])

    def test_d_notation(self):
        result = inspect_frequency(self.log().replace('100.0', '1.0D+02'), self.spec())
        self.assertEqual(result['frequencies'][0], 100)

    def test_imaginary_even_small_requires_review(self):
        result = inspect_frequency(self.log().replace('100.0', '-0.01'), self.spec())
        self.assertEqual(result['status'], 'NEEDS_REVIEW')

    def test_zero_requires_review(self):
        self.assertEqual(inspect_frequency(self.log().replace('100.0', '0.0'), self.spec())['status'], 'NEEDS_REVIEW')

    def test_missing_duplicate_disordered_modes(self):
        for modes in ('1 2', '1 2 2', '3 2 1'):
            with self.subTest(modes=modes):
                self.assertEqual(inspect_frequency(self.log().replace('1 2 3', modes), self.spec())['status'], 'NEEDS_REVIEW')

    def test_malformed_or_nonfinite_frequency(self):
        for token in ('********', 'NaN', 'Infinity', '1.0D+999'):
            with self.subTest(token=token):
                result = inspect_frequency(self.log().replace('100.0', token), self.spec())
                self.assertEqual(result['status'], 'NEEDS_REVIEW')
                self.assertIn('frequency_rows_parseable', result['issues'])

    def test_normal_termination_without_frequencies(self):
        text = self.log().replace(' Frequencies -- 100.0 200.0 300.0\n', '')
        self.assertEqual(inspect_frequency(text, self.spec())['status'], 'NEEDS_REVIEW')

    def test_wrong_identity_or_route(self):
        for old, new in [('NAtoms= 3', 'NAtoms= 4'), ('Charge = 0', 'Charge = 1'),
                         ('Multiplicity = 1', 'Multiplicity = 3'), ('GD3', 'GD3BJ'),
                         ('Harmonic frequencies', 'Anharmonic frequencies')]:
            with self.subTest(old=old):
                self.assertEqual(inspect_frequency(self.log().replace(old, new), self.spec())['status'], 'NEEDS_REVIEW')

    def test_truncated_error_or_concatenated_logs(self):
        for text in (self.log().replace('Normal termination of Gaussian 16', ''),
                     self.log() + 'Error termination\n', self.log() * 2):
            self.assertEqual(inspect_frequency(text, self.spec())['status'], 'NEEDS_REVIEW')

    def test_reference_mismatch(self):
        result = inspect_frequency(self.log().replace('-76.000000000', '-76.001'), self.spec())
        self.assertIn('reference_energy_within_investigation_threshold', result['issues'])

    def test_linear_molecule_requires_3n_minus_5(self):
        spec = self.spec()
        spec['linear'] = True
        self.assertIn('complete_unique_ordered_modes', inspect_frequency(self.log(), spec)['issues'])

    def test_dme_requires_all_42_modes(self):
        spec = self.spec()
        spec['atom_count'] = 16
        text = self.log().replace('NAtoms= 3', 'NAtoms= 16')
        block = ''.join(f' {i} {i+1} {i+2}\n A A A\n Frequencies -- 100.0 200.0 300.0\n'
                        for i in range(1, 43, 3))
        start = text.index('                      1 2 3')
        text = text[:start] + block + ' Normal termination of Gaussian 16\n'
        result = inspect_frequency(text, spec)
        self.assertEqual(len(result['frequencies']), 42)
        self.assertEqual(result['status'], 'SCREEN_PASSED_PENDING_REVIEW')
        self.assertEqual(inspect_frequency(text.replace(' 40 41 42', ' 37 38 39'), spec)['status'], 'NEEDS_REVIEW')

    def test_invalid_expected_values(self):
        for key, value in [('atom_count', True), ('linear', None), ('multiplicity', 0),
                           ('energy_tolerance_hartree', -1), ('reference_energy_hartree', float('nan'))]:
            spec = self.spec()
            spec[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                inspect_frequency(self.log(), spec)

    def test_provenance_and_modified_input(self):
        root = Path(__file__).resolve().parents[1] / 'work' / 'tests'
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as folder:
            log, inp = Path(folder) / 'synthetic.log', Path(folder) / 'synthetic.gjf'
            log.write_text(self.log(), encoding='utf-8')
            inp.write_bytes(b'synthetic input')
            spec = self.spec()
            spec['input_sha256'] = hashlib.sha256(inp.read_bytes()).hexdigest()
            result = inspect_frequency_files(log, inp, spec, 'synthetic')
            self.assertEqual(result['mode'], 'synthetic')
            self.assertEqual(result['provenance']['log_sha256'], hashlib.sha256(log.read_bytes()).hexdigest())
            inp.write_bytes(b'changed')
            self.assertEqual(inspect_frequency_files(log, inp, spec, 'synthetic')['status'], 'NEEDS_REVIEW')
            with self.assertRaises(ValueError):
                inspect_frequency_files(log, inp, spec, 'unknown')

    def test_cli_report_exit_status_and_no_overwrite(self):
        root = Path(__file__).resolve().parents[1] / 'work' / 'tests'
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as folder:
            folder = Path(folder)
            log, inp, config, out = [folder / name for name in ('synthetic.log', 'synthetic.gjf', 'screen.json', 'report.json')]
            log.write_text(self.log(), encoding='utf-8')
            inp.write_bytes(b'synthetic input')
            spec = self.spec()
            spec['input_sha256'] = hashlib.sha256(inp.read_bytes()).hexdigest()
            config.write_text(json.dumps(spec), encoding='utf-8')
            args = ['inspect-frequency', str(config), str(log), '--input', str(inp),
                    '--mode', 'synthetic', '--out', str(out)]
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(args), 0)
                preserved = out.read_bytes()
                self.assertEqual(main(args), 2)
                self.assertEqual(out.read_bytes(), preserved)
                log.write_text(self.log().replace('100.0', '-1.0'), encoding='utf-8')
                args[-1] = str(folder / 'failed-screen.json')
                self.assertEqual(main(args), 3)
            self.assertEqual(json.loads(Path(args[-1]).read_text(encoding='utf-8'))['status'], 'NEEDS_REVIEW')


if __name__ == '__main__':
    unittest.main()
