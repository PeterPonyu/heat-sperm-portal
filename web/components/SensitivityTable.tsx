"use client";

import { useMemo, useState } from "react";
import { fmtFixed, fmtInt, fmtP, uniqueSorted } from "@/lib/format";
import type { SensitivityRow } from "@/lib/types";

const ALL = "all";

export function SensitivityTable({
  rows,
  families,
}: {
  rows: SensitivityRow[];
  families: string[];
}) {
  const [family, setFamily] = useState(ALL);
  const [cohort, setCohort] = useState(ALL);

  const cohorts = useMemo(() => uniqueSorted(rows.map((r) => r.cohort)), [rows]);

  const filtered = useMemo(
    () =>
      rows.filter(
        (row) =>
          (family === ALL || row.family === family) &&
          (cohort === ALL || row.cohort === cohort),
      ),
    [rows, family, cohort],
  );

  return (
    <>
      <div className="filters">
        <label>
          Family
          <select value={family} onChange={(e) => setFamily(e.target.value)}>
            <option value={ALL}>All</option>
            {families.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>
        <label>
          Cohort
          <select value={cohort} onChange={(e) => setCohort(e.target.value)}>
            <option value={ALL}>All</option>
            {cohorts.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>
      </div>
      <p className="filter-count">
        Showing {filtered.length} of {rows.length} sensitivity rows
      </p>
      <div className="table-wrap">
        <table className="data">
          <thead>
            <tr>
              <th>Family</th>
              <th>Cohort</th>
              <th>Outcome</th>
              <th>Exposure</th>
              <th>Window</th>
              <th>Variant</th>
              <th>β (SD)</th>
              <th>SE</th>
              <th>P</th>
              <th>q</th>
              <th>n</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((row, index) => (
              <tr
                key={`${row.family}-${row.cohort}-${row.outcome}-${row.exposure_metric}-${row.window}-${row.variant}-${index}`}
              >
                <td>{row.family_label}</td>
                <td>{row.cohort}</td>
                <td>{row.outcome_label}</td>
                <td>{row.exposure_metric}</td>
                <td>{row.window}</td>
                <td>{row.variant}</td>
                <td className="num">{fmtFixed(row.beta_sd, 4)}</td>
                <td className="num">{fmtFixed(row.se_sd, 4)}</td>
                <td className="num">{fmtP(row.p_value)}</td>
                <td className="num">{fmtP(row.q_value)}</td>
                <td className="num">{fmtInt(row.n)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
