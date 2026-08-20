# Data policy

This repository is an **aggregate-statistics portal**. It may hold grouped counts, model coefficients, and city-level weather summaries. It may not hold donor-level records.

## Hard rule

**Donor-level data never leave the analysis host.**

The confidential tables (harmonised sample files, donor-linked exposure tables, clinic workbooks, and any file that can be joined back to a person) stay on the machine where the analysis was run. They are not copied into this repository, not committed, not uploaded as GitHub Actions artifacts, and not published with the static site.

The only sanctioned bridge is `scripts/remote_summarise.py`, which is run **on the analysis host**. It reads the confidential tables in place and writes grouped statistics (counts, medians, quartiles). No row, key, or free-text identifier is emitted.

## What this repository may contain

- Aggregate JSON under `results/json/` and the copy served at `web/public/data/`
- Aggregate source tables under `results/aggregate_source/` (model output and grouped summaries already reduced on the host)
- Build scripts, schema notes, and the static viewer

Every published dataset carries `data_status`: `verified` (built from a real aggregate file) or `placeholder` / pending (shape only; not a result).

## What this repository must never contain

- `spermdata/` or any copy of the upstream confidential tree
- Spreadsheets (`*.xlsx`, `*.xls`, `*.xlsm`, `*.xlsb`)
- `harmonized_donor_samples.csv`, `harmonized_*_clinical.csv`, `donor_exposure*`, `xiamen_exposure*`
- `data/raw/`, `raw_data/`
- Single-cell or matrix containers (`.h5ad`, `.h5`, `.loom`, `.rds`, `.RData`)
- Secrets (`.env`, keys, credentials)

`.gitignore` blocks these paths before `git init`. `scripts/check-no-pii.sh` is the commit gate (path, content, and tabular-size rules). A pre-commit hook runs the staged-file scan.

## Site and CI

The GitHub Pages workflow builds `web/` with `output: 'export'` and may upload only `web/out`. That tree is HTML plus the same aggregate JSON already in `web/public/data/`. It must not contain donor tables.

The commit hook is copied into `.git/hooks/pre-commit` (`scripts/install-hooks.sh`). This repository does not set `core.hooksPath`.

## If a forbidden file appears

Stop. Do not commit. Do not push. Remove the file from the working tree and the index. See `scripts/check-no-pii.sh` and this document.
