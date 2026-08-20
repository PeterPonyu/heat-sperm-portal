#!/usr/bin/env python3
"""Aggregate-only summariser, run WHERE the confidential tables live.

This script is the single sanctioned bridge between the confidential analysis
tables and this repository. It reads the donor-linked exposure table in place
and emits nothing but grouped statistics: counts, distinct-key counts, medians
and quartiles. No row, no key, no free-text field is written out.

It is intended to be run on the machine that holds the data, with its stdout
captured into `results/aggregate_source/`:

    python3 scripts/remote_summarise.py \
        --exposure-table /path/to/donor-linked-exposure-table.csv \
        --weather-table  /path/to/weather_daily.csv \
        --donor-key      <name of the donor key column> \
        --what cohort  > results/aggregate_source/cohort_aggregate.json

    python3 scripts/remote_summarise.py \
        --weather-table  /path/to/weather_daily.csv \
        --what weather > results/aggregate_source/weather_aggregate.json

The donor key column name is a required argument and is deliberately not
hard-coded here, so that this file contains no confidential schema literals.
Minimum group size is enforced: any group with fewer than --min-cell rows is
dropped rather than summarised.
"""
from __future__ import annotations

import argparse
import json
import sys

import pandas as pd


def quartiles(series: pd.Series) -> dict | None:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return None
    return {
        "median": round(float(values.median()), 2),
        "p25": round(float(values.quantile(0.25)), 2),
        "p75": round(float(values.quantile(0.75)), 2),
        "n": int(values.size),
    }


def summarise_weather(path: str) -> dict:
    wx = pd.read_csv(path, encoding="utf-8-sig", parse_dates=["date"])
    out: dict[str, list] = {"weather_span": [], "weather_monthly": [], "weather_annual_hot_days": []}
    for city, grp in wx.groupby("city"):
        grp = grp.dropna(subset=["tmax"])
        out["weather_span"].append({
            "city": city,
            "date_min": str(grp.date.min().date()),
            "date_max": str(grp.date.max().date()),
            "n_days": int(len(grp)),
        })
        for month, gm in grp.groupby(grp.date.dt.month):
            out["weather_monthly"].append({
                "city": city, "month": int(month), "n_days": int(len(gm)),
                "mean_tmax": round(float(gm.tmax.mean()), 2),
                "p10_tmax": round(float(gm.tmax.quantile(0.10)), 2),
                "p90_tmax": round(float(gm.tmax.quantile(0.90)), 2),
            })
        for year, gy in grp.groupby(grp.date.dt.year):
            if len(gy) < 300:          # drop partial years
                continue
            out["weather_annual_hot_days"].append({
                "city": city, "year": int(year), "n_days_observed": int(len(gy)),
                "days_tmax_ge_30": int((gy.tmax >= 30).sum()),
                "days_tmax_ge_32": int((gy.tmax >= 32).sum()),
                "days_tmax_ge_35": int((gy.tmax >= 35).sum()),
                "max_tmax": round(float(gy.tmax.max()), 1),
            })
    return out


def summarise_cohort(path: str, donor_key: str, min_cell: int) -> dict:
    exposure_metrics = ["tmax_w0_90", "tmax_w70_90", "ht35_w0_90", "ht35_w70_90"]
    covariates = ["age", "abstinence_days"]
    wanted = {"city", "cohort_type", donor_key, "year", *exposure_metrics, *covariates}
    frame = pd.read_csv(path, encoding="utf-8-sig", low_memory=False,
                        usecols=lambda c: c in wanted)

    out: dict[str, list] = {"cohort": [], "by_year": [], "exposure_dist": [], "covariates": []}
    for city, grp in frame.groupby("city"):
        out["cohort"].append({
            "city": city,
            "n_samples": int(len(grp)),
            "n_donors": int(grp[donor_key].nunique()),
            "year_min": int(grp.year.min()),
            "year_max": int(grp.year.max()),
        })
        for year, gy in grp.groupby("year"):
            if len(gy) < min_cell:
                continue
            out["by_year"].append({
                "city": city, "year": int(year),
                "n_samples": int(len(gy)), "n_donors": int(gy[donor_key].nunique()),
            })
        for metric in exposure_metrics:
            if metric in grp:
                stats = quartiles(grp[metric])
                if stats and stats["n"] >= min_cell:
                    out["exposure_dist"].append({"city": city, "metric": metric, **stats})
        for variable in covariates:
            if variable in grp:
                stats = quartiles(grp[variable])
                if stats and stats["n"] >= min_cell:
                    out["covariates"].append({"city": city, "variable": variable, **stats})
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--what", choices=["cohort", "weather"], required=True)
    ap.add_argument("--exposure-table")
    ap.add_argument("--weather-table")
    ap.add_argument("--donor-key", help="name of the donor key column in the exposure table")
    ap.add_argument("--min-cell", type=int, default=20,
                    help="drop any group smaller than this (default 20)")
    args = ap.parse_args()

    if args.what == "weather":
        if not args.weather_table:
            ap.error("--weather-table is required for --what weather")
        payload = summarise_weather(args.weather_table)
    else:
        if not (args.exposure_table and args.donor_key):
            ap.error("--exposure-table and --donor-key are required for --what cohort")
        payload = summarise_cohort(args.exposure_table, args.donor_key, args.min_cell)

    json.dump(payload, sys.stdout, indent=1, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
