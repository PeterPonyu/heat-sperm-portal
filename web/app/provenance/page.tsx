import { NotesList } from "@/components/NotesList";
import { PageHeader } from "@/components/PageHeader";
import { SourceList } from "@/components/SourceList";
import { provenanceManifest } from "@/lib/data";

export const metadata = { title: "Provenance" };

export default function ProvenancePage() {
  const data = provenanceManifest;
  const pending = data.data_status !== "verified";
  return (
    <>
      <PageHeader data={data} title="Figure provenance" />
      {pending ? (
        <div className="banner pending" role="status">
          Pending. No upstream <code>results/aggregate_source/provenance_manifest.json</code> was
          found on this machine. The rows below are a field-shape fixture. Figure identifiers may
          be real; paths, modification times, and status values are not.
        </div>
      ) : null}
      <NotesList notes={data.notes} />
      <div className="table-wrap">
        <table className="data">
          <thead>
            <tr>
              <th>Figure</th>
              <th>Panels</th>
              <th>Script</th>
              <th>Inputs</th>
              <th>Outputs</th>
              <th>mtime</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {data.entries.map((entry) => (
              <tr key={entry.figure_id}>
                <td>{entry.figure_id}</td>
                <td>{entry.panel_letters.join(", ")}</td>
                <td>
                  <code>{entry.script_path}</code>
                </td>
                <td>
                  {entry.input_data_paths.map((path) => (
                    <div key={path}>
                      <code>{path}</code>
                    </div>
                  ))}
                </td>
                <td>
                  {entry.output_paths.map((path) => (
                    <div key={path}>
                      <code>{path}</code>
                    </div>
                  ))}
                </td>
                <td>{entry.mtime}</td>
                <td>{entry.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <SourceList sources={data.provenance.sources} />
    </>
  );
}
