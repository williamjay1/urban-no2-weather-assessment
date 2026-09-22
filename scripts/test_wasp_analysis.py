"""Noiseless tests for the prespecified WASP statistics; no real outcome selection."""
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

import wasp_analysis as wa


def synthetic_panel():
    rows = []
    for year in range(2019, 2025):
        for month in [4, 5, 6, 7]:
            dates = pd.date_range(f"{year}-{month:02d}-01", periods=5, freq="7D")
            for site in ["A", "B"]:
                for k, date in enumerate(dates):
                    regime = ["neither", "episode", "heat_only", "wind_only", "other_compound"][k]
                    # Use dates just to satisfy the unique-day keys. Calendar strata are
                    # explicit here and identical to the model definition under test.
                    signal = dict(neither=0, episode=3, heat_only=1, wind_only=2, other_compound=4)[regime]
                    rows.append(dict(city="Atlanta", date=date, station_id=site, year=year,
                        month=month, weekday=1, no2_ppb=20 + .2*(year - 2019) + month + (site == "B") + signal,
                        regime=regime, episode_id=f"e{year}_{month}" if regime == "episode" else "",
                        hot=regime in ["episode", "heat_only", "other_compound"],
                        calm=regime in ["episode", "wind_only", "other_compound"],
                        persistent_wind_only=regime == "wind_only", pure_wind_run_days=2 if regime == "wind_only" else 0,
                        core_station_year=True))
    return pd.DataFrame(rows)


