import unittest

from simulation_agent.budget import estimate


class BudgetTests(unittest.TestCase):
    def fixture(self):
        return {"billing": {"unit": "cpu_core_hour", "price_per_unit_hour": None, "currency": "CNY"},
                "budget_cap": None, "jobs": [{"label": "synthetic", "billable_units": 4,
                "walltime_hours": 2, "replicas": 3, "max_attempts": 2}]}

    def test_unknown_price_is_not_zero(self):
        result = estimate(self.fixture())
        self.assertEqual(result["total_billable_unit_hours"], 48)
        self.assertIsNone(result["allocation_cost_ceiling"])
        self.assertIsNone(result["within_cap"])
        self.assertFalse(result["submission_enabled"])

    def test_over_cap(self):
        request = self.fixture()
        request["billing"]["price_per_unit_hour"] = 1
        request["budget_cap"] = 40
        self.assertFalse(estimate(request)["within_cap"])

    def test_node_billing_is_explicit(self):
        request = self.fixture()
        request["billing"]["unit"] = "node_hour"
        request["billing"]["price_per_unit_hour"] = 2
        request["jobs"][0]["billable_units"] = 1
        self.assertEqual(estimate(request)["allocation_cost_ceiling"], 24)

    def test_invalid_resources(self):
        for value in (0, -1, True, float("inf")):
            request = self.fixture()
            request["jobs"][0]["billable_units"] = value
            with self.assertRaises(ValueError):
                estimate(request)
