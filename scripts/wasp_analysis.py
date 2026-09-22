"""WASP revision: calendar-stratified environmental associations, 2026-09-23.

Only consumes the completed local-standard-day weather and qualified AQS inputs.
No source retrieval, time alignment, manuscript editing or publication occurs here.
The old analysis and outputs are never modified. Numerical FE/estimability helpers
are imported from the preserved, tested calendar_station_analysis module.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import sys
import time

import numpy as np
import pandas as pd
from patsy import build_design_matrices, dmatrix
from scipy.stats import t

from calendar_station_analysis import coefficients, within_transform, self_test as legacy_self_test

ROOT = Path("D:/MLWork/urban_no2_recovery_scs/results/wasp_20260923")
SEED = 20260923
CITIES = ("Atlanta", "Chicago", "Dallas", "Denver", "Houston", "Los Angeles",
          "New York", "Philadelphia", "Phoenix", "San Diego", "Seattle")
MET = ["relative_humidity_2m_mean", "precipitation_sum", "shortwave_radiation_sum",
       "wind_direction_10m_dominant"]
WEATHER_FIELDS = ["temperature_2m_max", "wind_speed_10m_mean"] + MET
REGIMES = ["episode", "heat_only", "wind_only", "other_compound"]
SUMMARY_NOTE = ("Cross-city t summary of dispersion, df=10 under approximate independent-city "
                "conditions; not guaranteed 95% coverage of the fixed heterogeneous 11-city target.")
TEMPORAL_NOTE = ("Whole-year exchangeability with very few blocks is an approximation. "
                 "Percentiles are conditional on estimability, not unconditional confidence limits.")


def clean_json(value):
    if isinstance(value, dict):
        return {str(k): clean_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean_json(v) for v in value]
    if isinstance(value, np.ndarray):
        return clean_json(value.tolist())
    if isinstance(value, np.generic):
        return clean_json(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        return None
    if isinstance(value, (Path, pd.Timestamp)):
        return str(value)
    return value


def dump(path, value):
    path.write_text(json.dumps(clean_json(value), indent=2, ensure_ascii=True,
                               allow_nan=False), encoding="utf-8")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass(frozen=True)
class Definition:
    name: str = "p80_p30_min2_sep7"
    heat_quantile: float = .80
    wind_quantile: float = .30
    min_days: int = 2
    start_separation: int = 7


DEFINITIONS = [Definition(), Definition("p85_p30_min2_sep7", .85, .30, 2, 7),
               Definition("p80_p20_min2_sep7", .80, .20, 2, 7),
               Definition("p80_p30_min3_sep7", .80, .30, 3, 7),
               Definition("p80_p30_min2_allruns", .80, .30, 2, 0)]


def consecutive_runs(dates, minimum=1):
    """Calendar-contiguous dates only; omitted days break runs."""
    dates = pd.DatetimeIndex(pd.to_datetime(dates)).sort_values().unique()
    result, block = [], []
    for day in dates:
        if block and (day - block[-1]).days != 1:
            if len(block) >= minimum:
                result.append((block[0], block[-1]))
            block = []
        block.append(day)
    if len(block) >= minimum:
        result.append((block[0], block[-1]))
    return result


def label_weather(raw, definition=Definition()):
    """All definitions use weather alone; keep short/separation-excluded compound days."""
    w = raw.copy().sort_values(["city", "date"]).reset_index(drop=True)
    for field, vals in [("year", w.date.dt.year), ("month", w.date.dt.month),
                        ("weekday", w.date.dt.weekday)]:
        w[field] = vals
    w["warm"] = w.month.between(4, 10)
    w["hot"], w["calm"] = False, False
    w["episode_id"], w["pure_wind_run_id"] = "", ""
    w["pure_wind_run_days"], w["low_wind_run_days"] = 0, 0
    w["phase"] = "background"
    thresholds, events, run_rows = [], [], []
    for city, g in w.groupby("city", sort=True):
        reference = g[g.warm & g.year.between(2019, 2022)]
        heat = float(reference.temperature_2m_max.quantile(definition.heat_quantile))
        wind = float(reference.wind_speed_10m_mean.quantile(definition.wind_quantile))
        hot, calm = g.temperature_2m_max.ge(heat), g.wind_speed_10m_mean.le(wind)
        w.loc[g.index, "hot"], w.loc[g.index, "calm"] = hot, calm
        thresholds.append(dict(definition=definition.name, city=city, heat_c=heat,
                               wind_kmh=wind, threshold_days=len(reference), **{
                                   k: v for k, v in asdict(definition).items() if k != "name"}))
        previous, retained = None, []
        for start, end in consecutive_runs(g.loc[hot & calm & g.warm, "date"], definition.min_days):
            if previous is not None and (start - previous).days < definition.start_separation:
                continue
            previous = start
            eid = city.lower().replace(" ", "_") + "_" + start.date().isoformat()
            mask = g.date.between(start, end)
            w.loc[g.index[mask], "episode_id"] = eid
            retained.append((start, end))
            events.append(dict(definition=definition.name, city=city, year=start.year,
                               episode_id=eid, start_date=start, end_date=end,
                               duration_days=(end - start).days + 1))
        # Duration is measured on the weather calendar, never the observed NO2 calendar.
        for kind, selected in [("low_wind", calm & g.warm),
                               ("pure_wind", calm & ~hot & g.warm)]:
            for start, end in consecutive_runs(g.loc[selected, "date"]):
                duration = (end - start).days + 1
                ix = g.index[g.date.between(start, end)]
                w.loc[ix, kind + "_run_days"] = duration
                rid = city.lower().replace(" ", "_") + "_" + start.date().isoformat()
                if kind == "pure_wind":
                    w.loc[ix, "pure_wind_run_id"] = rid
                run_rows.append(dict(definition=definition.name, city=city, year=start.year,
                                     run_type=kind, run_id=rid, start_date=start,
                                     end_date=end, duration_days=duration))
        for phase, bounds in [("pre1_6", (-6, -1)), ("post3_6", (3, 6)), ("post1_2", (1, 2))]:
            for start, end in retained:
                anchor = start if phase.startswith("pre") else end
                ix = g.index[g.date.between(anchor + pd.Timedelta(days=bounds[0]),
                                           anchor + pd.Timedelta(days=bounds[1]))]
                w.loc[ix, "phase"] = phase
    w["regime"] = np.select([w.episode_id.ne(""), w.hot & w.calm, w.hot, w.calm],
                             REGIMES[:1] + ["other_compound", "heat_only", "wind_only"],
                             default="neither")
    w["regime_factorial"] = np.select([w.hot & w.calm, w.hot, w.calm],
                                       ["compound", "heat_only", "wind_only"], default="neither")
    w["persistent_wind_only"] = w.regime.eq("wind_only") & w.pure_wind_run_days.ge(2)
    w["wind_duration_class"] = np.select(
        [w.persistent_wind_only, w.regime.eq("wind_only")],
        ["persistent_wind_only", "isolated_wind_only"], default="not_wind_only")
    w.loc[w.hot & w.calm & w.warm, "phase"] = "other_compound"
    w.loc[w.episode_id.ne(""), "phase"] = "episode"
    return (w, pd.DataFrame(thresholds), pd.DataFrame(events, columns=["definition", "city", "year",
        "episode_id", "start_date", "end_date", "duration_days"]), pd.DataFrame(run_rows,
        columns=["definition", "city", "year", "run_type", "run_id", "start_date", "end_date", "duration_days"]))


def add_splines(weather):
    """Freeze natural cubic bases on unique 2019-24 weather city-days, not outcomes."""
    w, specifications = weather.copy(), {}
    for city, g in w.groupby("city", sort=True):
        specifications[city] = {}
        for field in MET[:3] + ["wind_speed_10m_mean"]:
            x = g[field].to_numpy(float)
            if field == "precipitation_sum":
                x = np.log1p(x)
            mask = g.warm & g.year.between(2019, 2024)
            if field == "wind_speed_10m_mean":
                mask &= g.calm  # Fixed base P30 low-wind frame for E-vs-W sensitivity.
            train = x[mask.to_numpy()]
            knot_source = train[train > 0] if field == "precipitation_sum" else train
            knots = np.unique(np.quantile(knot_source, [1/3, 2/3]))
            knots = knots[(knots > train.min()) & (knots < train.max())]
            if len(knots) != 2:
                raise ValueError(f"Cannot define prespecified spline: {city}/{field}")
            args = dict(x=train, knots=knots, lower=float(train.min()), upper=float(train.max()))
            design = dmatrix("cr(x, knots=knots, lower_bound=lower, upper_bound=upper, "
                             "constraints='center') - 1", args)
            args["x"] = x
            basis = np.asarray(build_design_matrices([design.design_info], args)[0])
            prefix = "wind_adjust" if field == "wind_speed_10m_mean" else "met_" + field
            for k in range(3):
                w.loc[g.index, f"{prefix}_{k}"] = basis[:, k]
            specifications[city][field] = dict(df=3, knots=knots.tolist(),
                lower=float(train.min()), upper=float(train.max()), reference_days=len(train),
                reference="2019-2024 warm low-wind P30 days" if field == "wind_speed_10m_mean"
                          else "2019-2024 warm days", log1p=field == "precipitation_sum",
                center_constraint=np.asarray(design.design_info.factor_infos[
                    next(iter(design.design_info.factor_infos))].state["transforms"][
                        next(iter(design.design_info.factor_infos[
                            next(iter(design.design_info.factor_infos))].state["transforms"]))
                    ]._constraints).tolist())
    angle = np.deg2rad(w.wind_direction_10m_dominant)
    w["met_wind_sin"], w["met_wind_cos"] = np.sin(angle), np.cos(angle)
    return w, specifications


def make_strata(df):
    return (df.station_id.astype(str) + "|" + df.year.astype(str) + "|" +
            df.month.astype(str) + "|" + df.weekday.astype(str))


def select_rows(data, *, comparator=None, persistent=False, core=False, label="regime"):
    """For a direct comparison, remove other states BEFORE enforcing both-present strata."""
    df = data.copy()
    df["stratum"] = make_strata(df)
    if core:
        df = df[df.core_station_year].copy()
    if comparator is not None:
        comp = df.regime.eq(comparator)
        if persistent:
            if comparator != "wind_only":
                raise ValueError("Persistence restriction only defined for wind-only comparator")
            comp &= df.persistent_wind_only
        df = df[df.regime.eq("episode") | comp].copy()
        counts = pd.crosstab(df.stratum, df.regime).reindex(columns=["episode", comparator], fill_value=0)
        eligible = counts.index[counts.gt(0).all(axis=1)]
        df = df[df.stratum.isin(eligible)].copy()
        df["binary_regime"] = np.where(df.regime.eq("episode"), "episode", "reference")
    # Unique station-days were validated upstream; this drops non-informative singleton strata.
    n = df.groupby("stratum").date.transform("nunique")
    return df[n.ge(2)].copy()


def contrasts_for(levels, *, comparator=None):
    if comparator is not None:
        return ["episode_vs_" + comparator], np.ones((1, 1))
    names, rows = [], []
    for lev in levels:
        c = np.zeros(len(levels)); c[levels.index(lev)] = 1
        names.append(lev + "_vs_reference"); rows.append(c)
    target = "compound" if "compound" in levels else "episode"
    if "heat_only" in levels and "wind_only" in levels:
        for other in ["wind_only", "heat_only"]:
            c = np.zeros(len(levels)); c[levels.index(target)] = 1
            c[levels.index(other)] = -1
            names.append(target + "_vs_" + other); rows.append(c)
    if "compound" in levels:
        c = np.zeros(len(levels)); c[levels.index("compound")] = 1
        c[levels.index("heat_only")] = c[levels.index("wind_only")] = -1
        names.append("compound_additive_interaction"); rows.append(c)
    return names, np.array(rows)


def fit_city(data, *, years, adjusted=True, comparator=None, persistent=False,
             wind_adjust=False, core=False, equal_site=False, label="regime"):
    df = select_rows(data, comparator=comparator, persistent=persistent, core=core, label=label)
    if comparator is not None:
        levels, fit_label = ["episode"], "binary_regime"
    elif label == "regime_factorial":
        levels, fit_label = ["compound", "heat_only", "wind_only"], label
    elif label == "phase":
        levels, fit_label = ["episode", "pre1_6", "post1_2", "post3_6", "other_compound"], label
    else:
        levels, fit_label = REGIMES, label
    covariates = sorted(c for c in data if c.startswith("met_")) if adjusted else []
    if wind_adjust:
        if comparator != "wind_only":
            raise ValueError("Continuous wind sensitivity requires direct E-vs-W sample")
        covariates += ["wind_adjust_0", "wind_adjust_1", "wind_adjust_2"]
    names, C0 = contrasts_for(levels, comparator=("persistent_wind_only" if persistent else comparator))
    C = np.pad(C0, ((0, 0), (0, len(covariates))))
    p = C.shape[1]
    blocks, vectors = np.zeros((len(years), p, p)), np.zeros((len(years), p))
    columns = [f"indicator_{lev}" for lev in levels] + covariates
    if len(df):
        df["weight"] = 1.0 if equal_site else 1 / df.groupby("date").station_id.transform("nunique")
        x = np.column_stack([df[fit_label].eq(lev).to_numpy(float) for lev in levels] +
                            [df[c].to_numpy(float) for c in covariates])
        y, weights = df.no2_ppb.to_numpy(float), df.weight.to_numpy(float)
        xw, yw = within_transform(x, y, weights, df.stratum)
        for k, year in enumerate(years):
            mask = df.year.eq(year).to_numpy()
            blocks[k] = (xw[mask] * weights[mask, None]).T @ xw[mask]
            vectors[k] = xw[mask].T @ (weights[mask] * yw[mask])
        S, q = blocks.sum(axis=0), vectors.sum(axis=0)
        beta = np.linalg.pinv(S, rcond=1e-11) @ q
        rmse = float(np.sqrt(np.average((yw - xw @ beta)**2, weights=weights)))
    else:
        df["weight"] = pd.Series(dtype=float)
        S, q, rmse = blocks.sum(axis=0), vectors.sum(axis=0), np.nan
    point = coefficients(S, q, C)
    singular = np.linalg.svd(S, compute_uv=False)
    rank = int(np.sum(singular > (singular[0] * 1e-11))) if singular.size and singular[0] else 0
    episode = df.regime.eq("episode")
    diagnostics = dict(n_station_days=len(df), n_city_days=df.date.nunique(),
        n_stations=df.station_id.nunique(), n_strata=df.stratum.nunique(),
        n_episode_station_days=int(episode.sum()), n_episode_city_days=df.loc[episode, "date"].nunique(),
        n_episodes=df.loc[episode, "episode_id"].nunique(),
        n_compound_city_days=df.loc[df.hot & df.calm, "date"].nunique(),
        n_years_observed=df.year.nunique(), n_year_blocks=len(years),
        rank_at_pinv_tolerance=rank, parameters=p,
        condition_number=float(np.linalg.cond(S)) if len(df) else np.nan,
        weighted_rmse=rmse, total_weight=float(df.weight.sum()))
    for lev in ["episode", "neither", "heat_only", "wind_only", "other_compound"]:
        diagnostics["station_days_" + lev] = int(df.regime.eq(lev).sum())
        diagnostics["city_days_" + lev] = int(df.loc[df.regime.eq(lev), "date"].nunique())
    if comparator is not None:
        diagnostics["both_present_strata"] = df.stratum.nunique()
        assert df.regime.isin(["episode", comparator]).all()
        assert not len(df) or pd.crosstab(df.stratum, df.regime).gt(0).all().all()
        if persistent:
            assert df.loc[df.regime.eq(comparator), "persistent_wind_only"].all()
    return dict(blocks=blocks, q=vectors, C=C, names=names, point=point,
                years=list(years), diagnostics=diagnostics, rows=df, columns=columns)


def resample_years(fit, counts, chunk=512):
    """Each count vector represents its original draw; nonidentifiable draws stay NaN."""
    results = []
    for start in range(0, len(counts), chunk):
        part = counts[start:start + chunk]
        S = np.einsum("by,yij->bij", part, fit["blocks"])
        q = part @ fit["q"]
        results.append(coefficients(S, q, fit["C"]))
    return np.concatenate(results) if results else np.empty((0, len(fit["names"])))


def all_city_mean(values):
    """No available-city substitution: one NaN makes the prespecified pooled target NaN."""
    return np.mean(values, axis=0)


def bootstrap_diagnostics(fits, reps, seed=SEED):
    """Independent hierarchical draws; separate fixed-city synchronous-year diagnostic."""
    rng = np.random.default_rng(seed)
    nc, ny = len(fits), len(fits[0]["years"])
    nk = len(fits[0]["names"])
    probabilities = np.full(ny, 1 / ny)
    # Hierarchy: sample nc cities, then independently sample years for EACH occurrence.
    city_sample = rng.integers(nc, size=(reps, nc))
    hierarchy_values = np.full((reps, nc, nk), np.nan)
    for city_index, fit in enumerate(fits):
        positions = np.where(city_sample == city_index)
        counts = rng.multinomial(ny, probabilities, size=len(positions[0]))
        hierarchy_values[positions] = resample_years(fit, counts)
    hierarchy = hierarchy_values.mean(axis=1)
    # Fixed city set, shared whole-year shock draw. DO NOT city-resample this mean.
    synchronous_counts = rng.multinomial(ny, probabilities, size=reps)
    synchronous_city_values = np.stack([resample_years(f, synchronous_counts) for f in fits])
    synchronous_fixed = synchronous_city_values.mean(axis=0)
    # Legacy-style city resampling with synchronous years, explicitly different target.
    sync_city_sample = rng.integers(nc, size=(reps, nc))
    synchronous_resampled = synchronous_city_values[sync_city_sample, np.arange(reps)[:, None]].mean(axis=1)
    independent_city = np.stack([resample_years(f, rng.multinomial(ny, probabilities, size=reps))
                                 for f in fits])
    return {"hierarchical_city_independent_year": hierarchy,
            "synchronized_year_fixed_cities": synchronous_fixed,
            "synchronized_year_resampled_cities": synchronous_resampled}, independent_city, synchronous_counts


def diagnostic_interval(values, point_identifiable, temporal_available=True):
    valid = values[np.isfinite(values)]
    allowed = point_identifiable and temporal_available and len(valid) > 0
    lo, hi = np.quantile(valid, [.025, .975]) if allowed else (np.nan, np.nan)
    return float(lo), float(hi), len(valid)


def jackknife_diagnostic(point, deletions):
    n = len(deletions)
    if n < 3 or not np.isfinite(point) or not np.isfinite(deletions).all():
        return dict(jackknife_se=np.nan, jackknife_lower=np.nan, jackknife_upper=np.nan,
                    jackknife_status="unavailable_fewer_than_3_blocks_or_nonidentifiable_deletion")
    se = np.sqrt((n - 1) / n * np.sum((deletions - np.mean(deletions))**2))
    margin = float(t.ppf(.975, n - 1) * se)
    return dict(jackknife_se=se, jackknife_lower=point - margin, jackknife_upper=point + margin,
                jackknife_status=f"delete_year_jackknife_diagnostic_t_df_{n-1}")


def pooled_models(panel, model, out, reps, years=tuple(range(2019, 2025)), **options):
    years = tuple(years)
    data = panel[panel.year.isin(years)]
    fits = [fit_city(data[data.city.eq(city)], years=years, **options) for city in CITIES]
    names = fits[0]["names"]
    points = np.stack([f["point"] for f in fits])
    pooled = all_city_mean(points)
    draws, city_draws, sync_counts = bootstrap_diagnostics(fits, reps)
    np.savez_compressed(out / f"{model}_sufficient_statistics.npz",
        blocks=np.stack([f["blocks"] for f in fits]), q=np.stack([f["q"] for f in fits]),
        C=fits[0]["C"], years=np.array(years), cities=np.array(CITIES),
        contrasts=np.array(names), columns=np.array(fits[0]["columns"]))
    # Preserve every original replicate including NaNs, not only surviving percentiles.
    np.savez_compressed(out / f"{model}_bootstrap_draws.npz", **draws,
                        city_independent_year=city_draws, synchronized_year_counts=sync_counts)
    deleted = np.full((len(years), len(CITIES), len(names)), np.nan)
    year_city_rows, year_rows = [], []
    if len(years) >= 2:
        for j, year in enumerate(years):
            keep = np.arange(len(years)) != j
            for i, fit in enumerate(fits):
                deleted[j, i] = coefficients(fit["blocks"][keep].sum(axis=0),
                                              fit["q"][keep].sum(axis=0), fit["C"])
                for k, contrast in enumerate(names):
                    year_city_rows.append(dict(model=model, city=CITIES[i], omitted_year=year,
                        contrast=contrast, estimate_ppb=deleted[j, i, k],
                        estimable=bool(np.isfinite(deleted[j, i, k]))))
            for k, contrast in enumerate(names):
                values = deleted[j, :, k]
                year_rows.append(dict(model=model, omitted_year=year, contrast=contrast,
                    estimate_ppb=float(np.mean(values)), n_cities=11,
                    n_estimable_cities=int(np.isfinite(values).sum()),
                    missing_cities=";".join(c for c, v in zip(CITIES, values) if not np.isfinite(v))))
    pd.DataFrame(year_rows, columns=["model", "omitted_year", "contrast", "estimate_ppb", "n_cities",
                                    "n_estimable_cities", "missing_cities"]).to_csv(out / f"{model}_leave_year.csv", index=False)
    pd.DataFrame(year_city_rows, columns=["model", "city", "omitted_year", "contrast", "estimate_ppb", "estimable"]).to_csv(
        out / f"{model}_leave_year_by_city.csv", index=False)
    city_rows, boot_rows, summary, leave_city_rows = [], [], [], []
    for i, (city, fit) in enumerate(zip(CITIES, fits)):
        for k, contrast in enumerate(names):
            valid = city_draws[i, :, k]
            lo, hi, nv = diagnostic_interval(valid, np.isfinite(points[i, k]), len(years) >= 2)
            city_rows.append(dict(model=model, city=city, contrast=contrast,
                estimate_ppb=points[i, k], estimable=bool(np.isfinite(points[i, k])),
                bootstrap_conditional_lower=lo, bootstrap_conditional_upper=hi,
                bootstrap_valid=nv, bootstrap_failed=reps - nv, bootstrap_attempted=reps,
                bootstrap_status="conditional_diagnostic" if len(years) >= 2 else "no_temporal_interval_single_year",
                **jackknife_diagnostic(points[i, k], deleted[:, i, k]), **fit["diagnostics"]))
    for k, contrast in enumerate(names):
        cp = points[:, k]
        identifiable = bool(np.isfinite(cp).all())
        point = float(pooled[k])
        margin = float(t.ppf(.975, 10) * cp.std(ddof=1) / np.sqrt(11)) if identifiable else np.nan
        row = dict(model=model, contrast=contrast,
            status="estimable_all_11_cities" if identifiable else "unavailable_all_11_city_target",
            estimate_ppb=point, cross_city_summary_lower=point - margin,
            cross_city_summary_upper=point + margin, cross_city_summary_note=SUMMARY_NOTE,
            n_cities=11, n_estimable_cities=int(np.isfinite(cp).sum()),
            missing_cities=";".join(c for c, v in zip(CITIES, cp) if not np.isfinite(v)),
            positive_estimable_cities=int(np.sum(cp > 0)), years=";".join(map(str, years)),
            n_year_blocks=len(years), bootstrap_attempted=reps,
            **jackknife_diagnostic(point, deleted[:, :, k].mean(axis=1)))
        for field in ["n_station_days", "n_city_days", "n_strata", "n_episode_station_days",
                      "n_episode_city_days", "n_episodes"]:
            row[field] = sum(f["diagnostics"][field] for f in fits)
        for scheme, values in draws.items():
            # Hierarchical/resampled-city draws in a single year describe only city resampling.
            temporal = len(years) >= 2 or scheme != "synchronized_year_fixed_cities"
            lo, hi, nv = diagnostic_interval(values[:, k], identifiable, temporal)
            status = "conditional_on_estimability"
            if not identifiable:
                status = "all_11_city_point_unavailable_percentiles_suppressed"
            elif len(years) == 1:
                status = "no_temporal_interval_single_year" if not temporal else "city_resampling_only_no_temporal_uncertainty"
            boot_rows.append(dict(model=model, contrast=contrast, scheme=scheme,
                attempted=reps, valid=nv, failed=reps - nv, failure_fraction=(reps - nv) / reps,
                conditional_lower=lo, conditional_upper=hi, status=status,
                target="fixed_11_cities" if scheme == "synchronized_year_fixed_cities" else "resampled_city_distribution",
                temporal_year_blocks=len(years), note=TEMPORAL_NOTE))
            row[scheme + "_valid"] = nv
            row[scheme + "_failed"] = reps - nv
            row[scheme + "_conditional_lower"] = lo
            row[scheme + "_conditional_upper"] = hi
        for i, city in enumerate(CITIES):
            remaining = np.delete(cp, i)
            leave_city_rows.append(dict(model=model, contrast=contrast, omitted_city=city,
                estimate_ppb=float(remaining.mean()), n_target_cities=10,
                n_estimable_cities=int(np.isfinite(remaining).sum()),
                target="equal_mean_remaining_10_cities_not_the_primary_11_city_target"))
        summary.append(row)
    pd.DataFrame(city_rows).to_csv(out / f"{model}_city_estimates.csv", index=False)
    pd.DataFrame(boot_rows).to_csv(out / f"{model}_bootstrap_diagnostics.csv", index=False)
    pd.DataFrame(leave_city_rows).to_csv(out / f"{model}_leave_city.csv", index=False)
    audit_model_support(data, fits, model, out, options)
    print(model + ": " + "; ".join(f"{r['contrast']}={r['estimate_ppb']:.3f} "
          f"({r['n_estimable_cities']}/11 cities)" for r in summary), flush=True)
    return summary


def point_models(panel, model, out, years=tuple(range(2019, 2025)), **options):
    """Publish every planned point estimate/support first; no bootstrap results yet."""
    data = panel[panel.year.isin(years)]
    fits = [fit_city(data[data.city.eq(city)], years=years, **options) for city in CITIES]
    points = np.stack([f["point"] for f in fits])
    rows, cityrows = [], []
    for k, contrast in enumerate(fits[0]["names"]):
        cp = points[:, k]
        identified = np.isfinite(cp).all()
        estimate = float(np.mean(cp))
        margin = float(t.ppf(.975, 10) * cp.std(ddof=1) / np.sqrt(11)) if identified else np.nan
        row = dict(model=model, contrast=contrast, estimate_ppb=estimate,
            status="estimable_all_11_cities" if identified else "unavailable_all_11_city_target",
            cross_city_summary_lower=estimate-margin, cross_city_summary_upper=estimate+margin,
            cross_city_summary_note=SUMMARY_NOTE, n_cities=11,
            n_estimable_cities=int(np.isfinite(cp).sum()),
            missing_cities=";".join(c for c, v in zip(CITIES, cp) if not np.isfinite(v)),
            uncertainty_status="point_stage_year_diagnostics_pending")
        for field in ["n_station_days", "n_city_days", "n_strata", "n_episode_station_days", "n_episode_city_days", "n_episodes"]:
            row[field] = sum(f["diagnostics"][field] for f in fits)
        rows.append(row)
        for i, (city, fit) in enumerate(zip(CITIES, fits)):
            cityrows.append(dict(model=model, contrast=contrast, city=city,
                estimate_ppb=cp[i], estimable=bool(np.isfinite(cp[i])), **fit["diagnostics"]))
    pd.DataFrame(rows).to_csv(out / f"{model}_point_summary.csv", index=False)
    pd.DataFrame(cityrows).to_csv(out / f"{model}_point_city_estimates.csv", index=False)
    audit_model_support(data, fits, model, out, options)
    print("POINT " + model + ": " + "; ".join(f"{r['contrast']}={r['estimate_ppb']:.3f} "
          f"({r['n_estimable_cities']}/11 cities)" for r in rows), flush=True)
    return rows


def audit_model_support(data, fits, model, out, options):
    """Keep selected station-days, supported city-days and event denominators distinct."""
    city_rows, event_rows = [], []
    selected_all = []
    for city, fit in zip(CITIES, fits):
        original, selected = data[data.city.eq(city)], fit["rows"]
        selected_all.append(selected)
        episode = original[original.episode_id.ne("")]
        chosen = selected[selected.episode_id.ne("")]
        city_rows.append(dict(model=model, city=city,
            input_station_days=len(original), input_city_days=original.date.nunique(),
            input_episode_station_days=len(episode), input_episode_city_days=episode.date.nunique(),
            input_observed_events=episode.episode_id.nunique(),
            comparator=options.get("comparator", "multicategory"),
            persistent_only=options.get("persistent", False), **fit["diagnostics"]))
        for eid, eg in episode.groupby("episode_id"):
            kept = chosen[chosen.episode_id.eq(eid)]
            event_rows.append(dict(model=model, city=city, year=int(eg.year.iloc[0]), episode_id=eid,
                observed_station_days=len(eg), selected_station_days=len(kept),
                observed_city_days=eg.date.nunique(), selected_city_days=kept.date.nunique(),
                any_selected_site_day=bool(len(kept)),
                every_observed_site_day_selected=len(eg) == len(kept),
                every_observed_city_day_has_a_selected_site=eg.date.nunique() == kept.date.nunique()))
    pd.DataFrame(city_rows).to_csv(out / f"{model}_support_by_city.csv", index=False)
    pd.DataFrame(event_rows).to_csv(out / f"{model}_support_by_event.csv", index=False)
    if options.get("comparator"):
        used = pd.concat(selected_all, ignore_index=True)
        cols = ["city", "station_id", "date", "stratum", "regime", "episode_id", "weight",
                "pure_wind_run_days", "persistent_wind_only"]
        used[cols].to_csv(out / f"{model}_selected_station_days.csv", index=False)
        strata = used.groupby(["city", "stratum"]).agg(
            station_days=("date", "size"), city_dates=("date", "nunique"),
            episode_station_days=("regime", lambda s: int(s.eq("episode").sum())),
            comparator_station_days=("regime", lambda s: int(s.ne("episode").sum())))
        strata.to_csv(out / f"{model}_selected_strata.csv")


def episode_support(panel, weather, events, out, definition):
    """Weather-event denominators include wholly unobserved episodes (e.g., extension)."""
    rows, summaries = [], []
    for comparator, persistent in [("neither", False), ("wind_only", False), ("wind_only", True)]:
        comp_name = "persistent_wind_only" if persistent else comparator
        selected = pd.concat([select_rows(g, comparator=comparator, persistent=persistent)
                              for _, g in panel.groupby("city")], ignore_index=True)
        for event in events.itertuples():
            observed = panel[panel.city.eq(event.city) & panel.episode_id.eq(event.episode_id)]
            chosen = selected[selected.city.eq(event.city) & selected.episode_id.eq(event.episode_id)]
            rows.append(dict(definition=definition, comparator=comp_name, city=event.city,
                year=event.year, episode_id=event.episode_id, weather_days=event.duration_days,
                observed_city_days=observed.date.nunique(), observed_station_days=len(observed),
                supported_city_days=chosen.date.nunique(), supported_station_days=len(chosen),
                all_weather_days_have_observation=observed.date.nunique() == event.duration_days,
                all_weather_days_have_supported_site=chosen.date.nunique() == event.duration_days,
                all_observed_station_days_supported=bool(len(observed)) and len(observed) == len(chosen)))
        for city in CITIES:
            for year in range(2019, 2026):
                g = selected[selected.city.eq(city) & selected.year.eq(year)]
                summaries.append(dict(definition=definition, comparator=comp_name, city=city, year=year,
                    supported_station_days=len(g), supported_strata=g.stratum.nunique(),
                    supported_city_days=g.date.nunique(),
                    supported_episode_station_days=int(g.regime.eq("episode").sum()),
                    supported_episode_city_days=g.loc[g.regime.eq("episode"), "date"].nunique(),
                    supported_events=g.loc[g.episode_id.ne(""), "episode_id"].nunique()))
    pd.DataFrame(rows).to_csv(out / f"{definition}_event_support.csv", index=False)
    pd.DataFrame(summaries).to_csv(out / f"{definition}_binary_support_city_year.csv", index=False)


def distribution(values):
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    if not len(x):
        return dict(n=0, mean=np.nan, median=np.nan, q25=np.nan, q75=np.nan,
                    minimum=np.nan, maximum=np.nan, sd=np.nan)
    return dict(n=len(x), mean=float(np.mean(x)), median=float(np.median(x)),
                q25=float(np.quantile(x, .25)), q75=float(np.quantile(x, .75)),
                minimum=float(np.min(x)), maximum=float(np.max(x)),
                sd=float(np.std(x, ddof=1)) if len(x) > 1 else np.nan)


def descriptive_tables(panel, weather, run_manifest, events, out):
    city_daily = panel.groupby(["city", "date"], as_index=False).agg(
        no2_ppb=("no2_ppb", "mean"), n_available_sites=("station_id", "nunique"))
    city_daily = city_daily.merge(weather, on=["city", "date"], validate="one_to_one")
    city_daily.to_csv(out / "descriptive_city_daily.csv", index=False)
    rows, counts = [], []
    fields = ["no2_ppb", "n_available_sites"] + WEATHER_FIELDS + ["pure_wind_run_days", "low_wind_run_days"]
    for period, years in [("2019_2024", range(2019, 2025)), ("2025", [2025])]:
        obs = city_daily[city_daily.year.isin(years)]
        sites = panel[panel.year.isin(years)]
        for label in ["regime", "regime_factorial", "wind_duration_class"]:
            for (city, regime), g in obs.groupby(["city", label], sort=True):
                station_group = sites[sites.city.eq(city) & sites[label].eq(regime)]
                counts.append(dict(period=period, classification=label, city=city, regime=regime,
                    city_days=len(g), station_days=len(station_group),
                    sites=station_group.station_id.nunique(),
                    events=g.loc[g.episode_id.ne(""), "episode_id"].nunique()))
                for field in fields:
                    rows.append(dict(period=period, classification=label, city=city, regime=regime,
                        variable=field, **distribution(g[field])))
            # Meteorology-only distributions make observation availability explicit.
            for (city, regime), g in weather[weather.warm & weather.year.isin(years)].groupby(["city", label]):
                for field in WEATHER_FIELDS + ["pure_wind_run_days", "low_wind_run_days"]:
                    rows.append(dict(period=period, classification=label + "_weather_calendar",
                        city=city, regime=regime, variable=field, **distribution(g[field])))
    pd.DataFrame(counts).to_csv(out / "descriptive_counts_city_regime.csv", index=False)
    pd.DataFrame(rows).to_csv(out / "descriptive_distributions_city_regime.csv", index=False)
    run_rows = []
    for (city, year, kind), g in run_manifest.groupby(["city", "year", "run_type"]):
        run_rows.append(dict(city=city, year=year, run_type=kind,
            isolated_runs=int(g.duration_days.eq(1).sum()), persistent_runs=int(g.duration_days.ge(2).sum()),
            weather_days=int(g.duration_days.sum()), **distribution(g.duration_days)))
    pd.DataFrame(run_rows).to_csv(out / "low_wind_run_length_distributions.csv", index=False)
    episode_counts = events.groupby(["city", "year"]).size().reindex(
        pd.MultiIndex.from_product([CITIES, range(2019, 2026)], names=["city", "year"]), fill_value=0)
    episode_counts.rename("weather_episodes").to_csv(out / "episode_counts_city_year.csv")


def validate_inputs(root):
    weather_path, station_path = root / "weather/weather_daily.csv", root / "stations/station_daily.csv"
    for path in [weather_path, station_path]:
        if not path.is_file():
            raise FileNotFoundError(f"Aligned inputs not ready: {path}")
    before = {"weather/weather_daily.csv": sha256(weather_path), "stations/station_daily.csv": sha256(station_path)}
    weather = pd.read_csv(weather_path, parse_dates=["date"])
    stations = pd.read_csv(station_path, parse_dates=["date"], dtype={"station_id": str})
    if len(weather) != 28127 or set(weather.city) != set(CITIES):
        raise ValueError("Must have exactly 28127 complete days for the 11 fixed cities before fitting")
    expected = pd.date_range("2019-01-01", "2025-12-31", freq="D")
    for city, g in weather.groupby("city"):
        if not np.array_equal(g.date.sort_values().to_numpy(), expected.to_numpy()):
            raise ValueError(f"Missing, repeated or out-of-frame weather day: {city}")
    if weather.duplicated(["city", "date"]).any() or stations.duplicated(["city", "date", "station_id"]).any():
        raise ValueError("Duplicate input keys")
    if not np.isfinite(weather[WEATHER_FIELDS].to_numpy(float)).all():
        raise ValueError("Incomplete weather; no model fitting or imputation permitted")
    if not np.isfinite(stations.no2_ppb.to_numpy(float)).all() or stations.station_id.isna().any():
        raise ValueError("Station outcomes or site IDs incomplete")
    if set(stations.city) != set(CITIES):
        raise ValueError("Station input must contain the fixed 11 cities")
    if (weather.precipitation_sum < 0).any() or (weather.wind_speed_10m_mean < 0).any():
        raise ValueError("Invalid precipitation or speed")
    if "min_observation_percent" in stations and (stations.min_observation_percent < 75).any():
        raise ValueError("Station coverage rule violated")
    if "distance_km" in stations and (stations.distance_km > 25).any():
        raise ValueError("Station radius rule violated")
    audit_path = root / "provenance/time_alignment_audit.json"
    if audit_path.exists():
        alignment = json.loads(audit_path.read_text(encoding="utf-8"))
        audits = alignment["weather"]
        if len(audits) != 11 or not all(a["all_days_24_instant_and_24_accumulation_values"]
                                     and a["missing_hourly_values"] == 0 for a in audits):
            raise ValueError("Time-alignment completion gate not passed")
        before["provenance/time_alignment_audit.json"] = sha256(audit_path)
    return weather, stations, before


def make_panel(stations, weather):
    panel = stations[["city", "date", "station_id", "no2_ppb"]].merge(
        weather, on=["city", "date"], how="left", validate="many_to_one", indicator=True)
    if not panel._merge.eq("both").all():
        raise ValueError("Unmatched station dates")
    panel = panel[panel.warm].drop(columns="_merge").copy()
    counts = panel.groupby(["city", "station_id", "year"]).date.transform("nunique")
    panel["core_station_year"] = counts.ge(172)
    return panel


def validate_output_path(input_root, output):
    """Pure path validation, including portable relative paths; never source directories."""
    output_path, input_path = output.resolve(), input_root.resolve()
    protected = [input_path / name for name in ["weather", "stations", "provenance", "raw", "archive"]]
    if (output_path == input_path or output_path in input_path.parents
            or output_path == Path(output_path.anchor)
            or any(output_path == p or p in output_path.parents for p in protected)
            or any(part.lower() in {"raw", "archive"} for part in output_path.parts)):
        raise ValueError("Output must be a dedicated analysis directory, not an input/raw/archive directory")
    return output_path


def verify_saved_analysis(out):
    """Audit saved computations without fitting/reselecting models or replacing estimates.

    Full fixed-city synchronous replicates are rebuilt from saved sufficient statistics.
    The diagnostic report does not average available cities or change any sample.
    """
    summary = pd.read_csv(out / "model_summary.csv")
    points = pd.read_csv(out / "point_model_summary.csv")
    join = summary.merge(points[["model", "contrast", "estimate_ppb"]], on=["model", "contrast"],
                         validate="one_to_one", suffixes=("", "_point_stage"))
    np.testing.assert_allclose(join.estimate_ppb, join.estimate_ppb_point_stage, atol=1e-12, equal_nan=True)
    assert len(summary) == 98 and summary.model.nunique() == 20
    review_rows, deletion_rows = [], []
    diagnostics_checked = replicates_checked = 0
    max_error = 0.
    for model in summary.model.unique():
        stats = np.load(out / f"{model}_sufficient_statistics.npz")
        saved = np.load(out / f"{model}_bootstrap_draws.npz")
        boot = pd.read_csv(out / f"{model}_bootstrap_diagnostics.csv")
        city_table = pd.read_csv(out / f"{model}_city_estimates.csv")
        deletions = pd.read_csv(out / f"{model}_leave_year_by_city.csv")
        counts = saved["synchronized_year_counts"]
        assert counts.shape == (5000, len(stats["years"]))
        assert np.all(counts.sum(axis=1) == len(stats["years"]))
        rebuilt = []
        for i, city in enumerate(stats["cities"]):
            fit = dict(blocks=stats["blocks"][i], q=stats["q"][i], C=stats["C"], names=stats["contrasts"])
            rebuilt.append(resample_years(fit, counts))
            estimate = coefficients(fit["blocks"].sum(axis=0), fit["q"].sum(axis=0), fit["C"])
            for k, contrast in enumerate(stats["contrasts"]):
                row = city_table[city_table.city.eq(city) & city_table.contrast.eq(contrast)].iloc[0]
                np.testing.assert_allclose(estimate[k], row.estimate_ppb, atol=1e-10, equal_nan=True)
                selected = deletions[deletions.city.eq(city) & deletions.contrast.eq(contrast)]
                if row.n_episode_station_days == 0 and contrast.startswith("episode"):
                    reason = "no_retained_episode_station_days_in_this_city_and_specification"
                elif not row.estimable:
                    reason = "contrast_not_in_within_design_row_space_after_adjustment"
                elif row.condition_number > 1e6:
                    reason = "estimable_but_ill_conditioned_no_sample_or_model_change"
                else:
                    reason = "estimable"
                S = fit["blocks"].sum(axis=0)
                c = fit["C"][k]
                projection_error = float(np.max(np.abs(c - c @ np.linalg.pinv(S, rcond=1e-11) @ S)))
                failed_years = selected.loc[~selected.estimable, "omitted_year"].astype(str).tolist()
                review_rows.append(dict(model=model, city=city, contrast=contrast, estimate_ppb=row.estimate_ppb,
                    estimable=row.estimable, diagnostic_reason=reason,
                    support_station_days=row.n_station_days, strata=row.n_strata,
                    unique_weather_days=row.n_city_days, episode_station_days=row.n_episode_station_days,
                    episode_city_days=row.n_episode_city_days, observed_episodes=row.n_episodes,
                    within_rank=row.rank_at_pinv_tolerance, parameters=row.parameters,
                    condition_number=row.condition_number, contrast_projection_max_error=projection_error,
                    jackknife_status=row.jackknife_status, jackknife_se=row.jackknife_se,
                    jackknife_lower=row.jackknife_lower, jackknife_upper=row.jackknife_upper,
                    delete_year_attempted=len(selected), delete_year_unavailable=int((~selected.estimable).sum()),
                    unavailable_when_omitting_years=";".join(failed_years),
                    city_year_bootstrap_attempted=row.bootstrap_attempted,
                    city_year_bootstrap_valid=row.bootstrap_valid, city_year_bootstrap_failed=row.bootstrap_failed,
                    note="Weather is common to sites within a city-date; additional stations are not independent weather replicates."))
                for omitted in selected.itertuples():
                    deletion_rows.append(dict(model=model, city=city, contrast=contrast,
                        omitted_year=omitted.omitted_year, estimate_ppb=omitted.estimate_ppb,
                        estimable=omitted.estimable))
        rebuilt = np.stack(rebuilt).mean(axis=0)
        np.testing.assert_allclose(rebuilt, saved["synchronized_year_fixed_cities"], atol=1e-10, equal_nan=True)
        finite = np.isfinite(rebuilt)
        if finite.any():
            max_error = max(max_error, float(np.max(np.abs(rebuilt[finite] - saved["synchronized_year_fixed_cities"][finite]))))
        for row in boot.itertuples():
            k = list(stats["contrasts"]).index(row.contrast)
            samples = saved[row.scheme][:, k]
            nv = int(np.isfinite(samples).sum())
            assert len(samples) == row.attempted == 5000 and nv == row.valid
            assert row.failed == row.attempted - nv
            source_row = summary[summary.model.eq(model) & summary.contrast.eq(row.contrast)].iloc[0]
            allowed = source_row.n_estimable_cities == 11
            temporal = len(stats["years"]) >= 2 or row.scheme != "synchronized_year_fixed_cities"
            lo, hi, _ = diagnostic_interval(samples, allowed, temporal)
            np.testing.assert_allclose([lo, hi], [row.conditional_lower, row.conditional_upper],
                                       atol=1e-10, equal_nan=True)
            diagnostics_checked += 1
            replicates_checked += len(samples)
        stats.close(); saved.close()
    review = pd.DataFrame(review_rows)
    review.to_csv(out / "city_estimability_review.csv", index=False)
    direct = review[review.model.isin(["direct_episode_neither", "direct_episode_wind",
        "persistent_wind_comparator", "direct_wind_spline", "extension_2025", "p80_p30_min3_sep7"])]
    direct.to_csv(out / "restricted_support_review.csv", index=False)
    pd.DataFrame(deletion_rows).to_csv(out / "all_city_leave_year_diagnostics.csv", index=False)
    original = json.loads((out / "analysis_audit.json").read_text(encoding="utf-8"))
    helper = Path(__file__).with_name("calendar_station_analysis.py")
    assert sha256(helper) == original["legacy_helper_sha256"]
    result = dict(passed=True, models=20, pooled_contrasts=98, city_contrasts=len(review),
        scheme_contrast_diagnostics_checked=diagnostics_checked,
        saved_replicate_contrast_values_checked=replicates_checked,
        fixed_city_sync_reconstruction_max_absolute_error=max_error,
        all_point_stage_estimates_match=True, all_unavailable_points_preserved=True,
        all_attempts_including_failures_accounted=True, legacy_helper_unchanged=True,
        no_available_city_pooled_values_created=True, no_model_or_sample_changes=True,
        audit_script_sha256=sha256(Path(__file__)), executed_analysis_script_sha256=original["script_sha256"],
        review_note="Sparse direct/persistent models describe support limits, not general robustness confirmation.")
    dump(out / "verification_audit.json", result)
    files = sorted(p for p in out.iterdir() if p.is_file() and p.name != "output_manifest.json")
    dump(out / "output_manifest.json", {p.name: dict(bytes=p.stat().st_size, sha256=sha256(p)) for p in files})
    return result


def run_tests():
    import unittest
    from test_wasp_analysis import WaspAnalysisTests
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(WaspAnalysisTests)
    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise RuntimeError("Noiseless/statistical tests failed; no formal fits permitted")
    return dict(tests_run=result.testsRun, failures=len(result.failures), errors=len(result.errors),
                legacy_tests=legacy_self_test())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=ROOT / "analysis")
    parser.add_argument("--bootstrap", type=int, default=5000)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--verify-only", action="store_true", help="Audit completed files; no refitting or model changes")
    parser.add_argument("--allow-existing", action="store_true", help="Explicitly rerun only this new analysis directory")
    args = parser.parse_args()
    tests = run_tests()
    if args.self_test:
        print(json.dumps(tests)); return
    output_path = validate_output_path(args.input_root, args.output)
    if args.verify_only:
        print(json.dumps(verify_saved_analysis(output_path))); return
    if args.bootstrap != 5000:
        raise ValueError("Publication-grade run is prespecified at 5000 attempts, not a tunable parameter")
    if shutil.disk_usage(output_path.anchor).free < 2 * 1024**3:
        raise RuntimeError("Less than 2 GiB available on output drive")
    if (args.output / "analysis_audit.json").exists() and not args.allow_existing:
        raise RuntimeError("Completed output exists; use explicit --allow-existing for an audited rerun")
    started = time.perf_counter()
    raw, stations, hashes = validate_inputs(args.input_root)
    print(f"Input gate PASSED: {len(raw)} weather city-days, {len(stations)} station-days", flush=True)
    args.output.mkdir(parents=True, exist_ok=True)
    plan = Path(__file__).resolve().parents[1] / "WASP_REVISION_PLAN_20260923.md"
    frozen = dict(started_utc=datetime.now(timezone.utc).isoformat(), seed=SEED, bootstrap_attempts=args.bootstrap,
        input_sha256=hashes, plan_sha256=sha256(plan) if plan.exists() else None,
        script_sha256=sha256(Path(__file__)), legacy_helper_sha256=sha256(Path(__file__).with_name("calendar_station_analysis.py")),
        tests=tests, definitions=[asdict(d) for d in DEFINITIONS],
        target="equal-weight mean of 11 fixed city associations, retrospective revision",
        direct_comparisons="episode plus named comparator rows only, both-present site/year/month/weekday strata",
        wind_spline_reference="unique 2019-2024 warm days satisfying BASE P30 wind threshold, weather only",
        persistent_comparator="at least 2 contiguous warm-season pure wind-only days on weather calendar; isolated excluded",
        uncertainty_notes=[SUMMARY_NOTE, TEMPORAL_NOTE,
            "Year blocks are common calendar years for all cities, including zero-data blocks where applicable.",
            "Hierarchical duplicate city occurrences get independent year draws; synchronized-fixed retains every city.",
            "Unavailable 11-city point estimates suppress intervals even when a resample omits that city.",
            "For 2025, no year-based interval; city resampling describes city dispersion only."],
        versions={p: importlib.metadata.version(p) for p in ["numpy", "pandas", "scipy", "patsy"]},
        python=sys.version)
    dump(args.output / "run_specification.json", frozen)
    base, thresholds, events, runs = label_weather(raw)
    weather, splines = add_splines(base)
    dump(args.output / "spline_specifications.json", splines)
    weather.to_csv(args.output / "analysis_weather_daily.csv", index=False)
    thresholds.to_csv(args.output / "thresholds.csv", index=False)
    events.to_csv(args.output / "episode_manifest.csv", index=False)
    runs.to_csv(args.output / "low_wind_run_manifest.csv", index=False)
    panel = make_panel(stations, weather)
    panel.to_csv(args.output / "analysis_station_daily.csv", index=False)
    coverage = panel.groupby(["city", "station_id", "year"], as_index=False).agg(
        qualifying_warm_days=("date", "nunique"), high_coverage=("core_station_year", "all"))
    coverage.to_csv(args.output / "station_year_coverage.csv", index=False)
    descriptive_tables(panel, weather, runs, events, args.output)
    episode_support(panel, weather, events, args.output, DEFINITIONS[0].name)
    summaries, specs = [], []
    jobs = [
        ("calendar_only", dict(adjusted=False)),
        ("weather_adjusted", dict(adjusted=True)),
        ("direct_episode_neither", dict(comparator="neither")),
        ("direct_episode_wind", dict(comparator="wind_only")),
        ("persistent_wind_comparator", dict(comparator="wind_only", persistent=True)),
        ("direct_wind_spline", dict(comparator="wind_only", wind_adjust=True)),
        ("four_weather_regimes", dict(label="regime_factorial")),
        ("core_monitors", dict(core=True)),
        ("equal_station_weights", dict(equal_site=True)),
        ("exclude_2020", dict(years=tuple(y for y in range(2019, 2025) if y != 2020))),
        ("period_2019_2022", dict(years=tuple(range(2019, 2023)))),
        ("period_2023_2024", dict(years=(2023, 2024))),
        ("extension_2025", dict(years=(2025,))),
        ("phase_calendar_secondary", dict(adjusted=False, label="phase")),
        ("phase_adjusted_secondary", dict(label="phase")),
    ]
    all_jobs = [(name, panel, options, DEFINITIONS[0].name) for name, options in jobs]
    median = panel.groupby(["city", "date"], as_index=False).no2_ppb.median()
    median["station_id"] = "CITY_MEDIAN"
    median = make_panel(median, weather)
    all_jobs.append(("city_median", median, {}, DEFINITIONS[0].name))
    feature_cols = [c for c in weather if c.startswith("met_") or c.startswith("wind_adjust_")]
    for definition in DEFINITIONS[1:]:
        alt, th, ev, run = label_weather(raw, definition)
        alt = alt.merge(weather[["city", "date"] + feature_cols], on=["city", "date"], validate="one_to_one")
        alt.to_csv(args.output / f"{definition.name}_weather.csv", index=False)
        th.to_csv(args.output / f"{definition.name}_thresholds.csv", index=False)
        ev.to_csv(args.output / f"{definition.name}_events.csv", index=False)
        alt_panel = make_panel(stations, alt)
        episode_support(alt_panel, alt, ev, args.output, definition.name)
        all_jobs.append((definition.name, alt_panel, {}, definition.name))
    # Point estimates for the complete matrix precede all bootstrap calculations.
    point_rows = []
    for name, data, options, definition_name in all_jobs:
        specs.append(dict(model=name, definition=definition_name, **options))
        point_rows.extend(point_models(data, name, args.output, **options))
        pd.DataFrame(point_rows).to_csv(args.output / "point_model_summary.csv", index=False)
    dump(args.output / "model_specifications.json", specs)
    print("All point/support tables saved. Starting 5000-attempt bootstrap matrix.", flush=True)
    for name, data, options, definition_name in all_jobs:
        summaries.extend(pooled_models(data, name, args.output, args.bootstrap, **options))
        pd.DataFrame(summaries).to_csv(args.output / "model_summary.csv", index=False)
    # Numeric audit: all-city availability, every requested bootstrap, exact fixed-city resampling.
    table = pd.DataFrame(summaries)
    assert table.n_cities.eq(11).all()
    assert table.loc[table.n_estimable_cities.lt(11), "estimate_ppb"].isna().all()
    assert table.loc[table.n_estimable_cities.eq(11), "estimate_ppb"].notna().all()
    for scheme in ["hierarchical_city_independent_year", "synchronized_year_fixed_cities",
                   "synchronized_year_resampled_cities"]:
        assert (table[scheme + "_valid"] + table[scheme + "_failed"]).eq(args.bootstrap).all()
    for rel, original in hashes.items():
        if sha256(args.input_root / rel) != original:
            raise RuntimeError("Input changed during fits; outputs cannot be treated as frozen")
    table.to_csv(args.output / "model_summary.csv", index=False)
    dump(args.output / "model_specifications.json", specs)
    unavailable = table[table.n_estimable_cities.lt(11)][["model", "contrast", "n_estimable_cities", "missing_cities"]]
    audit = dict(**frozen, completed_utc=datetime.now(timezone.utc).isoformat(), elapsed_seconds=time.perf_counter() - started,
        completed=True, weather_city_days=len(raw), input_station_days=len(stations),
        warm_station_days=len(panel), warm_city_days=panel[["city", "date"]].drop_duplicates().shape[0],
        models=len(specs), pooled_contrasts=len(table),
        episode_counts=events.groupby("year").size().to_dict(),
        unavailable_all_city_contrasts=unavailable.to_dict("records"),
        all_input_hashes_unchanged=True, all_bootstrap_attempts_accounted=True)
    dump(args.output / "analysis_audit.json", audit)
    verify_saved_analysis(args.output)
    files = sorted(p for p in args.output.iterdir() if p.is_file() and p.name != "output_manifest.json")
    dump(args.output / "output_manifest.json", {p.name: dict(bytes=p.stat().st_size, sha256=sha256(p)) for p in files})
    print(json.dumps(clean_json({k: audit[k] for k in ["completed", "models", "pooled_contrasts", "episode_counts",
                                                     "elapsed_seconds", "unavailable_all_city_contrasts"]})), flush=True)


if __name__ == "__main__":
    main()
