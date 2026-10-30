"""Synthetic fixtures only: these values are not scientific protocols or results."""

import copy
import tempfile
import unittest
from pathlib import Path

from simulation_agent.core import CHECKS, Store, digest, load_json, plan, scientific_payload


def fixture(kind="dft"):
    spec = load_json(Path(__file__).parents[1] / "examples" / f"{kind}_draft.json")
    spec["mode"] = "synthetic"
    spec["protocol"] = {key: ("synthetic-placeholder" if value is None else value)
                        for key, value in spec["protocol"].items()}
    spec["protocol"]["status"] = "frozen"
    spec["system"] = {key: ("synthetic-placeholder" if value is None else value)
                      for key, value in spec["system"].items()}
    spec["system"]["identity_reviewed"] = True
    for c in spec["system"]["components"]:
        c["structure_id"] = "synthetic:" + c["identity"]
        if kind == "md":
            c["count"] = 1
    if kind == "md":
        spec["system"].update(temperature_k=300, seed=1, replica=0)
    spec["resources"] = {"cpus": 1, "memory_gb": 1, "walltime_hours": 1}
    return spec


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.test_root = (Path(__file__).parents[1] / "work" / "tests").resolve()
        self.test_root.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=self.test_root)
        self.root = Path(self.temp.name)
        self.path = self.root / "state.sqlite3"
        self.store = Store(self.path)
        self.artifact = self.root / "synthetic.log"
        self.artifact.write_text("SYNTHETIC TEST ONLY; no scientific data", encoding="utf-8")

    def tearDown(self):
        self.store.close()
        self.root.resolve().relative_to(self.test_root)
        self.temp.cleanup()

    def complete(self, kind="dft", checks=None):
        key = self.store.register(fixture(kind))
        self.store.start_synthetic(key)
        self.store.finish_synthetic(key, {c: True for c in CHECKS[kind]} if checks is None else checks,
                                    [self.artifact])
        return key

    def test_drafts_cannot_run(self):
        for kind in CHECKS:
            spec = load_json(Path(__file__).parents[1] / "examples" / f"{kind}_draft.json")
            self.assertEqual(plan(spec)["initial_state"], "NEEDS_REVIEW")
            self.assertFalse(plan(spec)["can_submit"])
            key = self.store.register(spec)
            with self.assertRaises(ValueError):
                self.store.start_synthetic(key)

    def test_persistence_and_source_deduplication(self):
        spec = fixture()
        key = self.store.register(spec)
        spec["sources"] = [{"paper_id": "second-paper"}]
        spec["label"] = "different label"
        spec["resources"]["cpus"] = 2
        self.assertEqual(self.store.register(spec), key)
        with Store(self.path) as reopened:
            self.assertEqual(len(reopened.list()), 1)
            self.assertEqual(len(reopened.get(key)["sources"]), 2)

    def test_component_order_does_not_duplicate(self):
        spec = fixture("md")
        other = copy.deepcopy(spec)
        other["system"]["components"].reverse()
        self.assertEqual(digest(scientific_payload(spec)), digest(scientific_payload(other)))

    def test_scientific_changes_make_new_key(self):
        for kind, container, field, value in (
            ("dft", "system", "charge", 2),
            ("dft", "system", "multiplicity", 3),
            ("dft", "system", "geometry_sha256", "other"),
            ("dft", "protocol", "basis", "other"),
            ("dft", "protocol", "engine_version", "other"),
            ("md", "system", "seed", 2),
            ("md", "system", "replica", 1),
            ("md", "system", "temperature_k", 310),
            ("md", "system", "concentration", "other"),
            ("md", "protocol", "parameter_hashes", "other"),
            ("md", "system", "polysulfide_state", "probe-Li2S6"),
        ):
            with self.subTest(kind=kind, field=field):
                spec = fixture(kind)
                before = plan(spec)["task_id"]
                spec[container][field] = value
                self.assertNotEqual(before, plan(spec)["task_id"])

    def test_synthetic_production_isolation(self):
        spec = fixture()
        synthetic_key = plan(spec)["task_id"]
        spec["mode"] = "production"
        key = self.store.register(spec)
        self.assertNotEqual(synthetic_key, key)
        with self.assertRaisesRegex(ValueError, "后端"):
            self.store.start_synthetic(key)

    def test_cannot_claim_twice(self):
        key = self.store.register(fixture())
        self.store.start_synthetic(key)
        with Store(self.path) as other:
            with self.assertRaises(ValueError):
                other.start_synthetic(key)
        self.assertEqual(self.store.get(key)["attempts"], 1)

    def test_retry_cap_and_audit(self):
        key = self.store.register(fixture())
        for attempt in range(2):
            self.store.start_synthetic(key)
            self.store.fail(key, "synthetic scheduler interruption")
            if attempt == 0:
                self.store.retry(key, "same inputs")
        with self.assertRaises(ValueError):
            self.store.retry(key, "over cap")
        self.assertEqual(self.store.get(key)["attempts"], 2)
        self.assertEqual(self.store.get(key)["state"], "FAILED")

    def test_running_task_survives_reopen_without_resubmission(self):
        key = self.store.register(fixture())
        self.store.start_synthetic(key)
        with Store(self.path) as other:
            self.assertEqual(other.get(key)["state"], "RUNNING")
            with self.assertRaises(ValueError):
                other.retry(key, "cannot blindly resubmit live job")

    def test_execution_success_is_not_qc_pass(self):
        key = self.complete()
        self.assertEqual(self.store.get(key)["state"], "SUCCEEDED_PENDING_QC")
        self.assertIsNone(self.store.cached(key))
        self.assertEqual(self.store.qc(key), "PASSED")
        self.assertTrue(self.store.cached(key)["not_scientific_data"])

    def test_md_qc_pass(self):
        self.assertEqual(self.store.qc(self.complete("md")), "PASSED")

    def test_missing_qc_goes_to_review(self):
        key = self.complete(checks={"electronic_convergence": True})
        self.assertEqual(self.store.qc(key), "NEEDS_REVIEW")
        self.assertIsNone(self.store.cached(key))
        with self.assertRaises(ValueError):
            self.store.retry(key, "cannot retry scientific failure automatically")

    def test_string_true_is_not_pass(self):
        key = self.complete(checks={c: "true" for c in CHECKS["dft"]})
        self.assertEqual(self.store.qc(key), "NEEDS_REVIEW")

    def test_artifact_tampering_before_qc(self):
        key = self.complete()
        self.artifact.write_text("changed", encoding="utf-8")
        self.assertEqual(self.store.qc(key), "NEEDS_REVIEW")

    def test_artifact_tampering_after_qc_invalidates_cache(self):
        key = self.complete()
        self.store.qc(key)
        self.artifact.write_text("changed", encoding="utf-8")
        self.assertIsNone(self.store.cached(key))
        self.assertEqual(self.store.get(key)["state"], "NEEDS_REVIEW")

    def test_missing_artifact_rejects_completion(self):
        key = self.store.register(fixture())
        self.store.start_synthetic(key)
        with self.assertRaises(ValueError):
            self.store.finish_synthetic(key, {}, [])
        self.assertEqual(self.store.get(key)["state"], "RUNNING")

    def test_invalid_retry_policy_rejected(self):
        for value in (0, 6, True, -1, 1.5):
            spec = fixture()
            spec["retry_policy"]["max_attempts"] = value
            with self.assertRaises(ValueError):
                plan(spec)

    def test_duplicate_components_rejected(self):
        spec = fixture()
        spec["system"]["components"].append(spec["system"]["components"][0])
        with self.assertRaises(ValueError):
            plan(spec)

    def test_nan_rejected(self):
        spec = fixture()
        spec["resources"]["cpus"] = float("nan")
        with self.assertRaises(ValueError):
            plan(spec)

    def test_resource_bound_includes_retries(self):
        self.assertEqual(plan(fixture())["reserved_cpu_hours_upper_bound"], 2)


if __name__ == "__main__":
    unittest.main()
