import { NotesList } from "@/components/NotesList";
import { PageHeader } from "@/components/PageHeader";
import { SourceList } from "@/components/SourceList";
import { interactionTests } from "@/lib/data";
import { fmtFixed, fmtInt, fmtP } from "@/lib/format";

export const metadata = { title: "Interaction" };

export default function InteractionPage() {
  const data = interactionTests;
  return (
    <>
      <PageHeader data={data} title="Cohort-by-exposure interaction" />
      <div className="table-wrap">
        <table className="data">
          <thead>
            <tr>
              <th>Set</th>
              <th>Outcome</th>
              <th>Exposure</th>
              <th>Contrast</th>
              <th>Window</th>
              <th>β interaction (SD)</th>
              <th>SE</th>
              <th>95% CI</th>
              <th>P</th>
              <th>Het. p&lt;0.05</th>
              <th>β Wuhan</th>
              <th>β Chongqing</th>
              <th>n obs</th>
              <th>Donors</th>
              <th>Model</th>
            </tr>
          </thead>
          <tbody>
            {data.rows.map((row, index) => (
              <tr key={`${row.test_set}-${row.outcome}-${row.exposure_metric}-${index}`}>
                <td>{row.test_set}</td>
                <td>{row.outcome_label}</td>
                <td>{row.exposure_label ?? row.exposure_metric}</td>
                <td>{row.exposure_contrast}</td>
                <td>{row.window_label}</td>
                <td className="num">{fmtFixed(row.beta_interaction_sd, 4)}</td>
                <td className="num">{fmtFixed(row.se_interaction, 4)}</td>
                <td className="num">
                  {row.ci_low_interaction == null && row.ci_high_interaction == null
                    ? "—"
                    : `${fmtFixed(row.ci_low_interaction, 4)}, ${fmtFixed(row.ci_high_interaction, 4)}`}
                </td>
                <td className="num">{fmtP(row.p_interaction)}</td>
                <td>{row.heterogeneous_at_0_05 ? "yes" : "no"}</td>
                <td className="num">{fmtFixed(row.beta_wuhan_sd, 4)}</td>
                <td className="num">{fmtFixed(row.beta_chongqing_sd, 4)}</td>
                <td className="num">{fmtInt(row.n_obs)}</td>
                <td className="num">{fmtInt(row.n_donors)}</td>
                <td>{row.model_id}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <NotesList notes={data.notes} />
      {data.models ? (
        <ul className="notes">
          {Object.entries(data.models).map(([id, text]) => (
            <li key={id}>
              <code>{id}</code>: {text}
            </li>
          ))}
        </ul>
      ) : null}
      <SourceList sources={data.provenance.sources} />
    </>
  );
}
