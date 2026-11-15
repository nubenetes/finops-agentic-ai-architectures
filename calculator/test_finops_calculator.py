"""Unit tests for the FinOps model (python -m unittest discover calculator)."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import finops_calculator as f  # noqa: E402


class ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = f.FinOpsModel.load()

    def test_reference_scenario_matches_baseline(self):
        """Calibration scenario: P3, Spain Central, 1,000 standard queries, no build cost."""
        s = f.Scenario(queries=1000, include_build=False)
        expected = {"A": 985.5, "B": 1107.0, "C": 1524.8, "D": 3955.5}
        for arch, value in expected.items():
            self.assertAlmostEqual(self.m.cost(arch, s).cloud_total, value, delta=1.0)

    def test_crossover_is_a_real_equality(self):
        s = f.Scenario(queries=0, profile="P3")
        q = self.m.crossover("B", "C", s)
        self.assertIsNotNone(q)
        probe = f.Scenario(queries=q, profile="P3", include_build=False)
        self.assertAlmostEqual(self.m.cost("B", probe).cloud_total, self.m.cost("C", probe).cloud_total, delta=0.01)

    def test_efficiency_threshold_means_fixed_equals_variable(self):
        s = f.Scenario(queries=0, profile="P2")
        q = self.m.efficiency_threshold("A", s)
        c = self.m.cost("A", f.Scenario(queries=q, profile="P2", include_build=False))
        self.assertAlmostEqual(c.cloud_fixed, c.cloud_variable, delta=0.01)

    def test_more_agents_favour_managed_platform(self):
        one = self.m.all_costs(f.Scenario(queries=10_000, profile="P2", agents=1))
        many = self.m.all_costs(f.Scenario(queries=10_000, profile="P2", agents=8))
        self.assertLess(one["A"].tco, one["B"].tco)
        self.assertLess(many["B"].tco, many["A"].tco)

    def test_optimization_reduces_ai_cost(self):
        base = f.Scenario(queries=1000)
        optimised = f.Scenario(queries=1000, optimization="routing_and_cache")
        self.assertLess(self.m.ai_per_query(optimised), self.m.ai_per_query(base))

    def test_regions_increase_fixed_cost(self):
        base = self.m.fixed("B", f.Scenario(queries=0))
        multi = self.m.fixed("B", f.Scenario(queries=0, extra_cells=2, dr_regions=1))
        self.assertGreater(multi, base)

    def test_shared_services_reduce_fixed_cost(self):
        base = self.m.fixed("D", f.Scenario(queries=0))
        shared = self.m.fixed("D", f.Scenario(queries=0, shared_integration=True, shared_edge=True))
        self.assertLess(shared, base)

    def test_gpu_requirement_forces_kubernetes(self):
        rec = self.m.recommend(f.Scenario(queries=5_000), needs_gpu_or_portability=True)
        self.assertEqual(rec["best"], "C")

    def test_us_regions_are_cheaper_than_spain_central(self):
        es = self.m.cost("B", f.Scenario(queries=1000, include_build=False)).cloud_total
        us = self.m.cost("B", f.Scenario(queries=1000, region="eastus2", include_build=False)).cloud_total
        ch = self.m.cost("B", f.Scenario(queries=1000, region="switzerlandnorth", include_build=False)).cloud_total
        self.assertLess(us, es)
        self.assertGreater(ch, es)

    def test_unknown_region_raises(self):
        with self.assertRaises(ValueError):
            self.m.cost("A", f.Scenario(queries=1, region="atlantis"))

    def test_dual_currency_format(self):
        self.assertEqual(f.fmt_num(1234567.891, 2), "1,234,567.89")
        self.assertEqual(f.eur(1107), "€1,107")
        self.assertEqual(f.money(1000), "€1,000 / $1,150")

    def test_update_docs_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            doc = Path(tmp) / "doc.md"
            doc.write_text(
                "x\n<!-- BEGIN:table-profiles -->\nstale\n<!-- END:table-profiles -->\n"
                "value <!-- val:value-per-query -->?<!-- /val --> end\n",
                encoding="utf-8",
            )
            self.assertEqual(f.update_docs(self.m, [doc]), [doc])
            first = doc.read_text(encoding="utf-8")
            self.assertIn("| Architecture |", first)
            self.assertNotIn("stale", first)
            self.assertEqual(f.update_docs(self.m, [doc]), [])

    def test_cli_runs(self):
        self.assertEqual(f.main(["--queries", "5000", "--profile", "P1", "--json"]), 0)


if __name__ == "__main__":
    unittest.main()
