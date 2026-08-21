#!/usr/bin/env python3
"""Build the aggregate JSON datasets consumed by the web front-end.

Inputs  : results/aggregate_source/   (aggregate model output only — see DATA_POLICY.md)
Outputs : results/json/               (canonical location)
          web/public/data/            (copy served by the static site)

Every emitted dataset carries a provenance block naming the source file and a
`data_status` of "verified" (derived from a real aggregate file) or
"placeholder" (fixture with the target shape, no real numbers).

Run:  python3 scripts/build_aggregates.py
      python3 scripts/build_aggregates.py --check   # fail if outputs are stale
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "results" / "aggregate_source"
OUT = REPO / "results" / "json"
WEB = REPO / "web" / "public" / "data"
FIXTURES = REPO / "fixtures"

SCHEMA_VERSION = "1.0.0"

# --------------------------------------------------------------------------
# Controlled vocabularies. These mirror the analysis code exactly; see
# analysis/ANALYSIS_CONTRACT.md for where each code is defined upstream.
# --------------------------------------------------------------------------
OUTCOMES = {
    "volume":        ("Semen volume", "mL", "pre-freezing"),
    "sc_pre":        ("Sperm concentration, pre-freezing", "10^6/mL", "pre-freezing"),
    "tsc":           ("Total sperm count", "10^6 per ejaculate", "pre-freezing"),
    "pr_pre":        ("Progressive motility, pre-freezing", "% of spermatozoa", "pre-freezing"),
    "np_pre":        ("Non-progressive motility, pre-freezing", "% of spermatozoa", "pre-freezing"),
    "im_pre":        ("Immotile fraction, pre-freezing", "% of spermatozoa", "pre-freezing"),
    "sc_post":       ("Sperm concentration, post-thaw", "10^6/mL", "post-thaw"),
    "pr_post":       ("Progressive motility, post-thaw", "% of spermatozoa", "post-thaw"),
    "np_post":       ("Non-progressive motility, post-thaw", "% of spermatozoa", "post-thaw"),
    "im_post":       ("Immotile fraction, post-thaw", "% of spermatozoa", "post-thaw"),
    "survival_post": ("Post-thaw survival rate", "%", "post-thaw"),
}

# Windows are counted in days before ejaculation, inclusive, as defined in the
# upstream exposure builder (WINDOWS dict) and the canonical model script.
WINDOWS = {
    "w0_90":  ("0-90 d before ejaculation", "Full spermatogenic window", 0, 90),
    "w70_90": ("70-90 d before ejaculation", "Spermatogonial proliferation phase", 70, 90),
    "w15_69": ("15-69 d before ejaculation", "Meiosis and spermiogenesis phase", 15, 69),
    "w0_9":   ("0-9 d before ejaculation", "Epididymal transit phase", 0, 9),
    "w10_14": ("10-14 d before ejaculation", "Late epididymal phase", 10, 14),
}

EXPOSURES = {
    "tmax":   ("Window mean daily maximum temperature", "per +1 degrees Celsius", "continuous"),
    "anyhw3": ("Any heatwave in window (>=3 consecutive days Tmax >=35 C)",
               "exposed vs unexposed", "binary"),
    "hwp95":  ("Any heatwave in window (>=3 consecutive days Tmax >= warm-season 95th percentile)",
               "exposed vs unexposed", "binary"),
    "ht30":   ("Days with Tmax >=30 C in window", "per +1 day", "count"),
    "ht32":   ("Days with Tmax >=32 C in window", "per +1 day", "count"),
    "ht35":   ("Days with Tmax >=35 C in window", "per +1 day", "count"),
    "htp90":  ("Days with Tmax >= warm-season 90th percentile", "per +1 day", "count"),
    "htp95":  ("Days with Tmax >= warm-season 95th percentile", "per +1 day", "count"),
    "hw2":    ("Heatwave days, >=2 consecutive days Tmax >=35 C", "per +1 day", "count"),
    "hw3":    ("Heatwave days, >=3 consecutive days Tmax >=35 C", "per +1 day", "count"),
    "hw4":    ("Heatwave days, >=4 consecutive days Tmax >=35 C", "per +1 day", "count"),
    "ht35_w0_90": ("Days with Tmax >=35 C, 0-90 d window", "per +10 days", "count"),
    "ht32_w0_90": ("Days with Tmax >=32 C, 0-90 d window", "per +10 days", "count"),
    "ht30_w0_90": ("Days with Tmax >=30 C, 0-90 d window", "per +10 days", "count"),
}

CONFIRMATORY_MODEL = (
    "Ordinary least squares on the within-cohort standardised outcome, with "
    "donor-level cluster-robust standard errors; covariates: donor age, "
    "abstinence days, season (categorical) and centred calendar year. "
    "Benjamini-Hochberg FDR across the 156-test two-cohort confirmatory family."
)


class ModelRegistry:
    """Interns model descriptions so rows carry a short id instead of a paragraph."""

    def __init__(self) -> None:
        self._ids: dict[str, str] = {}

    def id_for(self, text: str) -> str:
        if text not in self._ids:
            self._ids[text] = f"m{len(self._ids) + 1}"
        return self._ids[text]

    def as_dict(self) -> dict[str, str]:
        return {model_id: text for text, model_id in self._ids.items()}

    def reset(self) -> None:
        self._ids.clear()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


MODELS = ModelRegistry()


def read_csv(name: str) -> list[dict]:
    with (SRC / name).open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def read_json(name: str) -> dict:
    return json.loads((SRC / name).read_text(encoding="utf-8"))


def num(value, digits: int | None = None):
    if value is None:
        return None
    text = str(value).strip()
    if text == "" or text.upper() in {"NA", "NAN", "ERR", "NONE"}:
        return None
    try:
        out = float(text)
    except ValueError:
        return None
    if math.isnan(out) or math.isinf(out):
        return None
    return round(out, digits) if digits is not None else out


def as_int(value):
    parsed = num(value)
    return None if parsed is None else int(parsed)


def source_ref(name: str, origin: str, kind: str) -> dict:
    path = SRC / name
    return {
        "file": f"results/aggregate_source/{name}",
        "upstream_origin": origin,
        "kind": kind,
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
    }


def envelope(dataset: str, description: str, sources: list[dict], rows_key: str,
             rows, data_status: str = "verified", notes: list[str] | None = None,
             **extra) -> dict:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "dataset": dataset,
        "description": description,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "data_status": data_status,
        "provenance": {"sources": sources},
        "notes": notes or [],
    }
    payload.update(extra)
    models = MODELS.as_dict()
    if models:
        payload["models"] = models
    payload[rows_key] = rows
    payload["n_rows"] = len(rows) if isinstance(rows, list) else None
    return payload


def outcome_meta(code: str) -> dict:
    label, unit, stage = OUTCOMES.get(code, (code, "", "unspecified"))
    return {"outcome": code, "outcome_label": label, "outcome_unit": unit, "stage": stage}


def window_meta(code: str) -> dict:
    label, phase, lo, hi = WINDOWS.get(code, (code, "", None, None))
    return {"window": code, "window_label": label, "window_phase": phase,
            "window_days_before": [lo, hi]}


def exposure_meta(code: str) -> dict:
    label, unit, kind = EXPOSURES.get(code, (code, "", "unspecified"))
    return {"exposure_metric": code, "exposure_label": label,
            "exposure_contrast": unit, "exposure_kind": kind}


# --------------------------------------------------------------------------
# 1. cohort summary
# --------------------------------------------------------------------------
def build_cohort_summary() -> dict:
    canonical = read_csv("exposure_response_results_fdr_2city_canonical.csv")
    locked = read_json("SX_SY_provenance.json")
    cohort_agg = read_json("cohort_aggregate.json")
    weather = read_json("weather_aggregate.json")

    # confirmatory-model sample size per city: the largest n in the family
    model_n: dict[str, dict] = {}
    for row in canonical:
        city = row["city"]
        n, ndonor = as_int(row["n"]), as_int(row["ndonor"])
        current = model_n.setdefault(city, {"n_samples": 0, "n_donors": 0})
        current["n_samples"] = max(current["n_samples"], n or 0)
        current["n_donors"] = max(current["n_donors"], ndonor or 0)

    span = {entry["city"]: entry for entry in weather["weather_span"]}
    harmonised = {entry["city"]: entry for entry in cohort_agg["cohort"]}

    cohorts = []
    roles = {"Wuhan": "primary", "Chongqing": "primary",
             "Wenzhou": "supplementary", "Xiamen": "supplementary"}
    for city in ["Wuhan", "Chongqing", "Wenzhou", "Xiamen"]:
        record = {
            "city": city,
            "role": roles[city],
            "period_start_year": harmonised.get(city, {}).get("year_min"),
            "period_end_year": harmonised.get(city, {}).get("year_max"),
            "weather_record_start": span.get(city, {}).get("date_min"),
            "weather_record_end": span.get(city, {}).get("date_max"),
            "weather_days_observed": span.get(city, {}).get("n_days"),
            "samples": [],
        }
        if city in harmonised:
            record["samples"].append({
                "sample_definition": "harmonised source table, all records",
                "n_samples": harmonised[city]["n_samples"],
                "n_donors": None,
                "n_donors_note": (
                    "Distinct-key counts in the harmonised source table are not "
                    "comparable with the analysis-sample donor counts and are "
                    "therefore omitted."
                ),
                "source": "results/aggregate_source/cohort_aggregate.json",
            })
        if city in locked.get("locked_by_city", {}):
            record["samples"].append({
                "sample_definition": "locked complete-parameter analysis sample",
                "n_samples": locked["locked_by_city"][city],
                "n_donors": locked.get("locked_donors_by_city", {}).get(city),
                "source": "results/aggregate_source/SX_SY_provenance.json",
            })
        if city in model_n:
            record["samples"].append({
                "sample_definition": "confirmatory exposure-response model sample (maximum n in family)",
                "n_samples": model_n[city]["n_samples"],
                "n_donors": model_n[city]["n_donors"],
                "source": "results/aggregate_source/exposure_response_results_fdr_2city_canonical.csv",
            })
        cohorts.append(record)

    exposure_distributions = []
    for entry in cohort_agg["exposure_dist"]:
        metric = entry["metric"]
        stem, _, window = metric.partition("_w")
        window_code = f"w{window}"
        label = {
            "tmax": "Window mean daily maximum temperature",
            "ht35": "Days with Tmax >=35 C in window",
        }.get(stem, stem)
        exposure_distributions.append({
            "city": entry["city"],
            "metric": metric,
            "metric_label": label,
            "unit": "degrees Celsius" if stem == "tmax" else "days",
            **window_meta(window_code),
            "median": entry["median"], "p25": entry["p25"], "p75": entry["p75"],
            "n": entry["n"],
            "source": "results/aggregate_source/cohort_aggregate.json",
        })

    return envelope(
        dataset="cohort_summary",
        description=(
            "Cohort composition, study periods, donor covariate distributions, "
            "exposure distributions and city-level heat climatology."
        ),
        sources=[
            source_ref("cohort_aggregate.json",
                       "分析输出/donor_exposure.csv, reduced to grouped statistics on the host machine "
                       "by scripts/remote_summarise.py --what cohort",
                       "grouped counts, medians and quartiles"),
            source_ref("weather_aggregate.json",
                       "分析输出/weather_daily.csv, reduced to grouped statistics by "
                       "scripts/remote_summarise.py --what weather",
                       "city-day weather aggregated to month and year"),
            source_ref("SX_SY_provenance.json",
                       "02_DATA_VERIFICATION/out/SX_SY_provenance.json",
                       "analysis-sample counts"),
            source_ref("exposure_response_results_fdr_2city_canonical.csv",
                       "分析输出/exposure_response_results_fdr_2city_canonical.csv",
                       "model output"),
        ],
        rows_key="cohorts",
        rows=cohorts,
        notes=[
            "Donor counts are reported per sample definition because the harmonised "
            "source table, the locked complete-parameter sample and the confirmatory "
            "model sample are not the same set of records.",
            "Exposure distributions are computed over the harmonised source table, "
            "not over the confirmatory model sample.",
        ],
        exposure_distributions=exposure_distributions,
        covariates=[
            {"city": entry["city"], "variable": entry["variable"],
             "variable_label": {"age": "Donor age", "abstinence_days": "Abstinence"}.get(
                 entry["variable"], entry["variable"]),
             "unit": {"age": "years", "abstinence_days": "days"}.get(entry["variable"], ""),
             "median": entry["median"], "p25": entry["p25"], "p75": entry["p75"],
             "n": entry["n"],
             "source": "results/aggregate_source/cohort_aggregate.json"}
            for entry in cohort_agg["covariates"]
        ],
        samples_by_year=cohort_agg["by_year"],
        weather_monthly=weather["weather_monthly"],
        weather_annual_hot_days=weather["weather_annual_hot_days"],
    )


# --------------------------------------------------------------------------
# 2. baseline table
# --------------------------------------------------------------------------
def build_baseline_table() -> dict:
    rows = []
    for entry in read_csv("analysis_sample_sd_reference.csv"):
        code = entry["outcome"]
        rows.append({
            "cohort": entry["cohort"],
            "stratum": "locked complete-parameter analysis sample, all records",
            **outcome_meta(code),
            "native_unit": entry["native_unit"],
            "median": num(entry["median"], 2),
            "p25": num(entry["q1"], 2),
            "p75": num(entry["q3"], 2),
            "mean": num(entry["mean"], 2),
            "sd": num(entry["sd"], 3),
            "n": as_int(entry["n"]),
            "source": "results/aggregate_source/analysis_sample_sd_reference.csv",
        })
    return envelope(
        dataset="baseline_table",
        description=(
            "Semen parameter distributions by cohort in the locked "
            "complete-parameter analysis sample."
        ),
        sources=[source_ref("analysis_sample_sd_reference.csv",
                            "02_DATA_VERIFICATION/out/analysis_sample_sd_reference.csv",
                            "group medians, quartiles, means and standard deviations")],
        rows_key="rows",
        rows=rows,
        notes=[
            "The standard deviation column is the within-cohort scaling constant used "
            "to express model coefficients in SD units and to back-convert them to "
            "native units.",
            "Only one stratum is included: the analysis sample as a whole. No "
            "stratification that could reduce cell sizes towards individual records "
            "is included.",
        ],
    )


# --------------------------------------------------------------------------
# 3. exposure-response
# --------------------------------------------------------------------------
def build_exposure_response() -> dict:
    native = {}
    for entry in read_csv("tableSY_native_unit_effects.csv"):
        key = (entry["cohort"], entry["outcome"], entry["exposure_metric"],
               entry["exposure_window"])
        native[key] = entry

    rows = []
    for entry in read_csv("exposure_response_results_fdr_2city_canonical.csv"):
        city, code, window, expo = (entry["city"], entry["outcome"],
                                    entry["window"], entry["expo"])
        q = num(entry["q"])
        p = num(entry["p"])
        row = {
            "cohort": city,
            **outcome_meta(code),
            **exposure_meta(expo),
            **window_meta(window),
            "beta_sd": num(entry["beta"], 4),
            "se_sd": num(entry["se"], 4),
            "ci_low_sd": num(entry["ci_l"], 4),
            "ci_high_sd": num(entry["ci_u"], 4),
            "p_value": p,
            "q_value": q,
            "fdr_significant": bool(q is not None and q < 0.05),
            "p_below_0_05": bool(p is not None and p < 0.05),
            "n": as_int(entry["n"]),
            "n_donors": as_int(entry["ndonor"]),
            "model_id": MODELS.id_for(CONFIRMATORY_MODEL),
            "family": "two-cohort confirmatory family, 156 tests",
            "source": "results/aggregate_source/exposure_response_results_fdr_2city_canonical.csv",
        }
        match = native.get((city, code, expo, window))
        if match:
            row["native"] = {
                "unit": match["native_unit"],
                "effect": num(match["effect_native_units"], 4),
                "ci_low": num(match["ci_low_native_units"], 4),
                "ci_high": num(match["ci_high_native_units"], 4),
                "percent_of_median": num(match["percent_of_median"], 3),
                "analysis_sample_sd": num(match["analysis_sample_sd"], 4),
                "analysis_sample_median": num(match["analysis_sample_median"], 3),
                "source": "results/aggregate_source/tableSY_native_unit_effects.csv",
            }
        rows.append(row)

    rows.sort(key=lambda r: (r["cohort"], r["outcome"], r["exposure_metric"], r["window"]))
    return envelope(
        dataset="exposure_response",
        description=(
            "Confirmatory exposure-response coefficients: 13 cohort-outcome "
            "combinations x 4 spermatogenic windows x 3 exposure metrics."
        ),
        sources=[
            source_ref("exposure_response_results_fdr_2city_canonical.csv",
                       "分析输出/exposure_response_results_fdr_2city_canonical.csv",
                       "model coefficients, standard errors, P and BH q values"),
            source_ref("tableSY_native_unit_effects.csv",
                       "02_DATA_VERIFICATION/out/tableSY_native_unit_effects.csv",
                       "SD-to-native-unit conversion of the same coefficients"),
        ],
        rows_key="rows",
        rows=rows,
        notes=[
            "Coefficients are in within-cohort standard-deviation units of the "
            "outcome. Confidence intervals are beta +/- 1.96 x SE.",
            "anyhw3 and hwp95 are binary in this family: the coefficient is the "
            "exposed-versus-unexposed contrast, not a per-day slope.",
            "q values are Benjamini-Hochberg adjusted across all 156 tests of the "
            "two-cohort family, not within cohort or outcome.",
            "Native-unit effects are available for the subset of rows that have a "
            "matching within-cohort standard deviation in the locked sample.",
        ],
        vocabularies={
            "outcomes": {k: {"label": v[0], "unit": v[1], "stage": v[2]}
                         for k, v in OUTCOMES.items()},
            "windows": {k: {"label": v[0], "phase": v[1], "days_before": [v[2], v[3]]}
                        for k, v in WINDOWS.items()},
            "exposures": {k: {"label": v[0], "contrast": v[1], "kind": v[2]}
                          for k, v in EXPOSURES.items()},
        },
    )


# --------------------------------------------------------------------------
# 4. interaction tests
# --------------------------------------------------------------------------
def build_interaction_tests() -> dict:
    rows = []
    for entry in read_csv("interaction_test_results.csv"):
        rows.append({
            "test_set": "primary cohort-by-exposure interaction test",
            "outcome_label": entry["outcome"],
            "outcome": {"Concentration": "sc_pre"}.get(entry["outcome"], entry["outcome"].lower()),
            "exposure_metric": "cumulative high-temperature days",
            "exposure_contrast": "not restated in the source file",
            "window": None,
            "window_label": "not restated in the source file",
            "beta_interaction_sd": num(entry["beta"], 4),
            "se_interaction": None,
            "ci_low_interaction": None,
            "ci_high_interaction": None,
            "p_interaction": num(entry["pval"]),
            "heterogeneous_at_0_05": entry["sig"].strip() == "*",
            "n_obs": None,
            "n_donors": None,
            "beta_wuhan_sd": None,
            "beta_chongqing_sd": None,
            "sample": "not restated in the source file",
            "model_id": MODELS.id_for((
                "Cluster-robust OLS on the pooled two-cohort sample with a "
                "cohort-by-exposure interaction; outcome standardised within cohort."
            )),
            "source": "results/aggregate_source/interaction_test_results.csv",
        })

    for entry in read_csv("tableSX_cohort_exposure_interaction.csv"):
        expo = entry["exposure"]
        rows.append({
            "test_set": "supplementary interaction table",
            **outcome_meta(entry["outcome"]),
            "exposure_metric": expo,
            "exposure_label": EXPOSURES.get(expo, (expo, "", ""))[0],
            "exposure_contrast": "per +10 days",
            **window_meta("w0_90"),
            "beta_interaction_sd": num(entry["beta_interaction_sd_per10d"], 4),
            "se_interaction": num(entry["se_interaction"], 4),
            "ci_low_interaction": num(entry["ci_low_interaction"], 4),
            "ci_high_interaction": num(entry["ci_high_interaction"], 4),
            "p_interaction": num(entry["p_interaction"]),
            "heterogeneous_at_0_05": entry["heterogeneous_at_0.05"] == "yes",
            "n_obs": as_int(entry["n_obs"]),
            "n_donors": as_int(entry["n_donors"]),
            "n_obs_wuhan": as_int(entry["n_obs_wuhan"]),
            "n_obs_chongqing": as_int(entry["n_obs_chongqing"]),
            "beta_wuhan_sd": num(entry["beta_wuhan_sd_per10d"], 4),
            "beta_chongqing_sd": num(entry["beta_chongqing_sd_per10d"], 4),
            "se_chongqing": num(entry["se_chongqing"], 4),
            "tier": entry["tier"],
            "sample": entry["sample"],
            "model_id": MODELS.id_for((
                "Cluster-robust OLS on the pooled locked sample with a "
                "cohort-by-exposure interaction; outcome standardised within cohort; "
                "exposure scaled per ten high-temperature days."
            )),
            "source": "results/aggregate_source/tableSX_cohort_exposure_interaction.csv",
        })

    return envelope(
        dataset="interaction_tests",
        description="Cohort-by-exposure interaction tests quantifying between-cohort heterogeneity.",
        sources=[
            source_ref("interaction_test_results.csv",
                       "02_DATA_VERIFICATION/interaction_test_results.csv",
                       "single primary interaction coefficient"),
            source_ref("tableSX_cohort_exposure_interaction.csv",
                       "02_DATA_VERIFICATION/out/tableSX_cohort_exposure_interaction.csv",
                       "interaction coefficients with per-cohort slopes"),
        ],
        rows_key="rows",
        rows=rows,
        notes=[
            "The two test sets use different samples and different exposure scalings, "
            "so their coefficients are not interchangeable. Both are shown rather "
            "than reconciled.",
            "The primary interaction file contains only outcome, beta, P and a "
            "significance flag. Fields it does not carry are left null instead of "
            "being inferred.",
        ],
    )


# --------------------------------------------------------------------------
# 5. sensitivity analyses
# --------------------------------------------------------------------------
COVID_ROW = re.compile(
    r"^\s*(?P<label>\S.*?)\s+(?P<outcome>[a-z_]+)\s+(?P<beta>-?\d+\.\d+)\s+"
    r"(?P<se>\d+\.\d+)\s+(?P<p>[\d.]+e[-+]\d+)\s+(?P<n>\d+)\s+(?P<donors>\d+)\s*$"
)


def parse_pandemic_exclusion() -> list[dict]:
    """Parse the pandemic-year sensitivity tables out of the COVID-period exclusion text dump."""
    text = (SRC / "covid_period_exclusion_sensitivity.txt").read_text(encoding="utf-8")
    rows: list[dict] = []
    window = "w0_90"
    exposure = "anyhw3"
    for line in text.splitlines():
        if "expo=anyhw3_w0_90" in line:
            window, exposure = "w0_90", "anyhw3"
            continue
        if line.strip().startswith("Early window w70_90"):
            window, exposure = "w70_90", "anyhw3"
            continue
        match = COVID_ROW.match(line)
        if not match or match.group("outcome") == "y":
            continue
        label = match.group("label").strip()
        variant = {
            "ALL 2020-24": "all years 2020-2024",
            "ALL": "all years 2020-2024",
            "excl 2020-21": "excluding 2020-2021",
            "2022 only (heat yr)": "2022 only (hottest year)",
        }.get(label, label)
        rows.append({
            "family": "pandemic_exclusion",
            "family_label": "Pandemic-year exclusion",
            "cohort": "Chongqing",
            **outcome_meta(match.group("outcome")),
            **exposure_meta(exposure),
            **window_meta(window),
            "variant": variant,
            "beta_sd": num(match.group("beta"), 4),
            "se_sd": num(match.group("se"), 4),
            "p_value": num(match.group("p")),
            "n": as_int(match.group("n")),
            "n_donors": as_int(match.group("donors")),
            "model_id": MODELS.id_for(("Cluster-robust OLS, donor-level clustering, outcome "
                      "standardised within cohort.")),
            "source": "results/aggregate_source/covid_period_exclusion_sensitivity.txt",
        })
    if len(rows) != 24:
        raise SystemExit(
            f"pandemic-exclusion parser extracted {len(rows)} rows, expected 24; "
            "the source text layout changed and the parser must be reviewed"
        )
    return rows


def build_sensitivity() -> dict:
    rows: list[dict] = []

    for entry in read_csv("sensitivity_heatwave_definitions.csv"):
        metric = entry["metric"]
        family = entry["family"]
        rows.append({
            "family": f"{family}_variant",
            "family_label": ("Alternative temperature threshold" if family == "threshold"
                             else "Alternative heatwave duration"),
            "cohort": entry["city"],
            **outcome_meta(entry["outcome"]),
            **exposure_meta(metric),
            **window_meta(entry["window"]),
            "variant": EXPOSURES.get(metric, (metric, "", ""))[0],
            "beta_sd": num(entry["beta"], 4),
            "se_sd": num(entry["se"], 4),
            "p_value": num(entry["p"]),
            "n": as_int(entry["n"]),
            "model_id": MODELS.id_for("Cluster-robust OLS, donor-level clustering."),
            "source": "results/aggregate_source/sensitivity_heatwave_definitions.csv",
        })

    verdicts = {
        "ROBUST_to_pollution": "Association retained after pollutant adjustment",
        "attenuated_by_pollution": "Association attenuated after pollutant adjustment",
        "coverage_power_loss": "Inconclusive: air-quality subset too small",
        "null_base": "No association in the unadjusted model",
        "mixed": "Mixed",
    }
    for entry in read_csv("exposure_response_pollution_adjusted.csv"):
        rows.append({
            "family": "pollutant_adjustment",
            "family_label": "Air-pollutant adjustment",
            "cohort": entry["city"],
            **outcome_meta(entry["outcome"]),
            **exposure_meta(entry["expo"]),
            **window_meta(entry["window"]),
            "variant": verdicts.get(entry["label"], entry["label"]),
            "verdict_code": entry["label"],
            "beta_sd": num(entry["adj_beta"], 4),
            "se_sd": num(entry["adj_se"], 4),
            "p_value": num(entry["adj_p"]),
            "n": as_int(entry["n_sub"]),
            "comparison": {
                "base_full_beta": num(entry["base_full_beta"], 4),
                "base_full_p": num(entry["base_full_p"]),
                "n_full": as_int(entry["n_full"]),
                "base_subset_beta": num(entry["base_sub_beta"], 4),
                "base_subset_p": num(entry["base_sub_p"]),
                "n_subset": as_int(entry["n_sub"]),
            },
            "model_id": MODELS.id_for(("Cluster-robust OLS additionally adjusted for air-quality "
                      "covariates, fitted on the air-quality available subset.")),
            "source": "results/aggregate_source/exposure_response_pollution_adjusted.csv",
        })

    for entry in read_csv("sensitivity_humidity_heatindex.csv"):
        rows.append({
            "family": "humidity_adjustment",
            "family_label": "Humidity and heat-index specification",
            "cohort": entry["city"],
            **outcome_meta(entry["outcome"]),
            **exposure_meta("tmax"),
            **window_meta(entry["window"]),
            "variant": "Tmax adjusted for relative humidity",
            "beta_sd": num(entry["tmax_rhadj_beta"], 4),
            "se_sd": None,
            "p_value": num(entry["tmax_rhadj_p"]),
            "n": as_int(entry["n"]),
            "comparison": {
                "base_full_beta": num(entry["tmax_base_beta"], 4),
                "base_full_p": num(entry["tmax_base_p"]),
                "heat_index_beta": num(entry["hi_beta"], 4),
                "heat_index_p": num(entry["hi_p"]),
            },
            "model_id": MODELS.id_for("Cluster-robust OLS with relative humidity added, and a heat-index variant."),
            "source": "results/aggregate_source/sensitivity_humidity_heatindex.csv",
        })

    for entry in read_csv("sensitivity_ses.csv"):
        expo_code, _, window_code = entry["expo"].partition("_")
        rows.append({
            "family": "covariate_adjustment",
            "family_label": "Body-mass index and education adjustment",
            "cohort": entry["city"],
            **outcome_meta(entry["outcome"]),
            **exposure_meta(expo_code),
            **window_meta(window_code or "w0_90"),
            "variant": f"adjusted for {entry['ses_covars']}",
            "beta_sd": num(entry["ses_beta"], 4),
            "se_sd": None,
            "p_value": num(entry["ses_p"]),
            "n": as_int(entry["n"]),
            "comparison": {
                "base_full_beta": num(entry["base_beta"], 4),
                "base_full_p": num(entry["base_p"]),
                "bmi_only_beta": num(entry["bmi_beta"], 4),
                "bmi_only_p": num(entry["bmi_p"]),
            },
            "model_id": MODELS.id_for("Cluster-robust OLS with body-mass index and education added."),
            "source": "results/aggregate_source/sensitivity_ses.csv",
        })

    rows.extend(parse_pandemic_exclusion())

    for entry in read_csv("exposure_response_results_fdr.csv"):
        rows.append({
            "family": "analysis_sample_variant",
            "family_label": "Superseded analysis sample",
            "cohort": entry["city"],
            **outcome_meta(entry["outcome"]),
            **exposure_meta(entry["expo"]),
            **window_meta(entry["window"]),
            "variant": "earlier full harmonised-table family (superseded by the canonical family)",
            "beta_sd": num(entry["beta"], 4),
            "se_sd": num(entry["se"], 4),
            "p_value": num(entry["p"]),
            "q_value": num(entry["q"]),
            "n": as_int(entry["n"]),
            "n_donors": as_int(entry["ndonor"]),
            "model_id": MODELS.id_for(("Cluster-robust OLS on the earlier, non-canonical harmonised "
                      "table; retained to show how much the result depends on the "
                      "analysis sample definition.")),
            "source": "results/aggregate_source/exposure_response_results_fdr.csv",
        })

    families = sorted({r["family"] for r in rows})
    return envelope(
        dataset="sensitivity",
        description=("Sensitivity analyses: alternative heat definitions, pollutant "
                     "and covariate adjustment, pandemic-year exclusion, and the "
                     "superseded analysis sample."),
        sources=[
            source_ref("sensitivity_heatwave_definitions.csv",
                       "分析输出/sensitivity_heatwave_definitions.csv", "model output"),
            source_ref("exposure_response_pollution_adjusted.csv",
                       "分析输出/exposure_response_pollution_adjusted.csv", "model output"),
            source_ref("sensitivity_humidity_heatindex.csv",
                       "分析输出/sensitivity_humidity_heatindex.csv", "model output"),
            source_ref("sensitivity_ses.csv", "分析输出/sensitivity_ses.csv", "model output"),
            source_ref("covid_period_exclusion_sensitivity.txt", "分析输出/covid_period_exclusion_sensitivity.txt",
                       "aggregate model output as a formatted text table, parsed by "
                       "scripts/build_aggregates.py"),
            source_ref("exposure_response_results_fdr.csv",
                       "分析输出/exposure_response_results_fdr.csv", "model output"),
        ],
        rows_key="rows",
        rows=rows,
        notes=[
            "Sensitivity rows do not carry FDR q values except where the source file "
            "provides them; they were not part of the 156-test confirmatory family.",
            "Some pandemic-exclusion cells failed to fit (singular matrix) upstream "
            "and are absent rather than imputed.",
            "Rows for Wenzhou and Xiamen appear in some sensitivity families because "
            "the upstream file includes them; they are supplementary cohorts.",
        ],
        families=families,
    )


# --------------------------------------------------------------------------
# 6. provenance manifest (fixture until the upstream file exists)
# --------------------------------------------------------------------------
def build_provenance_manifest() -> dict:
    fixture = json.loads((FIXTURES / "provenance_manifest.fixture.json").read_text(encoding="utf-8"))
    real = SRC / "provenance_manifest.json"
    extra: dict = {}
    if real.exists():
        raw = json.loads(real.read_text(encoding="utf-8"))
        entries = raw.get("entries", raw) if isinstance(raw, dict) else raw
        extra = {key: raw[key] for key in ("confidence_definitions", "confidence_counts")
                 if isinstance(raw, dict) and key in raw}
        status = "verified"
        note = (
            "Public extract of the analysis-host provenance audit. Absolute paths, "
            "host names and confidential directory names were stripped. Figure-level "
            "confidence is copied as recorded; UNRESOLVED and MEDIUM rows are not "
            "upgraded."
        )
        sources = [source_ref("provenance_manifest.json",
                              "01_REVISION_DOCS/provenance/provenance_manifest.json",
                              "sanitized figure-to-script records")]
    else:
        entries = fixture["entries"]
        status = "placeholder"
        note = ("PLACEHOLDER. The upstream manifest "
                "01_REVISION_DOCS/provenance/provenance_manifest.json did not exist "
                "when this dataset was built. These entries carry the target field "
                "shape only; figure_id values are real, every path, mtime and status "
                "is a placeholder. Drop the real file into "
                "results/aggregate_source/provenance_manifest.json and rebuild.")
        sources = [{"file": "fixtures/provenance_manifest.fixture.json",
                    "upstream_origin": "none — fixture written by hand",
                    "kind": "placeholder", "sha256": sha256(
                        FIXTURES / "provenance_manifest.fixture.json"),
                    "bytes": (FIXTURES / "provenance_manifest.fixture.json").stat().st_size}]

    return envelope(
        dataset="provenance_manifest",
        description="Which script produced each figure, from which inputs, to which outputs.",
        sources=sources,
        rows_key="entries",
        rows=entries,
        data_status=status,
        notes=[note,
               "Public fields: figure_id, in_article, script, input_files, "
               "confidence, status, unresolved_reason. Input names may refer to "
               "confidential tables; only the filename is shown.",
               "Confidence is HIGH, MEDIUM, LOW or UNRESOLVED as defined in "
               "confidence_definitions. Dataset data_status=verified means the "
               "extract was built from a real audit file, not that every figure "
               "link is settled."],
        **extra,
    )


# --------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="verify that committed outputs match a fresh build")
    args = ap.parse_args()

    builders = {
        "cohort_summary.json": build_cohort_summary,
        "baseline_table.json": build_baseline_table,
        "exposure_response.json": build_exposure_response,
        "interaction_tests.json": build_interaction_tests,
        "sensitivity.json": build_sensitivity,
        "provenance_manifest.json": build_provenance_manifest,
    }

    OUT.mkdir(parents=True, exist_ok=True)
    WEB.mkdir(parents=True, exist_ok=True)

    built: dict[str, dict] = {}
    for name, builder in builders.items():
        MODELS.reset()
        built[name] = builder()

    index = {
        "schema_version": SCHEMA_VERSION,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "repository": "heat-sperm-portal",
        "contains_individual_level_data": False,
        "datasets": [
            {
                "file": name,
                "dataset": payload["dataset"],
                "description": payload["description"],
                "data_status": payload["data_status"],
                "n_rows": payload.get("n_rows"),
                "sources": [s["file"] for s in payload["provenance"]["sources"]],
            }
            for name, payload in built.items()
        ],
    }
    built["manifest.json"] = index

    stale: list[str] = []
    for name, payload in built.items():
        text = json.dumps(payload, indent=1, ensure_ascii=False, sort_keys=False) + "\n"
        target = OUT / name
        if args.check:
            def strip(blob: str) -> str:
                return re.sub(r'"generated_utc": "[^"]*"', '"generated_utc": ""', blob)
            if not target.exists() or strip(target.read_text(encoding="utf-8")) != strip(text):
                stale.append(name)
            continue
        target.write_text(text, encoding="utf-8")
        shutil.copyfile(target, WEB / name)
        rows = payload.get("n_rows")
        print(f"  {name:28} {payload.get('data_status', 'index'):12} "
              f"{'' if rows is None else str(rows) + ' rows'}")

    if args.check:
        if stale:
            print("stale outputs: " + ", ".join(stale))
            return 1
        print("aggregate JSON is up to date")
        return 0

    print(f"\nwrote {len(built)} files to results/json/ and web/public/data/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
