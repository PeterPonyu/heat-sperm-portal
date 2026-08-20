import { NotesList } from "@/components/NotesList";
import { PageHeader } from "@/components/PageHeader";
import { SourceList } from "@/components/SourceList";
import { cohortSummary } from "@/lib/data";
import { fmtInt, fmtNum, fmtYearSpan } from "@/lib/format";

export const metadata = { title: "Cohorts" };

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export default function CohortPage() {
  const data = cohortSummary;
  return (
    <>
      <PageHeader data={data} title="Cohort summary" />
      <NotesList notes={data.notes} />

      <h2>Cities</h2>
      <div className="table-wrap">
        <table className="data">
          <thead>
            <tr>
              <th>City</th>
              <th>Role</th>
              <th>Study years</th>
              <th>Weather record</th>
              <th>Weather days</th>
              <th>Sample definition</th>
              <th>Samples</th>
              <th>Donors</th>
            </tr>
          </thead>
          <tbody>
            {data.cohorts.map((cohort) =>
              (cohort.samples.length ? cohort.samples : [null]).map((sample, index) => (
                <tr key={`${cohort.city}-${index}`}>
                  {index === 0 ? (
                    <>
                      <td>{cohort.city}</td>
                      <td>{cohort.role}</td>
                      <td className="num">{fmtYearSpan(cohort.period_start_year, cohort.period_end_year)}</td>
                      <td className="nowrap">
                        {cohort.weather_record_start && cohort.weather_record_end
                          ? `${cohort.weather_record_start} \u2013 ${cohort.weather_record_end}`
                          : "—"}
                      </td>
                      <td className="num">{fmtInt(cohort.weather_days_observed)}</td>
                    </>
                  ) : (
                    <>
                      <td />
                      <td />
                      <td />
                      <td />
                      <td />
                    </>
                  )}
                  <td>{sample?.sample_definition ?? "No sample counts in this file"}</td>
                  <td className="num">{fmtInt(sample?.n_samples)}</td>
                  <td className="num" title={sample?.n_donors_note}>
                    {fmtInt(sample?.n_donors)}
                  </td>
                </tr>
              )),
            )}
          </tbody>
        </table>
      </div>

      <h2>Covariates (harmonised source table)</h2>
      <div className="table-wrap">
        <table className="data">
          <thead>
            <tr>
              <th>City</th>
              <th>Variable</th>
              <th>Unit</th>
              <th>Median</th>
              <th>P25</th>
              <th>P75</th>
              <th>n</th>
            </tr>
          </thead>
          <tbody>
            {data.covariates.map((row) => (
              <tr key={`${row.city}-${row.variable}`}>
                <td>{row.city}</td>
                <td>{row.variable_label}</td>
                <td>{row.unit}</td>
                <td className="num">{fmtNum(row.median, 2)}</td>
                <td className="num">{fmtNum(row.p25, 2)}</td>
                <td className="num">{fmtNum(row.p75, 2)}</td>
                <td className="num">{fmtInt(row.n)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h2>Exposure distributions</h2>
      <div className="table-wrap">
        <table className="data">
          <thead>
            <tr>
              <th>City</th>
              <th>Metric</th>
              <th>Window</th>
              <th>Unit</th>
              <th>Median</th>
              <th>P25</th>
              <th>P75</th>
              <th>n</th>
            </tr>
          </thead>
          <tbody>
            {data.exposure_distributions.map((row) => (
              <tr key={`${row.city}-${row.metric}`}>
                <td>{row.city}</td>
                <td>{row.metric_label}</td>
                <td>{row.window_label}</td>
                <td>{row.unit}</td>
                <td className="num">{fmtNum(row.median, 2)}</td>
                <td className="num">{fmtNum(row.p25, 2)}</td>
                <td className="num">{fmtNum(row.p75, 2)}</td>
                <td className="num">{fmtInt(row.n)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h2>Samples by year</h2>
      <div className="table-wrap">
        <table className="data">
          <thead>
            <tr>
              <th>City</th>
              <th>Year</th>
              <th>Samples</th>
              <th>Donors</th>
            </tr>
          </thead>
          <tbody>
            {data.samples_by_year.map((row) => (
              <tr key={`${row.city}-${row.year}`}>
                <td>{row.city}</td>
                <td className="num">{row.year}</td>
                <td className="num">{fmtInt(row.n_samples)}</td>
                <td className="num">{fmtInt(row.n_donors)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h2>Monthly climatology (Tmax)</h2>
      <div className="table-wrap">
        <table className="data">
          <thead>
            <tr>
              <th>City</th>
              <th>Month</th>
              <th>Days</th>
              <th>Mean Tmax</th>
              <th>P10</th>
              <th>P90</th>
            </tr>
          </thead>
          <tbody>
            {data.weather_monthly.map((row) => (
              <tr key={`${row.city}-${row.month}`}>
                <td>{row.city}</td>
                <td>{MONTHS[row.month - 1] ?? row.month}</td>
                <td className="num">{fmtInt(row.n_days)}</td>
                <td className="num">{fmtNum(row.mean_tmax, 2)}</td>
                <td className="num">{fmtNum(row.p10_tmax, 2)}</td>
                <td className="num">{fmtNum(row.p90_tmax, 2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h2>Annual hot days</h2>
      <div className="table-wrap">
        <table className="data">
          <thead>
            <tr>
              <th>City</th>
              <th>Year</th>
              <th>Days observed</th>
              <th>Tmax ≥30</th>
              <th>Tmax ≥32</th>
              <th>Tmax ≥35</th>
              <th>Max Tmax</th>
            </tr>
          </thead>
          <tbody>
            {data.weather_annual_hot_days.map((row) => (
              <tr key={`${row.city}-${row.year}`}>
                <td>{row.city}</td>
                <td className="num">{row.year}</td>
                <td className="num">{fmtInt(row.n_days_observed)}</td>
                <td className="num">{fmtInt(row.days_tmax_ge_30)}</td>
                <td className="num">{fmtInt(row.days_tmax_ge_32)}</td>
                <td className="num">{fmtInt(row.days_tmax_ge_35)}</td>
                <td className="num">{fmtNum(row.max_tmax, 1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <SourceList sources={data.provenance.sources} />
    </>
  );
}
