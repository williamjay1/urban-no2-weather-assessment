"""Reproducible calendar-stratified analysis of measured surface NO2.

No NO2 value enters episode definitions, spline knots, or calendar support rules.
Use --input-root to reproduce from the public derived-data package.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import hashlib

import numpy as np
import pandas as pd
from patsy import dmatrix, build_design_matrices
from scipy.stats import t

DEFAULT = Path(__file__).resolve().parents[1] / "data"
SEED = 20260922
MET = ["relative_humidity_2m_mean", "precipitation_sum", "shortwave_radiation_sum", "wind_direction_10m_dominant"]
REGIMES = ["episode", "heat_only", "wind_only", "other_compound"]


def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")


def runs(dates):
    dates = sorted(pd.to_datetime(dates))
    out, block = [], []
    for date in dates:
        if block and (date - block[-1]).days != 1:
            if len(block) >= 2:
                out.append((block[0], block[-1]))
            block = []
        block.append(date)
    if len(block) >= 2:
        out.append((block[0], block[-1]))
    return out


def prepare_weather(weather):
    weather = weather.copy().sort_values(["city", "date"]).reset_index(drop=True)
    weather["year"] = weather.date.dt.year
    weather["month"] = weather.date.dt.month
    weather["weekday"] = weather.date.dt.weekday
    weather["warm"] = weather.month.between(4, 10)
    weather["episode_id"] = ""
    weather["unrestricted_episode"] = False
    weather["phase"] = "background"
    thresholds, eventrows, spline_specs = [], [], {}
    for city, group in weather.groupby("city", sort=True):
        dev = group[group.year.between(2019, 2022) & group.warm]
        heat = float(dev.temperature_2m_max.quantile(.8))
        wind = float(dev.wind_speed_10m_mean.quantile(.3))
        thresholds.append(dict(city=city, heat_q80_c=heat, wind_q30_kmh=wind, threshold_days=len(dev)))
        hot = group.temperature_2m_max.ge(heat)
        calm = group.wind_speed_10m_mean.le(wind)
        weather.loc[group.index, "hot"] = hot
        weather.loc[group.index, "calm"] = calm
        compound = hot & calm & group.warm
        previous = None
        retained = []
        for start, end in runs(group.loc[compound, "date"]):
            mask = weather.city.eq(city) & weather.date.between(start, end)
            weather.loc[mask, "unrestricted_episode"] = True
            if previous is not None and (start - previous).days < 7:
                continue
            previous = start
            eid = city.lower().replace(" ", "_") + "_" + start.date().isoformat()
            weather.loc[mask, "episode_id"] = eid
            retained.append((start, end))
            eventrows.append(dict(city=city, year=start.year, episode_id=eid, start_date=start.date().isoformat(), end_date=end.date().isoformat(), duration_days=(end-start).days+1))
        # Precedence: background < lead < post3-6 < post1-2 < other compound < episode.
        for label, bounds in [("pre1_6", (-6, -1)), ("post3_6", (3, 6)), ("post1_2", (1, 2))]:
            for start, end in retained:
                anchor = start if label.startswith("pre") else end
                mask = weather.city.eq(city) & weather.date.between(anchor+pd.Timedelta(days=bounds[0]), anchor+pd.Timedelta(days=bounds[1]))
                weather.loc[mask, "phase"] = label
        weather.loc[group.index[compound], "phase"] = "other_compound"
        weather.loc[weather.city.eq(city) & weather.episode_id.ne(""), "phase"] = "episode"
        # All knots are determined by unique city-days of weather, never outcomes.
        spline_specs[city] = {}
        for field in MET[:3]:
            x = group[field].astype(float).to_numpy()
            if field == "precipitation_sum":
                x = np.log1p(np.maximum(0, x))
            train = x[group.year.le(2024).to_numpy() & group.warm.to_numpy()]
            train = train[np.isfinite(train)]
            positive = train[train > 0] if field == "precipitation_sum" else train
            knots = np.unique(np.quantile(positive, [1/3, 2/3]))
            knots = knots[(knots > train.min()) & (knots < train.max())]
            if len(knots) != 2:
                raise ValueError(f"Cannot define 3-df natural spline for {city}/{field}")
            formula = "cr(x, knots=knots, lower_bound=lower, upper_bound=upper, constraints='center') - 1"
            design = dmatrix(formula, dict(x=train, knots=knots, lower=float(train.min()), upper=float(train.max())))
            vals = np.full((len(x), 3), np.nan)
            ok = np.isfinite(x)
            vals[ok] = np.asarray(build_design_matrices([design.design_info], dict(x=x[ok], knots=knots, lower=float(train.min()), upper=float(train.max())))[0])
            for k in range(3):
                weather.loc[group.index, f"met_{field}_{k}"] = vals[:, k]
            spline_specs[city][field] = dict(knots=knots.tolist(), lower=float(train.min()), upper=float(train.max()), df=3, log1p=field=="precipitation_sum")
    weather["hot"] = weather.hot.astype(bool)
    weather["calm"] = weather.calm.astype(bool)
    weather["regime"] = np.select(
        [weather.episode_id.ne(""), weather.hot & weather.calm, weather.hot, weather.calm],
        ["episode", "other_compound", "heat_only", "wind_only"], default="neither")
    weather["regime_unrestricted"] = np.where(weather.unrestricted_episode, "episode", np.where(weather.hot & weather.calm, "other_compound", weather.regime))
    weather["regime_factorial"] = np.where(weather.hot & weather.calm, "compound", weather.regime)
    angle = np.deg2rad(weather.wind_direction_10m_dominant)
    weather["met_wind_sin"] = np.sin(angle)
    weather["met_wind_cos"] = np.cos(angle)
    return weather, pd.DataFrame(thresholds), pd.DataFrame(eventrows), spline_specs


def within_transform(x, y, weights, groups):
    ids, unique = pd.factorize(groups, sort=True)
    totals = np.bincount(ids, weights=weights, minlength=len(unique))
    sums = np.zeros((len(unique), x.shape[1]))
    np.add.at(sums, ids, x * weights[:, None])
    ysum = np.bincount(ids, weights=weights*y, minlength=len(unique))
    return x - (sums / totals[:, None])[ids], y - (ysum / totals)[ids]


def coefficients(S, q, C):
    inv = np.linalg.pinv(S, rcond=1e-11)
    beta = inv @ q[..., None]
    estimates = np.einsum("kp,...pj->...k", C, beta)
    projection = C - np.einsum("kp,...pq,...qr->...kr", C, inv, S)
    estimates[np.max(np.abs(projection), axis=-1) > 1e-5] = np.nan
    return estimates


def design_contrasts(levels):
    names, contrasts = [], []
    for level in levels:
        c = np.zeros(len(levels)); c[levels.index(level)] = 1
        names.append(level + "_vs_reference"); contrasts.append(c)
    if "episode" in levels and "heat_only" in levels:
        for other in ["heat_only", "wind_only"]:
            c = np.zeros(len(levels)); c[levels.index("episode")] = 1; c[levels.index(other)] = -1
            names.append("episode_vs_" + other); contrasts.append(c)
    if "compound" in levels:
        c = np.zeros(len(levels)); c[levels.index("compound")] = 1
        c[levels.index("heat_only")] = -1; c[levels.index("wind_only")] = -1
        names.append("compound_additive_interaction"); contrasts.append(c)
    return names, np.array(contrasts)


def fit_city(df, adjusted=True, label="regime", direct=False, core=False, equal_site=False):
    levels = REGIMES if label.startswith("regime") else ["episode", "pre1_6", "post1_2", "post3_6", "other_compound"]
    if label == "regime_factorial":
        levels = ["compound", "heat_only", "wind_only"]
    df = df.copy()
    df["stratum"] = df.station_id.astype(str) + "_" + df.year.astype(str) + "_" + df.month.astype(str) + "_" + df.weekday.astype(str)
    if core:
        df = df[df.core_station_year]
    if direct:
        eligible = df.groupby("stratum")[label].agg(lambda x: {"episode", "neither"}.issubset(set(x)))
        df = df[df.stratum.isin(eligible[eligible].index)]
    # Single-observation strata cannot identify any within-stratum contrast.
    n = df.groupby("stratum").date.transform("nunique")
    df = df[n >= 2].copy()
    df["weight"] = 1.0 if equal_site else 1 / df.groupby("date").station_id.transform("nunique")
    metcols = [c for c in df if c.startswith("met_")]
    covcols = metcols if adjusted else []
    x = np.column_stack([(df[label] == lev).to_numpy(dtype=float) for lev in levels] + [df[c].to_numpy(float) for c in covcols])
    y, w = df.no2_ppb.to_numpy(float), df.weight.to_numpy(float)
    xw, yw = within_transform(x, y, w, df.stratum)
    names, C0 = design_contrasts(levels)
    C = np.pad(C0, ((0, 0), (0, len(covcols))))
    matrices, vectors = [], []
    years = sorted(df.year.unique().tolist())
    for year in years:
        take = df.year.eq(year).to_numpy()
        matrices.append((xw[take] * w[take, None]).T @ xw[take])
        vectors.append(xw[take].T @ (w[take] * yw[take]))
    blocks, q = np.array(matrices), np.array(vectors)
    S = blocks.sum(axis=0)
    est = coefficients(S, q.sum(axis=0), C)
    beta = np.linalg.pinv(S, rcond=1e-11) @ q.sum(axis=0)
    resid = yw - xw @ beta
    diagnostics = dict(n_station_days=len(df), n_city_days=df.date.nunique(), n_stations=df.station_id.nunique(), n_strata=df.stratum.nunique(), n_episode_days=df.loc[df.regime.eq("episode"), "date"].nunique(), n_episodes=df.loc[df.episode_id.ne(""), "episode_id"].nunique(), n_years=len(years), rank=int(np.linalg.matrix_rank(S)), parameters=len(beta), condition_number=float(np.linalg.cond(S)), weighted_rmse=float(np.sqrt(np.average(resid**2, weights=w))))
    for lev in levels:
        diagnostics["days_"+lev] = int(df.loc[df[label].eq(lev), "date"].nunique())
    return dict(blocks=blocks, q=q, years=years, C=C, names=names, point=est, diagnostics=diagnostics)


def resample_years(fit, counts):
    S = np.einsum("by,yij->bij", counts, fit["blocks"])
    q = counts @ fit["q"]
    return coefficients(S, q, fit["C"])


def pooled_models(panel, name, out, reps, years=(2019, 2024), **options):
    data = panel[panel.year.between(*years)].copy()
    fits = {city: fit_city(df, **options) for city, df in data.groupby("city", sort=True)}
    citynames = list(fits)
    names = fits[citynames[0]]["names"]
    rng = np.random.default_rng(SEED)
    per_city_draws, cityrows = [], []
    for city, fit in fits.items():
        ny = len(fit["years"])
        counts = rng.multinomial(ny, np.repeat(1/ny, ny), size=reps)
        draws = resample_years(fit, counts)
        per_city_draws.append(draws)
        deleted = []
        if ny >= 3:
            for leave in range(ny):
                keep = np.arange(ny) != leave
                deleted.append(coefficients(fit["blocks"][keep].sum(axis=0), fit["q"][keep].sum(axis=0), fit["C"]))
        deleted = np.array(deleted)
        for k, contrast in enumerate(names):
            valid = draws[np.isfinite(draws[:, k]), k]
            blo, bhi = np.quantile(valid, [.025, .975]) if ny >= 2 and len(valid) else [np.nan, np.nan]
            if ny >= 3 and np.isfinite(deleted[:, k]).all() and np.isfinite(fit["point"][k]):
                jack_se = np.sqrt((ny-1)/ny * np.sum((deleted[:, k]-deleted[:, k].mean())**2))
                margin = t.ppf(.975, ny-1)*jack_se
                lo, hi = fit["point"][k]-margin, fit["point"][k]+margin
                ci_status = "approximate_delete_one_year_jackknife_t"
            else:
                lo, hi = np.nan, np.nan
                ci_status = "unavailable: fewer than three years or nonidentifiable deletion"
            cityrows.append(dict(model=name, city=city, contrast=contrast, estimate_ppb=fit["point"][k], ci_lower=lo, ci_upper=hi, ci_status=ci_status, bootstrap_conditional_lower=blo, bootstrap_conditional_upper=bhi, bootstrap_status="conditional_on_estimability" if ny>=2 else "unavailable_single_year", valid_bootstrap=len(valid), **fit["diagnostics"]))
    pools = np.stack(per_city_draws)
    nc = len(fits)
    citysample = rng.integers(nc, size=(reps, nc))
    drawsample = rng.integers(reps, size=(reps, nc))
    draws = pools[citysample, drawsample].mean(axis=1)
    points = np.stack([f["point"] for f in fits.values()])
    summaries = []
    for k, contrast in enumerate(names):
        v = draws[np.isfinite(draws[:, k]), k]
        cp = points[:, k]
        identified = np.isfinite(cp).all()
        # A rare nuisance category can be absent in a restricted sample. Do not
        # replace its nonidentifiable coefficient by zero or silently omit a city.
        # Such an all-city contrast is explicitly unavailable, while estimable
        # contrasts in the very same model remain reportable.
        lo, hi = np.quantile(v, [.025, .975]) if identified and len(v) else (np.nan, np.nan)
        mean = float(cp.mean()) if identified else np.nan
        margin = float(t.ppf(.975, nc-1)*cp.std(ddof=1)/np.sqrt(nc)) if identified else np.nan
        loo = [(cp.sum()-x)/(nc-1) for x in cp] if identified else [np.nan]
        summaries.append(dict(model=name, contrast=contrast, status="estimable" if identified else "unavailable: at least one city contrast is not identifiable", estimate_ppb=mean, ci_lower=mean-margin, ci_upper=mean+margin, ci_method="approximate_cross_city_t_df_10", bootstrap_conditional_lower=float(lo), bootstrap_conditional_upper=float(hi), bootstrap_status="conditional_on_estimability" if years[0]!=years[1] else "city_resampling_only_no_within_year_uncertainty", n_cities=nc, n_estimable_cities=int(np.isfinite(cp).sum()), positive_cities=int((cp>0).sum()), valid_bootstrap=len(v), requested_bootstrap=reps, bootstrap_failure_fraction=1-len(v)/reps, leave_city_min=float(min(loo)), leave_city_max=float(max(loo)), year_start=years[0], year_end=years[1], station_days=int(sum(f["diagnostics"]["n_station_days"] for f in fits.values())), city_days=int(sum(f["diagnostics"]["n_city_days"] for f in fits.values())), episode_city_days=int(sum(f["diagnostics"]["n_episode_days"] for f in fits.values())), episodes=int(sum(f["diagnostics"]["n_episodes"] for f in fits.values()))))
    pd.DataFrame(cityrows).to_csv(out/f"{name}_city_estimates.csv", index=False)
    # Shared calendar-year resampling accounts for nationwide year shocks.
    same_years = all(f["years"] == fits[citynames[0]]["years"] for f in fits.values())
    if same_years:
        ny = len(fits[citynames[0]]["years"])
        counts = rng.multinomial(ny, np.repeat(1/ny, ny), size=reps)
        synced = np.stack([resample_years(f, counts) for f in fits.values()])
        ds = synced[citysample, np.arange(reps)[:, None]].mean(axis=1)
        for k, summary in enumerate(summaries):
            valid = ds[np.isfinite(ds[:, k]), k]
            lo, hi = np.quantile(valid, [.025, .975]) if summary["status"] == "estimable" and len(valid) else (np.nan, np.nan)
            summary.update(synchronized_conditional_lower=float(lo), synchronized_conditional_upper=float(hi), synchronized_valid_bootstrap=len(valid))
    yearrows = []
    if years[0] != years[1]:
        for year in range(years[0], years[1]+1):
            without = []
            for fit in fits.values():
                mask = np.array(fit["years"]) != year
                without.append(coefficients(fit["blocks"][mask].sum(axis=0), fit["q"][mask].sum(axis=0), fit["C"]))
            estimates = np.mean(without, axis=0)
            for k, contrast in enumerate(names):
                yearrows.append(dict(model=name, omitted_year=year, contrast=contrast, estimate_ppb=estimates[k]))
        pd.DataFrame(yearrows).to_csv(out/f"{name}_leave_year.csv", index=False)
    print(f"{name}: " + "; ".join(f"{r['contrast']} {r['estimate_ppb']:.3f} [{r['ci_lower']:.3f},{r['ci_upper']:.3f}]" for r in summaries), flush=True)
    return summaries


def support_audit(panel, events, out):
    df = panel.copy()
    df["stratum"] = df.city + "_" + df.station_id.astype(str) + "_" + df.year.astype(str) + "_" + df.month.astype(str) + "_" + df.weekday.astype(str)
    group = df.groupby("stratum")
    metadata = group.agg(n_dates=("date", "nunique"), n_episode=("regime", lambda x: int((x=="episode").sum())), n_neither=("regime", lambda x: int((x=="neither").sum())), n_noncompound=("regime", lambda x: int(x.isin(["neither", "heat_only", "wind_only"]).sum())))
    df = df.merge(metadata, on="stratum", how="left", validate="many_to_one")
    df["direct_support"] = df.n_neither.gt(0) & df.n_episode.gt(0)
    df["noncompound_support"] = df.n_noncompound.gt(0) & df.n_episode.gt(0)
    episode = df[df.episode_id.ne("")].groupby(["city", "year", "episode_id"]).agg(observed_episode_days=("date", "nunique"), n_station_days=("date", "size"), station_ids=("station_id", lambda x: ";".join(sorted(set(x.astype(str))))))
    supported = df[df.direct_support & df.episode_id.ne("")].groupby(["city", "year", "episode_id"]).date.nunique().rename("days_with_direct_support")
    broad = df[df.noncompound_support & df.episode_id.ne("")].groupby(["city", "year", "episode_id"]).date.nunique().rename("days_with_noncompound_support")
    audit = events.merge(episode.reset_index(), how="left", on=["city", "year", "episode_id"]).merge(supported.reset_index(), how="left", on=["city", "year", "episode_id"]).merge(broad.reset_index(), how="left", on=["city", "year", "episode_id"])
    numeric = ["observed_episode_days", "n_station_days", "days_with_direct_support", "days_with_noncompound_support"]
    audit[numeric] = audit[numeric].fillna(0).astype(int)
    audit.to_csv(out/"episode_calendar_support.csv", index=False)
    flow = []
    for city, part in df[df.year.le(2024)].groupby("city"):
        ev = audit[audit.city.eq(city) & audit.year.le(2024)]
        flow.append(dict(city=city, weather_episodes=len(ev), observed_episodes=int(ev.observed_episode_days.gt(0).sum()), episodes_any_direct_support=int(ev.days_with_direct_support.gt(0).sum()), episodes_full_direct_support=int(ev.days_with_direct_support.eq(ev.duration_days).sum()), station_days=len(part), city_days=part.date.nunique(), stations=part.station_id.nunique(), episode_city_days=part.loc[part.regime.eq("episode"), "date"].nunique(), direct_support_episode_days=part.loc[part.regime.eq("episode") & part.direct_support, "date"].nunique()))
    pd.DataFrame(flow).to_csv(out/"sample_support_by_city.csv", index=False)
    return flow


def historical_candidate_funnel(weather, events, out):
    """Outcome-blind diagnosis of losses under the superseded window design."""
    rows=[]
    for city, group in weather.groupby("city",sort=True):
        daily=group.set_index("date")
        cityevents=events[events.city.eq(city)]
        intervals=[(pd.Timestamp(r.start_date),pd.Timestamp(r.end_date)) for r in cityevents.itertuples()]
        for event in cityevents.itertuples():
            start=pd.Timestamp(event.start_date)
            dates=group.loc[group.year.eq(event.year)&group.month.eq(start.month)&group.weekday.eq(start.weekday()),"date"]
            counters=dict(calendar_candidates=0,episode_window_noncompound=0,full_window_noncompound=0,after_21day_embargo=0)
            for date in dates:
                counters["calendar_candidates"]+=1
                end=date+pd.Timedelta(days=event.duration_days-1)
                episode=daily.loc[date:end]
                if (episode.hot&episode.calm&episode.warm).any():
                    continue
                counters["episode_window_noncompound"]+=1
                full=daily.loc[date-pd.Timedelta(days=7):end+pd.Timedelta(days=6)]
                if len(full)!=event.duration_days+13 or (full.hot&full.calm&full.warm).any():
                    continue
                counters["full_window_noncompound"]+=1
                if any(a<=date<=b or min(abs((date-a).days),abs((date-b).days))<21 for a,b in intervals):
                    continue
                counters["after_21day_embargo"]+=1
            rows.append(dict(city=city,year=event.year,episode_id=event.episode_id,**counters))
    pd.DataFrame(rows).to_csv(out/"historical_matching_candidate_funnel.csv",index=False)


def self_test():
    rng = np.random.default_rng(11)
    n, p = 150, 3
    ids = np.repeat(np.arange(30), 5)
    x, y, w = rng.normal(size=(n,p)), rng.normal(size=n), rng.uniform(.2, 2, size=n)
    xd, yd = within_transform(x,y,w,ids)
    b1 = np.linalg.solve((xd*w[:,None]).T@xd, xd.T@(w*yd))
    explicit = np.column_stack([x, np.eye(30)[ids]])
    b2 = np.linalg.lstsq(explicit*np.sqrt(w)[:,None],y*np.sqrt(w),rcond=None)[0][:p]
    assert np.max(np.abs(b1-b2)) < 1e-10
    repeated = np.stack([(xd*w[:,None]).T@xd]*2)
    q = np.stack([xd.T@(w*yd)]*2)
    assert np.allclose(coefficients(repeated,q,np.eye(3)),[b1,b1])
    assert runs(pd.to_datetime(["2020-01-01","2020-01-02","2020-01-04"])) == [(pd.Timestamp("2020-01-01"),pd.Timestamp("2020-01-02"))]
    return dict(weighted_fixed_effects_matches_explicit_dummies=True, batched_contrasts=True, run_dates=True)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--input-root",type=Path,default=DEFAULT)
    parser.add_argument("--output",type=Path)
    parser.add_argument("--bootstrap",type=int,default=5000)
    parser.add_argument("--self-test",action="store_true")
    args=parser.parse_args()
    tests=self_test()
    if args.self_test:
        print(json.dumps(tests)); return
    out=args.output or args.input_root/"analysis"
    out.mkdir(parents=True,exist_ok=True)
    weather=pd.read_csv(args.input_root/"weather"/"weather_daily.csv",parse_dates=["date"])
    stations=pd.read_csv(args.input_root/"stations"/"station_daily.csv",parse_dates=["date"],dtype={"station_id":str})
    assert not weather.duplicated(["city","date"]).any()
    assert not stations.duplicated(["city","date","station_id"]).any()
    weather,thresholds,events,splines=prepare_weather(weather)
    weather.to_csv(out/"analysis_weather_daily.csv",index=False)
    thresholds.to_csv(out/"thresholds.csv",index=False)
    events.to_csv(out/"episode_manifest.csv",index=False)
    historical_candidate_funnel(weather,events,out)
    dump(out/"spline_specifications.json",splines)
    panel=stations[["city","date","station_id","no2_ppb"]].merge(weather,on=["city","date"],how="inner",validate="many_to_one")
    n_merged=len(panel)
    panel=panel[panel.warm].copy()
    n_warm=len(panel)
    required=["no2_ppb"]+MET+[c for c in panel if c.startswith("met_")]
    missing=panel[required].isna().sum().to_dict()
    panel=panel.dropna(subset=required).copy()
    counts=panel.groupby(["city","station_id","year"]).date.transform("nunique")
    panel["core_station_year"]=counts.ge(.8*214)
    panel.to_csv(out/"analysis_station_daily.csv",index=False)
    flow=support_audit(panel,events,out)
    summary=[]
    specifications=[
        ("calendar_only",dict(adjusted=False)),
        ("weather_adjusted",dict(adjusted=True)),
        ("direct_calendar_support",dict(adjusted=True,direct=True)),
        ("core_monitors",dict(adjusted=True,core=True)),
        ("equal_station_weights",dict(adjusted=True,equal_site=True)),
        ("all_consecutive_episodes",dict(adjusted=True,label="regime_unrestricted")),
        ("four_weather_regimes",dict(adjusted=True,label="regime_factorial")),
        ("phase_calendar",dict(adjusted=False,label="phase")),
        ("phase_adjusted",dict(adjusted=True,label="phase")),
        ("period_2019_2022",dict(adjusted=True,years=(2019,2022))),
        ("period_2023_2024",dict(adjusted=True,years=(2023,2024))),
        ("extension_2025",dict(adjusted=True,years=(2025,2025))),
    ]
    for name,options in specifications:
        summary.extend(pooled_models(panel,name,out,args.bootstrap,**options))
        pd.DataFrame(summary).to_csv(out/"model_summary.csv",index=False)
    summary.extend(pooled_models(panel[panel.year.ne(2020)],"exclude_2020",out,args.bootstrap,adjusted=True))
    median=panel.groupby(["city","date"]).no2_ppb.median().reset_index()
    median=median.merge(weather,on=["city","date"],validate="one_to_one")
    median["station_id"]="CITY_MEDIAN"
    median["core_station_year"]=True
    summary.extend(pooled_models(median,"city_median",out,args.bootstrap,adjusted=True))
    pd.DataFrame(summary).to_csv(out/"model_summary.csv",index=False)
    source_hashes={str(p.relative_to(args.input_root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [args.input_root/"weather"/"weather_daily.csv",args.input_root/"stations"/"station_daily.csv"]}
    audit=dict(analysis_status="retrospective revision; not preregistered",pooled_interval="approximate cross-city t, df=10; assumes independent city-level estimates",city_interval="approximate delete-one-year jackknife t; at least three years and all deletion contrasts identifiable",bootstrap_role="conditional sensitivity diagnostics, not unconditional confidence intervals",bootstrap_reps=args.bootstrap,seed=SEED,merged_station_days=n_merged,warm_station_days=n_warm,complete_station_days=len(panel),missing={k:int(v) for k,v in missing.items()},episode_counts=events.groupby("year").size().to_dict(),self_tests=tests,input_sha256=source_hashes,support_by_city=flow)
    # Convert numpy scalar values to plain JSON scalars.
    audit=json.loads(json.dumps(audit,default=lambda x:x.item() if hasattr(x,"item") else str(x)))
    dump(out/"analysis_audit.json",audit)
    print(json.dumps(audit,ensure_ascii=False),flush=True)


if __name__=="__main__":
    main()