class WaspAnalysisTests(unittest.TestCase):
    def test_legacy_weighted_fe_and_coefficients(self):
        self.assertTrue(all(wa.legacy_self_test().values()))

    def test_consecutive_runs_duration_and_gaps(self):
        dates = pd.to_datetime(["2020-02-27", "2020-02-28", "2020-02-29", "2020-03-01", "2020-03-03"])
        self.assertEqual(wa.consecutive_runs(dates, 3), [(dates[0], dates[3])])
        self.assertEqual(len(wa.consecutive_runs(dates, 1)), 2)

    def test_known_noiseless_coefficients(self):
        fit = wa.fit_city(synthetic_panel(), years=tuple(range(2019, 2025)), adjusted=False)
        np.testing.assert_allclose(fit["point"], [3, 1, 2, 4, 1, 2], atol=1e-10)

    def test_direct_binary_removes_all_other_states(self):
        panel = synthetic_panel()
        selected = wa.select_rows(panel, comparator="neither")
        self.assertEqual(set(selected.regime), {"episode", "neither"})
        fit = wa.fit_city(panel, years=tuple(range(2019, 2025)), adjusted=False, comparator="neither")
        np.testing.assert_allclose(fit["point"], [3], atol=1e-10)
        fit = wa.fit_city(panel, years=tuple(range(2019, 2025)), adjusted=False, comparator="wind_only")
        np.testing.assert_allclose(fit["point"], [1], atol=1e-10)

    def test_both_present_strata_required(self):
        panel = synthetic_panel()
        panel = panel[~(panel.year.eq(2019) & panel.regime.eq("neither"))]
        selected = wa.select_rows(panel, comparator="neither")
        self.assertFalse(selected.year.eq(2019).any())
        self.assertTrue(selected.year.eq(2020).any())

    def test_persistent_excludes_isolated_and_other_states(self):
        panel = synthetic_panel()
        panel.loc[panel.year.eq(2019), "persistent_wind_only"] = False
        selected = wa.select_rows(panel, comparator="wind_only", persistent=True)
        self.assertFalse(selected.year.eq(2019).any())
        self.assertEqual(set(selected.regime), {"episode", "wind_only"})

    def test_factorial_all_contrasts(self):
        names, C = wa.contrasts_for(["compound", "heat_only", "wind_only"])
        self.assertIn("compound_vs_wind_only", names)
        self.assertIn("compound_vs_heat_only", names)
        self.assertIn("compound_additive_interaction", names)
        np.testing.assert_allclose(C @ [5, 1, 2], [5, 1, 2, 3, 4, 2])

    def test_nonidentifiability_not_zero_and_all_city_rule(self):
        estimates = wa.coefficients(np.diag([1., 0]), np.array([2., 0]), np.eye(2))
        self.assertEqual(estimates[0], 2)
        self.assertTrue(np.isnan(estimates[1]))
        self.assertTrue(np.isnan(wa.all_city_mean(np.array([[1.], [np.nan]])))[0])
        fit = wa.fit_city(synthetic_panel().iloc[:0], years=tuple(range(2019, 2025)), adjusted=False)
        self.assertTrue(np.isnan(fit["point"]).all())

    def test_year_blocks_match_explicit_subset_refit(self):
        panel = synthetic_panel()
        years = tuple(range(2019, 2025))
        fit = wa.fit_city(panel, years=years, adjusted=False)
        counts = np.array([[1, 0, 1, 1, 1, 1], [2, 0, 0, 0, 0, 0]])
        block = wa.resample_years(fit, counts)
        refit = wa.fit_city(panel[panel.year.ne(2020)], years=years, adjusted=False)
        np.testing.assert_allclose(block[0], refit["point"], atol=1e-10)
        np.testing.assert_allclose(block[1], fit["point"], atol=1e-10)

    def test_bootstrap_fixed_city_distinct_no_replacement_failure(self):
        def stub(offset, zero_first=False):
            return dict(blocks=np.array([[[0. if zero_first else 1.]], [[1.]]]),
                        q=np.array([[0. if zero_first else offset], [offset + 2]]),
                        C=np.ones((1, 1)), names=["a"], years=[2019, 2020])
        fits = [stub(1), stub(10, True)]
        draws, _, counts = wa.bootstrap_diagnostics(fits, 200, 1)
        expected = np.stack([wa.resample_years(fit, counts) for fit in fits]).mean(axis=0)
        np.testing.assert_allclose(draws["synchronized_year_fixed_cities"], expected, equal_nan=True)
        self.assertGreater(np.isnan(expected).sum(), 0)
        self.assertEqual(len(expected), 200)
        self.assertFalse(np.allclose(draws["synchronized_year_fixed_cities"],
                                     draws["synchronized_year_resampled_cities"], equal_nan=True))
        again, _, _ = wa.bootstrap_diagnostics(fits, 200, 1)
        for key in draws:
            np.testing.assert_array_equal(draws[key], again[key])

    def test_unavailable_point_suppresses_conditional_interval(self):
        lo, hi, valid = wa.diagnostic_interval(np.array([1., 2., np.nan]), False)
        self.assertTrue(np.isnan(lo) and np.isnan(hi))
        self.assertEqual(valid, 2)
        lo, hi, _ = wa.diagnostic_interval(np.array([1., 2.]), True, False)
        self.assertTrue(np.isnan(lo) and np.isnan(hi))

    def test_jackknife_requires_every_block(self):
        diag = wa.jackknife_diagnostic(2., np.array([1., 2., 3., np.nan, 2., 2.]))
        self.assertTrue(np.isnan(diag["jackknife_se"]))
        diag = wa.jackknife_diagnostic(2., np.array([1., 2., 3., 2., 2., 2.]))
        self.assertAlmostEqual(diag["jackknife_se"], np.sqrt(5/6*2))

    def test_definition_othercompound_and_pure_wind(self):
        dates = pd.date_range("2019-01-01", "2025-12-31")
        n = len(dates)
        # Periodic weather, with deterministic ties, tests both threshold conventions.
        raw = pd.DataFrame(dict(city="Atlanta", date=dates,
            temperature_2m_max=(np.arange(n)//3) % 10, wind_speed_10m_mean=(np.arange(n)//5) % 10))
        base, _, events, runs = wa.label_weather(raw)
        self.assertTrue(base.loc[base.episode_id.ne(""), "hot"].all())
        self.assertTrue(base.loc[base.episode_id.ne(""), "calm"].all())
        self.assertTrue(base.loc[base.episode_id.ne(""), "warm"].all())
        leftovers = base.hot & base.calm & base.episode_id.eq("")
        self.assertTrue(base.loc[leftovers, "regime"].eq("other_compound").all())
        self.assertGreater(len(events), 0)
        self.assertTrue((events.duration_days >= 2).all())
        alt, _, ev3, _ = wa.label_weather(raw, wa.Definition("three", .8, .3, 3, 0))
        self.assertGreater(len(ev3), 0)
        self.assertTrue((ev3.duration_days >= 3).all())
        self.assertFalse((base.persistent_wind_only & base.hot).any())
        self.assertTrue(base.loc[base.persistent_wind_only, "pure_wind_run_days"].ge(2).all())

    def test_portable_output_paths_and_source_protection(self):
        source = Path("portable_reproduction/data")
        dest = Path("portable_reproduction/results")
        self.assertEqual(wa.validate_output_path(source, dest), dest.resolve())
        self.assertEqual(wa.validate_output_path(source, source / "analysis"), (source / "analysis").resolve())
        for bad in [source, source.parent, source / "weather", source / "stations/results", source / "raw/results"]:
            with self.assertRaises(ValueError):
                wa.validate_output_path(source, bad)

    def test_definition_start_separation_and_preserved_short_runs(self):
        dates = pd.date_range("2019-01-01", "2025-12-31")
        n = len(dates)
        raw = pd.DataFrame(dict(city="Atlanta", date=dates,
            temperature_2m_max=np.arange(n) % 100, wind_speed_10m_mean=np.arange(n) % 100))
        # Reference has disjoint heat/calm states; deliberately insert known episodes later.
        for a, b in [("2025-04-02", "2025-04-03"), ("2025-04-06", "2025-04-07"),
                     ("2025-04-10", "2025-04-12"), ("2025-04-18", "2025-04-18")]:
            mask = raw.date.between(a, b)
            raw.loc[mask, "temperature_2m_max"] = 110
            raw.loc[mask, "wind_speed_10m_mean"] = -1  # Synthetic labels only, not validated physical input.
        base, _, ev, _ = wa.label_weather(raw)
        apr = ev[ev.start_date.between("2025-04-01", "2025-04-30")]
        self.assertEqual(apr.start_date.dt.day.tolist(), [2, 10])
        self.assertEqual(base.loc[base.date.eq("2025-04-06"), "regime"].iloc[0], "other_compound")
        allruns, _, all_ev, _ = wa.label_weather(raw, wa.Definition("all", .8, .3, 2, 0))
        self.assertEqual(all_ev.start_date.dt.day.tolist(), [2, 6, 10])
        self.assertEqual(allruns.loc[allruns.date.eq("2025-04-18"), "regime"].iloc[0], "other_compound")


if __name__ == "__main__":
    unittest.main()
