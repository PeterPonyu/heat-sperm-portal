# Aggregate JSON envelope

Files in `results/json/` and `web/public/data/` share one envelope. The site renders these files only.

```json
{
  "schema_version": "1.0.0",
  "dataset": "<name>",
  "description": "<one sentence>",
  "generated_utc": "<ISO-8601 Z>",
  "data_status": "verified | placeholder",
  "provenance": { "sources": [ { "file": "...", "upstream_origin": "...", "kind": "...", "sha256": "...", "bytes": 0 } ] },
  "notes": ["..."],
  "models": { "m1": "..." },
  "<rows_key>": [],
  "n_rows": 0
}
```

| Dataset | Rows key | Extra keys |
| --- | --- | --- |
| `cohort_summary` | `cohorts` | `exposure_distributions`, `covariates`, `samples_by_year`, `weather_monthly`, `weather_annual_hot_days` |
| `baseline_table` | `rows` | — |
| `exposure_response` | `rows` | `vocabularies` |
| `interaction_tests` | `rows` | — |
| `sensitivity` | `rows` | `families` |
| `provenance_manifest` | `entries` | `confidence_definitions`, `confidence_counts` |

`manifest.json` is the index. It repeats `data_status` and `n_rows` per file and sets `contains_individual_level_data` to `false`.

`data_status` is `verified` only when the builder read a real aggregate source. `placeholder` means the payload is a fixture. For `provenance_manifest`, verified means the extract exists; figure-level `confidence` may still be MEDIUM or UNRESOLVED.

Rebuild with `python3 scripts/build_aggregates.py`. `--check` compares a fresh build to `results/json/` (ignoring `generated_utc`).
