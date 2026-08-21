#!/usr/bin/env python3
"""Fail-closed numeric locks for the public aggregate JSON.

Locks follow the living manuscript on Vector (git 35978f2, 31-page article):
  - Chongqing locked-sample TSC n = 8144; overall median 339.76 (S3)
  - Table 1 age 20-25 TSC 339.9 is a stratum (n = 4649), not the overall cell
  - never 275.4
  - Wuhan locked-sample TSC SD = 86.60 (n = 17268 on the archived file)
  - confirmatory family: 70 tests P<0.05, 62 remain at q<0.05
  - Wuhan confirmatory n 16621/2688 is a reproducibility gap vs 17268/3675,
    not the locked complete-parameter n and not "complete ten-parameter"

Does not download data. Does not re-fit models. Exits 1 on mismatch.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "web" / "public" / "data"
SRC = ROOT / "results" / "aggregate_source"


def load(name: str) -> dict:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def fail(msg: str) -> None:
    print(f"LOCKED-NUMBER FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)


def near(a: float, b: float, tol: float) -> bool:
    return abs(a - b) <= tol


def scan_2754() -> None:
    roots = [DATA, SRC, ROOT / "results" / "json"]
    hits = []
    for root in roots:
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".json", ".csv", ".txt", ".md"}:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            if "275.4" in text:
                hits.append(str(path.relative_to(ROOT)))
    if hits:
        fail("forbidden 275.4 present in " + ", ".join(hits))


def check_baseline(baseline: dict) -> None:
    rows = baseline["rows"]

    def one(cohort: str, outcome: str) -> dict:
        found = [r for r in rows if r["cohort"] == cohort and r["outcome"] == outcome]
        if len(found) != 1:
            fail(f"{cohort} {outcome}: expected 1 baseline row, got {len(found)}")
        return found[0]

    cq = one("Chongqing", "tsc")
    if cq["n"] != 8144:
        fail(f"Chongqing TSC n={cq['n']} (lock 8144)")
    if not near(float(cq["median"]), 339.76, 0.005):
        fail(f"Chongqing TSC overall median={cq['median']} (lock 339.76 from 35978f2 tab:sd_reference)")

    wh = one("Wuhan", "tsc")
    if wh["n"] != 17268:
        fail(f"Wuhan locked-sample TSC n={wh['n']} (lock 17268 archived file)")
    if not near(float(wh["sd"]), 86.60, 0.005):
        fail(f"Wuhan TSC SD={wh['sd']} (lock 86.60)")


def check_fdr(exposure: dict) -> None:
    rows = exposure["rows"]
    if len(rows) != 156:
        fail(f"confirmatory family size {len(rows)} (lock 156)")
    n_p = sum(1 for r in rows if r.get("p_below_0_05") is True)
    n_q = sum(1 for r in rows if r.get("fdr_significant") is True)
    if n_p != 70 or n_q != 62:
        fail(f"FDR counts P<0.05={n_p} q<0.05={n_q} (lock 70/62)")

    wuhan = [r for r in rows if r["cohort"] == "Wuhan"]
    pairs = {(r["n"], r["n_donors"]) for r in wuhan}
    if pairs != {(16621, 2688)}:
        fail(f"Wuhan confirmatory n pairs {sorted(pairs)} (lock 16621/2688 as confirmatory family only)")

    cq = [r for r in rows if r["cohort"] == "Chongqing" and r["outcome"] == "tsc"]
    if not cq:
        fail("no Chongqing TSC exposure rows")
    ns = {r["n"] for r in cq}
    if 8144 not in ns and 8143 not in ns:
        fail(f"Chongqing TSC exposure n={ns} (expected 8143 or 8144)")


def check_cohorts(cohort: dict) -> None:
    by_city = {c["city"]: c for c in cohort["cohorts"]}
    wh = {s["sample_definition"]: s for s in by_city["Wuhan"]["samples"]}
    cq = {s["sample_definition"]: s for s in by_city["Chongqing"]["samples"]}

    locked_wh = wh["locked complete-parameter analysis sample"]
    if locked_wh["n_samples"] != 17268 or locked_wh["n_donors"] != 3675:
        fail(f"Wuhan locked complete-parameter {locked_wh} (lock 17268/3675)")

    conf_wh = wh["confirmatory exposure-response model sample (maximum n in family)"]
    if conf_wh["n_samples"] != 16621 or conf_wh["n_donors"] != 2688:
        fail(f"Wuhan confirmatory {conf_wh} (lock 16621/2688)")

    locked_cq = cq["locked complete-parameter analysis sample"]
    if locked_cq["n_samples"] != 8144:
        fail(f"Chongqing locked n={locked_cq['n_samples']} (lock 8144)")


def check_interaction(inter: dict, provenance: dict) -> None:
    sx = [r for r in inter["rows"] if r.get("test_set") == "supplementary interaction table"]
    if len(sx) != 24:
        fail(f"SX rows {len(sx)} (lock 24)")
    n_sig = sum(1 for r in sx if r.get("heterogeneous_at_0_05") is True)
    if n_sig != 17:
        fail(f"SX P<0.05 interactions {n_sig} (lock 17)")
    if provenance.get("sx_rows") != 24 or provenance.get("sx_significant_interactions_p05") != 17:
        fail(f"SX_SY_provenance sx={provenance.get('sx_rows')}/{provenance.get('sx_significant_interactions_p05')}")


def main() -> None:
    scan_2754()
    check_baseline(load("baseline_table.json"))
    check_fdr(load("exposure_response.json"))
    check_cohorts(load("cohort_summary.json"))
    check_interaction(
        load("interaction_tests.json"),
        json.loads((SRC / "SX_SY_provenance.json").read_text(encoding="utf-8")),
    )
    print(
        "locked-number PASS: Chongqing TSC 339.76/n=8144; no 275.4; "
        "Wuhan TSC SD 86.60 (locked n=17268); FDR 70/62; "
        "Wuhan confirmatory 16621/2688 listed separately from archived 17268/3675."
    )


if __name__ == "__main__":
    main()
