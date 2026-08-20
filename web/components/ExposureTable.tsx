"use client";

import { useMemo, useState } from "react";
import { fmtFixed, fmtInt, fmtP, uniqueSorted } from "@/lib/format";
import type { ExposureRow } from "@/lib/types";

const ALL = "all";

export function ExposureTable({ rows }: { rows: ExposureRow[] }) {
  const [cohort, setCohort] = useState(ALL);
  const [outcome, setOutcome] = useState(ALL);
  const [windowCode, setWindow] = useState(ALL);
  const [exposure, setExposure] = useState(ALL);
  const [fdrOnly, setFdrOnly] = useState(false);

  const options = useMemo(
    () => ({
      cohort: uniqueSorted(rows.map((r) => r.cohort)),
      outcome: uniqueSorted(rows.map((r) => r.outcome_label)),
      window: uniqueSorted(rows.map((r) => r.window_label)),
      exposure: uniqueSorted(rows.map((r) => r.exposure_metric)),
    }),
    [rows],
  );

  const filtered = useMemo(
    () =>
      rows.filter(
        (row) =>
          (cohort === ALL || row.cohort === cohort) &&
          (outcome === ALL || row.outcome_label === outcome) &&
          (windowCode === ALL || row.window_label === windowCode) &&
          (exposure === ALL || row.exposure_metric === exposure) &&
          (!fdrOnly || row.fdr_significant),
      ),
    [rows, cohort, outcome, windowCode, exposure, fdrOnly],
  );

  return (
    <>
      <div className="filters">
        <label>
          Cohort
          <select value={cohort} onChange={(e) => setCohort(e.target.value)}>
            <option value={ALL}>All</option>
            {options.cohort.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>
        <label>
          Outcome
          <select value={outcome} onChange={(e) => setOutcome(e.target.value)}>
            <option value={ALL}>All</option>
            {options.outcome.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>
        <label>
          Window
          <select value={windowCode} onChange={(e) => setWindow(e.target.value)}>
            <option value={ALL}>All</option>
            {options.window.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>
        <label>
          Exposure
          <select value={exposure} onChange={(e) => setExposure(e.target.value)}>
            <option value={ALL}>All</option>
            {options.exposure.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>
        <label className="check">
          <input
            type="checkbox"
            checked={fdrOnly}
            onChange={(e) => setFdrOnly(e.target.checked)}
          />
          FDR q &lt; 0.05 only
        </label>
      </div>
      <p className="filter-count">
        Showing {filtered.length} of {rows.length} confirmatory rows
      </p>
      <div className="table-wrap">
        <table className="data">
          <thead>
            <tr>
              <th>Cohort</th>
              <th>Outcome</th>
              <th>Exposure</th>
              <th>Contrast</th>
              <th>Window</th>
              <th>β (SD)</th>
              <th>SE</th>
              <th>95% CI</th>
              <th>P</th>
              <th>q</th>
              <th>FDR</th>
              <th>Native effect</th>
              <th>n</th>
              <th>Donors</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((row) => (
              <tr key={`${row.cohort}-${row.outcome}-${row.exposure_metric}-${row.window}`}>
                <td>{row.cohort}</td>
                <td>{row.outcome_label}</td>
                <td>{row.exposure_metric}</td>
                <td>{row.exposure_contrast}</td>
                <td>{row.window}</td>
                <td className="num">{fmtFixed(row.beta_sd, 4)}</td>
                <td className="num">{fmtFixed(row.se_sd, 4)}</td>
                <td className="num">
                  {row.ci_low_sd == null && row.ci_high_sd == null
                    ? "—"
                    : `${fmtFixed(row.ci_low_sd, 4)}, ${fmtFixed(row.ci_high_sd, 4)}`}
                </td>
                <td className="num">{fmtP(row.p_value)}</td>
                <td className="num">{fmtP(row.q_value)}</td>
                <td>{row.fdr_significant ? "q < 0.05" : "—"}</td>
                <td className="num">
                  {row.native
                    ? `${fmtFixed(row.native.effect, 4)} ${row.native.unit}`
                    : "—"}
                </td>
                <td className="num">{fmtInt(row.n)}</td>
                <td className="num">{fmtInt(row.n_donors)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
