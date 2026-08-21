# Analysis contract

This file records the codes and model text that `scripts/build_aggregates.py` copies into the aggregate JSON. It is a dictionary, not a results paper. Numbers live only in `results/aggregate_source/` and the derived JSON.

Upstream definitions are the analysis-host scripts (exposure-window builder and the confirmatory model). If those scripts change, update this file and the Python vocabularies together.

## Outcomes

| Code | Label | Unit | Stage |
| --- | --- | --- | --- |
| `volume` | Semen volume | mL | pre-freezing |
| `sc_pre` | Sperm concentration, pre-freezing | 10^6/mL | pre-freezing |
| `tsc` | Total sperm count | 10^6 per ejaculate | pre-freezing |
| `pr_pre` | Progressive motility, pre-freezing | % of spermatozoa | pre-freezing |
| `np_pre` | Non-progressive motility, pre-freezing | % of spermatozoa | pre-freezing |
| `im_pre` | Immotile fraction, pre-freezing | % of spermatozoa | pre-freezing |
| `sc_post` | Sperm concentration, post-thaw | 10^6/mL | post-thaw |
| `pr_post` | Progressive motility, post-thaw | % of spermatozoa | post-thaw |
| `np_post` | Non-progressive motility, post-thaw | % of spermatozoa | post-thaw |
| `im_post` | Immotile fraction, post-thaw | % of spermatozoa | post-thaw |
| `survival_post` | Post-thaw survival rate | % | post-thaw |

## Windows

Days before ejaculation, inclusive, matching the upstream `WINDOWS` dict.

| Code | Label | Phase | Days |
| --- | --- | --- | --- |
| `w0_90` | 0-90 d before ejaculation | Full spermatogenic window | 0–90 |
| `w70_90` | 70-90 d before ejaculation | Spermatogonial proliferation | 70–90 |
| `w15_69` | 15-69 d before ejaculation | Meiosis and spermiogenesis | 15–69 |
| `w0_9` | 0-9 d before ejaculation | Epididymal transit | 0–9 |
| `w10_14` | 10-14 d before ejaculation | Late epididymal | 10–14 |

## Exposure metrics

| Code | Label | Contrast | Kind |
| --- | --- | --- | --- |
| `tmax` | Window mean daily maximum temperature | per +1 °C | continuous |
| `anyhw3` | Any heatwave (≥3 consecutive days Tmax ≥35 °C) | exposed vs unexposed | binary |
| `hwp95` | Any heatwave (≥3 consecutive days Tmax ≥ warm-season 95th percentile) | exposed vs unexposed | binary |
| `ht30` / `ht32` / `ht35` | Days with Tmax at the named threshold | per +1 day | count |
| `htp90` / `htp95` | Days with Tmax at the named percentile | per +1 day | count |
| `hw2` / `hw3` / `hw4` | Heatwave days at the named duration, Tmax ≥35 °C | per +1 day | count |
| `ht35_w0_90` / `ht32_w0_90` / `ht30_w0_90` | Days at threshold in the 0–90 d window | per +10 days | count |

## Confirmatory family

Thirteen cohort–outcome combinations × four windows × three exposure metrics = **156 tests** (Wuhan and Chongqing).

Model text interned as `models.m1` in `exposure_response.json`:

> Ordinary least squares on the within-cohort standardised outcome, with donor-level cluster-robust standard errors; covariates: donor age, abstinence days, season (categorical) and centred calendar year. Benjamini–Hochberg FDR across the 156-test two-cohort confirmatory family.

Coefficients are in within-cohort SD units. Native-unit back-conversion is attached only when `tableSY_native_unit_effects.csv` has a matching row.

## Sample definitions (do not mix)

Counts are labelled by definition because they are not the same records:

1. Harmonised source table, all records (`cohort_aggregate.json`) — sample counts only; distinct-key counts from that table are omitted.
2. Locked complete-parameter analysis sample (`SX_SY_provenance.json`).
3. Confirmatory model sample (maximum *n* in the 156-test family).

Wenzhou and Xiamen are supplementary. Xiamen currently has weather span only.

## Sensitivity families

Codes in `sensitivity.json` → `families`:

- `threshold_variant`, `duration_variant`
- `pollutant_adjustment`
- `humidity_adjustment`
- `covariate_adjustment`
- `pandemic_exclusion`
- `analysis_sample_variant` (superseded harmonised-table family)

Sensitivity rows are not in the 156-test FDR family unless the source file already carries a *q* value.

## Interaction tests

Two unreconciled sets: the primary cohort-by-exposure interaction file (sparse columns) and the supplementary interaction table (per-cohort slopes, per +10 high-temperature days). Null fields stay null.

## Provenance

Figure-to-script records are a sanitized extract in `results/aggregate_source/provenance_manifest.json`. Public fields are figure name, script, input filenames, confidence, and unresolved reason. UNRESOLVED and MEDIUM rows stay as recorded.
