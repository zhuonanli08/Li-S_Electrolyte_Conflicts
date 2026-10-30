import copy
import tempfile
import unittest
from pathlib import Path

from simulation_agent.core import load_json
from simulation_agent.workflow import WorkflowRun, build_workflow, validate_graph


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.base = (Path(__file__).parents[1] / "work" / "tests").resolve()
        self.base.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=self.base)
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.root.resolve().relative_to(self.base)
        self.temp.cleanup()

    def workflow(self, kind="dft", mode="synthetic"):
        spec = load_json(Path(__file__).parents[1] / "examples" / f"{kind}_draft.json")
        spec["mode"] = mode
        return build_workflow(spec)

    def test_both_end_to_end(self):
        for kind in ("dft", "md"):
            with WorkflowRun(self.workflow(kind), self.root) as run:
                report = run.run_synthetic()
                self.assertEqual(report["status"], "DRY_RUN_PASSED")
                self.assertEqual(report["scientific_results"], 0)
                self.assertEqual(report["real_jobs_submitted"], 0)

    def test_failure_blocks_dependents_and_resume_preserves_completed_work(self):
        wf = self.workflow()
        with WorkflowRun(wf, self.root) as run:
            first = run.run_synthetic(fail_at="opt_complex")
            self.assertEqual(first["stages"]["opt_complex"]["status"], "FAILED")
            self.assertEqual(first["stages"]["geometry_qc"]["status"], "PENDING")
            self.assertEqual(first["stages"]["opt_fragments"]["status"], "DRY_RUN_PASSED")
        with WorkflowRun(wf, self.root) as run:
            run.retry("opt_complex", "synthetic recovery test")
            second = run.run_synthetic()
            self.assertEqual(second["status"], "DRY_RUN_PASSED")
            self.assertEqual(second["stages"]["opt_complex"]["attempts"], 2)
            self.assertEqual(second["stages"]["opt_fragments"]["attempts"], 1)

    def test_artifact_change_invalidates_descendants(self):
        with WorkflowRun(self.workflow(), self.root) as run:
            result = run.run_synthetic()
            (run.root / result["stages"]["energy_complex"]["artifact"]).write_text("changed", encoding="utf-8")
            report = run.run_synthetic()
            self.assertEqual(report["stages"]["archive"]["status"], "NEEDS_REVIEW")
            self.assertEqual(report["stages"]["energy_fragments"]["status"], "DRY_RUN_PASSED")

    def test_production_never_runs_as_mock(self):
        with WorkflowRun(self.workflow(mode="production"), self.root) as run:
            with self.assertRaises(ValueError):
                run.run_synthetic()

    def test_definition_tampering_rejected(self):
        workflow = self.workflow()
        workflow["stages"][0]["operation"] = "changed"
        with self.assertRaises(ValueError):
            WorkflowRun(workflow, self.root)

    def test_cycles_rejected(self):
        workflow = self.workflow()
        workflow["stages"][0]["depends_on"] = ["archive"]
        with self.assertRaises(ValueError):
            validate_graph(workflow)

    def test_rerun_does_not_repeat_finished_stages(self):
        with WorkflowRun(self.workflow(), self.root) as run:
            run.run_synthetic()
            result = run.run_synthetic()
            self.assertTrue(all(row["attempts"] == 1 for row in result["stages"].values()))

    def test_retry_limit(self):
        with WorkflowRun(self.workflow(), self.root) as run:
            run.run_synthetic("opt_complex")
            run.retry("opt_complex", "test")
            run.run_synthetic("opt_complex")
            with self.assertRaises(ValueError):
                run.retry("opt_complex", "third attempt")

    def test_replica_count_changes_workflow_identity(self):
        spec = load_json(Path(__file__).parents[1] / "examples" / "md_draft.json")
        self.assertNotEqual(build_workflow(spec, 2)["workflow_id"], build_workflow(spec, 3)["workflow_id"])
