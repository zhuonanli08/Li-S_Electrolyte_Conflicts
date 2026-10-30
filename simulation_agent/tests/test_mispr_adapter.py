import copy
import unittest

from simulation_agent.mispr_adapter import DEFAULT_SOURCE, normalize_gaussian


class MisprAdapterTests(unittest.TestCase):
    def request(self):
        # Integration fixture only; these are not selected scientific parameters.
        settings = {"functional": "B3LYP", "basis_set": "6-31G(d)", "route_parameters": {},
                    "link0_parameters": {"%chk": "test.chk", "%mem": "2GB", "%NProcShared": "2"}}
        return {"gaussian_inputs": {"opt": copy.deepcopy(settings), "freq": copy.deepcopy(settings)},
                "solvent_gaussian_inputs": None}

    @unittest.skipUnless(DEFAULT_SOURCE.is_dir(), "需要已锁定的上游源码，不能用模拟替代集成测试")
    def test_real_upstream_call(self):
        request = self.request()
        before = copy.deepcopy(request)
        result = normalize_gaussian(request)
        self.assertEqual(result["provider"], "MISPR")
        self.assertEqual(result["jobs_submitted"], 0)
        self.assertIn("Opt", result["gaussian_inputs"]["opt"]["route_parameters"])
        self.assertIn("Freq", result["gaussian_inputs"]["freq"]["route_parameters"])
        self.assertNotIn("Opt", result["gaussian_inputs"]["freq"]["route_parameters"])
        self.assertEqual(request, before)
        self.assertEqual(result["gaussian_inputs"]["opt"]["link0_parameters"]["%NProcShared"], "2")

    @unittest.skipUnless(DEFAULT_SOURCE.is_dir(), "需要已锁定的上游源码")
    def test_real_solvent_handling(self):
        request = self.request()
        request["solvent_gaussian_inputs"] = "(SMD,Solvent=Water)"
        result = normalize_gaussian(request)
        self.assertEqual(result["gaussian_inputs"]["freq"]["route_parameters"]["SCRF"], "(SMD,Solvent=Water)")

    def test_no_implicit_resource_defaults(self):
        for field in ("%mem", "%NProcShared", "%chk"):
            request = self.request()
            del request["gaussian_inputs"]["opt"]["link0_parameters"][field]
            with self.assertRaises(ValueError):
                normalize_gaussian(request)

    def test_no_implicit_method_defaults(self):
        request = self.request()
        del request["gaussian_inputs"]["opt"]["functional"]
        with self.assertRaises(ValueError):
            normalize_gaussian(request)

    def test_environment_must_be_explicit(self):
        request = self.request()
        del request["solvent_gaussian_inputs"]
        with self.assertRaises(ValueError):
            normalize_gaussian(request)

    def test_missing_source_is_not_fake_success(self):
        with self.assertRaises(ValueError):
            normalize_gaussian(self.request(), DEFAULT_SOURCE / "missing")
