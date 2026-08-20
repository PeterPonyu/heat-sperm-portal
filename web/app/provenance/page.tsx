import { NotesList } from "@/components/NotesList";
import { PageHeader } from "@/components/PageHeader";
import { SourceList } from "@/components/SourceList";
import { provenanceManifest } from "@/lib/data";

export const metadata = { title: "Provenance" };

export default function ProvenancePage() {
  const data = provenanceManifest;
  const counts = data.confidence_counts;
  return (
    <>
      <PageHeader data={data} title="Figure provenance" />
      {data.data_status === "verified" ? (
        <div className="banner policy" role="status">
          {counts
            ? `${data.n_rows ?? data.entries.length} links: ${counts.HIGH ?? 0} HIGH, ${counts.MEDIUM ?? 0} MEDIUM, ${counts.LOW ?? 0} LOW, ${counts.UNRESOLVED ?? 0} UNRESOLVED (not upgraded).`
            : "Figure-level confidence is shown as recorded. Unresolved rows are not upgraded."}
        </div>
      ) : (
        <div className="banner pending" role="status">
          Pending. No upstream provenance extract was found. Rows below are a field-shape fixture.
        </div>
      )}
      <div className="table-wrap">
        <table className="data">
          <thead>
            <tr>
              <th>Figure</th>
              <th>Script</th>
              <th>Inputs</th>
              <th>Confidence</th>
              <th>Status</th>
              <th>Reason</th>
            </tr>
          </thead>
          <tbody>
            {data.entries.map((entry) => {
              const script = entry.script ?? entry.script_path ?? null;
              const inputs = entry.input_files ?? entry.input_data_paths ?? [];
              const confidence = entry.confidence;
              return (
                <tr key={entry.figure_id}>
                  <td className="nowrap">{entry.figure_id}</td>
                  <td>{script ? <code>{script}</code> : "—"}</td>
                  <td>
                    {inputs.length
                      ? inputs.map((name) => (
                          <div key={name}>
                            <code>{name}</code>
                          </div>
                        ))
                      : "—"}
                  </td>
                  <td>
                    {confidence ? <span className={`badge ${confidence}`}>{confidence}</span> : "—"}
                  </td>
                  <td>{entry.status}</td>
                  <td className="reason-cell">{entry.unresolved_reason ?? "—"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {data.confidence_definitions ? (
        <ul className="notes">
          {Object.entries(data.confidence_definitions).map(([level, text]) => (
            <li key={level}>
              <span className={`badge ${level}`}>{level}</span> {text}
            </li>
          ))}
        </ul>
      ) : null}
      <NotesList notes={data.notes} />
      <SourceList sources={data.provenance.sources} />
    </>
  );
}
