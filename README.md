# Heat-exposure / cryopreserved donor-sperm aggregate tables

Aggregate tables from a heat-exposure semen-quality analysis of cryopreserved donor sperm. Individual-level records are not stored here and are not served by the site.

The pages list the numbers already written to `web/public/data/*.json`. They do not add estimates, claims, or journal packaging.

## Privacy

Donor-level data never leave the analysis host. See [DATA_POLICY.md](DATA_POLICY.md).

Do not add `spermdata/`, workbooks, or donor-linked CSVs. `scripts/check-no-pii.sh` must pass in `--staged`, `--tracked`, and `--worktree` modes before a commit is considered clean.

## Layout

| Path | Role |
| --- | --- |
| `results/aggregate_source/` | Grouped summaries and model output copied from the analysis host |
| `results/json/` | Canonical aggregate JSON |
| `web/public/data/` | Same JSON, served by the static site |
| `scripts/build_aggregates.py` | Rebuilds JSON from `results/aggregate_source/` |
| `scripts/remote_summarise.py` | Host-side reducer (run where the confidential tables live) |
| `analysis/ANALYSIS_CONTRACT.md` | Outcome, window, exposure, and model contract |
| `schema/README.md` | JSON envelope |
| `web/` | Next.js static-export viewer |

## Rebuild aggregates

```bash
python3 scripts/build_aggregates.py          # write results/json and web/public/data
python3 scripts/build_aggregates.py --check  # fail if committed JSON is stale
```

`provenance_manifest` is a sanitized public extract of the analysis-host audit (figure name, script name, input filenames, confidence, unresolved reason). Absolute paths are stripped. Figure-level UNRESOLVED / MEDIUM values are not upgraded.

## Web viewer

```bash
cd web
npm ci
npm run typecheck
npm run build          # writes web/out (static export)
```

`npm run dev` serves the App Router locally. Production viewing uses the export:

```bash
python3 -m http.server --directory web/out 4173
```

The site reads only `public/data/*.json` (copied into `out/data/` at build). It does not query an analysis host.

## Git

This tree is a local git repository (`master`, no remote). Hooks are copied into `.git/hooks/` (see `scripts/install-hooks.sh`). Do not use `git add -A`. Stage explicit paths. Pushing and creating a remote are manual steps for the maintainer.

## GitHub Pages (when a remote exists)

`.github/workflows/pages.yml` builds the static export on push / pull request / `workflow_dispatch`. It does not run on a schedule. Upload and deploy run only when the repository variable `ENABLE_PAGES` is `true`. The uploaded artifact is `web/out` only.

`.github/workflows/ci.yml` repeats the same gates plus `npm ci` / typecheck / export. It does not compile `article.tex` and does not download datasets.
