import copy
import unittest

from simulation_agent.analysis import binding_energy
from simulation_agent.engines import coordinates, inspect_log, render_dft
from simulation_agent.scheduler import render_slurm


class EngineTests(unittest.TestCase):
    def test_gaussian_input_charge_and_spin(self):
        text = render_dft("gaussian", [{"element": "Li", "xyz_angstrom": [0, 0, 0]}], 1, 1,
                          "B3LYP/6-31G(d) SP", 2, 2)
        self.assertIn("%nprocshared=2", text)
        self.assertIn("\n1 1\nLi", text)

    def test_orca_input_resources(self):
        text = render_dft("orca", [{"element": "Li", "xyz_angstrom": [0, 0, 0]}], 1, 1,
                          "B3LYP def2-SVP SP", 2, 2)
        self.assertIn("%maxcore 768", text)
        self.assertIn("* xyz 1 1", text)

    def test_wrong_electron_parity(self):
        with self.assertRaises(ValueError):
            coordinates([{"element": "Li", "xyz_angstrom": [0, 0, 0]}], 0, 1)

    def test_input_section_injection_rejected(self):
        with self.assertRaises(ValueError):
            render_dft("gaussian", [{"element": "Li", "xyz_angstrom": [0, 0, 0]}], 1, 1,
                       "B3LYP/6-31G(d)\n--Link1--", 2, 2)

    def test_gaussian_normal_exit_not_scientific_pass(self):
        parsed = inspect_log("gaussian", "SCF Done: E(RB3LYP) = -7.200D+00 A.U.\nNormal termination of Gaussian 16")
        self.assertEqual(parsed["energy_hartree"], -7.2)
        self.assertEqual(parsed["status"], "SUCCESS_PENDING_QC")
        self.assertFalse(parsed["usable_for_analysis"])

    def test_gaussian_error_after_scf(self):
        parsed = inspect_log("gaussian", "SCF Done: E(RB3LYP) = -7.2 A.U.\nError termination")
        self.assertEqual(parsed["status"], "EXECUTION_FAILED")
        self.assertIsNone(parsed["energy_hartree"])

    def test_geometry_missing_is_review(self):
        parsed = inspect_log("gaussian", "SCF Done: E(RB3LYP) = -7.2 A.U.\nNormal termination of Gaussian 16", True)
        self.assertEqual(parsed["status"], "NEEDS_REVIEW")

    def test_unfinished_append_rejected(self):
        parsed = inspect_log("gaussian", "SCF Done: E(RB3LYP) = -7.2 A.U.\nNormal termination of Gaussian 16\nEntering Gaussian System")
        self.assertEqual(parsed["status"], "INCOMPLETE")

    def test_orca_energy(self):
        parsed = inspect_log("orca", "THE OPTIMIZATION HAS CONVERGED\nFINAL SINGLE POINT ENERGY -10.0\n****ORCA TERMINATED NORMALLY****\nTOTAL RUN TIME: 1 seconds", True)
        self.assertEqual(parsed["status"], "SUCCESS_PENDING_QC")

    def test_lammps_steps_checked(self):
        text = "Loop time of 1 on 1 procs for 100 steps with 10 atoms\nTotal wall time: 0:00:01"
        self.assertEqual(inspect_log("lammps", text, expected_steps=[100])["status"], "SUCCESS_PENDING_QC")
        self.assertEqual(inspect_log("lammps", text, expected_steps=[200])["status"], "NEEDS_REVIEW")
        self.assertEqual(inspect_log("lammps", text)["status"], "NEEDS_REVIEW")

    def test_lammps_lost_atoms_rejected(self):
        parsed = inspect_log("lammps", "WARNING: Lost atoms\nTotal wall time: 0:00:01", expected_steps=[])
        self.assertEqual(parsed["status"], "EXECUTION_FAILED")


class SchedulerTests(unittest.TestCase):
    def config(self):
        return {"job_name": "test", "partition": "synthetic", "account": "synthetic", "cpus": 2,
                "memory_mb": 2048, "walltime_minutes": 30, "billing_verified": True,
                "billing": {"unit": "cpu_core_hour", "price_per_unit_hour": 1, "currency": "CNY"},
                "billable_units": 2, "approved_cap": 2, "engine": "gaussian",
                "executable": "/synthetic/g16", "input_file": "input.gjf", "modules": ["gaussian/test"]}

    def test_bounded_script(self):
        text = render_slurm(self.config())
        self.assertIn("#SBATCH --time=30", text)
        self.assertNotIn("--exclusive", text)
        self.assertIn("Existing engine.log", text)

    def test_unknown_price_or_excess_blocked(self):
        for key, value in (("billing_verified", False), ("approved_cap", None), ("approved_cap", 0.1)):
            config = self.config()
            config[key] = value
            with self.assertRaises(ValueError):
                render_slurm(config)

    def test_directive_injection_rejected(self):
        config = self.config()
        config["partition"] = "test\n#SBATCH --exclusive"
        with self.assertRaises(ValueError):
            render_slurm(config)

    def test_unknown_mpi_launch_blocked(self):
        config = self.config()
        config["engine"] = "lammps"
        with self.assertRaises(ValueError):
            render_slurm(config)

    def test_cannot_understate_billable_cores(self):
        config = self.config()
        config["billable_units"] = 1
        with self.assertRaises(ValueError):
            render_slurm(config)


class EnergyTests(unittest.TestCase):
    def energy(self, value, formula, charge=0):
        return {"electronic_energy": value, "unit": "hartree", "geometry_basis": "isolated_optimized",
                "mode": "synthetic", "qc_status": "PASSED", "protocol_hash": "test",
                "source_sha256": "synthetic", "charge": charge, "formula": formula}

    def test_stoichiometric_binding(self):
        result = binding_energy(self.energy(-3, {"H": 2}),
                                [{"coefficient": 2, "result": self.energy(-1, {"H": 1})}])
        self.assertEqual(result["value"], -1)
        self.assertEqual(result["qc_status"], "DERIVED_PENDING_REVIEW")

    def test_nonconservation_rejected(self):
        with self.assertRaises(ValueError):
            binding_energy(self.energy(-3, {"H": 2}),
                           [{"coefficient": 1, "result": self.energy(-1, {"H": 1})}])

    def test_mixed_protocol_and_units_rejected(self):
        for key, value in (("unit", "eV"), ("protocol_hash", "other"), ("mode", "production"),
                           ("qc_status", "SUCCESS_PENDING_QC"), ("geometry_basis", "frozen_in_complex")):
            fragment = self.energy(-1, {"H": 1})
            fragment[key] = value
            with self.assertRaises(ValueError):
                binding_energy(self.energy(-3, {"H": 2}), [{"coefficient": 2, "result": fragment}])
