"""
Suite de Pruebas Unitarias para JevScreener (Arquitectura 5+1)
"""

import unittest
import numpy as np
import pandas as pd
from screener import JevScreener


class TestJevScreener(unittest.TestCase):

    def setUp(self):
        self.screener = JevScreener()

    def test_filter_pre_llm_entropy_deterministic(self):
        # 1. Serie estructurada persistente (baja entropía)
        dates = pd.date_range("2026-01-01", periods=100, freq="1h")
        np.random.seed(99)
        rets_persist = np.concatenate([
            np.random.normal(0.005, 0.001, 75),
            np.random.normal(0.005, 0.004, 25)
        ])
        clean_prices = 100 * np.exp(np.cumsum(rets_persist))
        df_clean = pd.DataFrame({"close": clean_prices}, index=dates)

        res_clean = self.screener.filter_pre_llm_entropy(df_clean)
        self.assertTrue(res_clean["allow_llm_call"])
        self.assertLess(res_clean["h_norm"], 0.84)
        self.assertEqual(res_clean["regime"], "PERSISTENT_STRUCTURE")

        # 2. Serie caótica / ruido blanco puro
        np.random.seed(42)
        chaos_returns = np.random.normal(0, 0.05, 100)
        chaos_prices = 100 * np.exp(np.cumsum(chaos_returns))
        df_chaos = pd.DataFrame({"close": chaos_prices}, index=dates)

        res_chaos = self.screener.filter_pre_llm_entropy(df_chaos)
        self.assertGreater(res_chaos["h_norm"], 0.70)

    def test_cluster_correlation_matrix(self):
        np.random.seed(123)
        ret_a = np.random.normal(0.001, 0.01, 100)
        ret_b = ret_a + np.random.normal(0.0, 0.001, 100)
        ret_c = np.random.normal(0.001, 0.01, 100)

        curves = {
            "STRAT_A": pd.Series(100 * np.cumprod(1 + ret_a)),
            "STRAT_B": pd.Series(100 * np.cumprod(1 + ret_b)),
            "STRAT_C": pd.Series(100 * np.cumprod(1 + ret_c))
        }

        rankings = {"STRAT_A": 2.5, "STRAT_B": 1.8, "STRAT_C": 2.1}

        res = self.screener.cluster_correlation_matrix(curves, kpi_rankings=rankings, max_correlation=0.80)
        self.assertIn("STRAT_A", res["retained_strategies"])
        self.assertIn("STRAT_B", res["pruned_strategies"])
        self.assertIn("STRAT_C", res["retained_strategies"])
        self.assertEqual(len(res["retained_strategies"]), 2)

    def test_validate_governance_rules(self):
        bad_meta = {"max_dd": 22.5, "profit_factor": 1.6, "total_trades": 50, "sizing_mode": "PERCENTAGE"}
        val_bad = self.screener.validate_governance_rules(bad_meta, account_type="CAPITAL_PROPIO")
        self.assertFalse(val_bad["passed"])
        self.assertTrue(any("techo" in v for v in val_bad["violations"]))

        fixed_meta = {"max_dd": 12.0, "profit_factor": 1.6, "total_trades": 50, "sizing_mode": "FIXED_DOLLAR"}
        val_fixed = self.screener.validate_governance_rules(fixed_meta, account_type="CAPITAL_PROPIO")
        self.assertFalse(val_fixed["passed"])
        self.assertTrue(any("PROHIBIDO" in v for v in val_fixed["violations"]))

        good_meta = {"max_dd": 14.2, "profit_factor": 1.75, "total_trades": 45, "sizing_mode": "PERCENTAGE"}
        val_good = self.screener.validate_governance_rules(good_meta, account_type="CAPITAL_PROPIO")
        self.assertTrue(val_good["passed"])
        self.assertEqual(len(val_good["violations"]), 0)

    def test_calculate_stagnation_days(self):
        dates = pd.date_range("2026-01-01", periods=30, freq="1D")
        eq = [100 + i for i in range(10)] + [102 for _ in range(19)] + [115]
        s_eq = pd.Series(eq, index=dates)

        stag_days = self.screener.calculate_stagnation_days(s_eq, dates=pd.Series(dates))
        self.assertGreaterEqual(stag_days, 18)

    def test_calculate_oos_r_dd_ratio(self):
        res_good = self.screener.calculate_oos_r_dd_ratio(is_return=30.0, is_max_dd=10.0, oos_return=27.0, oos_max_dd=10.0)
        self.assertTrue(res_good["pass_filter"])
        self.assertEqual(res_good["status"], "APROBADO_OOS")

        res_bad = self.screener.calculate_oos_r_dd_ratio(is_return=40.0, is_max_dd=10.0, oos_return=12.0, oos_max_dd=10.0)
        self.assertFalse(res_bad["pass_filter"])
        self.assertEqual(res_bad["status"], "RECHAZADO_OVERFITTING")

    def test_calculate_asset_breakdown(self):
        trades = [
            {"symbol": "NQ", "net_pnl": 350.0},
            {"symbol": "NQ", "net_pnl": 200.0},
            {"symbol": "NQ", "net_pnl": -100.0},
            {"symbol": "ES", "net_pnl": 150.0},
            {"symbol": "ES", "net_pnl": -50.0}
        ]
        breakdown = self.screener.calculate_asset_breakdown(trades)
        self.assertIn("NQ", breakdown)
        self.assertIn("ES", breakdown)
        self.assertEqual(breakdown["NQ"]["total_trades"], 3)
        self.assertEqual(breakdown["NQ"]["max_win_streak"], 2)
        self.assertEqual(breakdown["NQ"]["net_pnl"], 450.0)


if __name__ == '__main__':
    unittest.main()
