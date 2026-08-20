import { NotesList } from "@/components/NotesList";
import { PageHeader } from "@/components/PageHeader";
import { SourceList } from "@/components/SourceList";
import { baselineTable } from "@/lib/data";
import { fmtInt, fmtNum } from "@/lib/format";

export const metadata = { title: "Baseline" };

export default function BaselinePage() {
  const data = baselineTable;
  return (
    <>
      <PageHeader data={data} title="Baseline semen parameters" />
      <NotesList notes={data.notes} />
      <div className="table-wrap">
        <table className="data">
          <thead>
            <tr>
              <th>Cohort</th>
              <th>Outcome</th>
              <th>Stage</th>
              <th>Unit</th>
              <th>Median</th>
              <th>P25</th>
              <th>P75</th>
              <th>Mean</th>
              <th>SD</th>
              <th>n</th>
            </tr>
          </thead>
          <tbody>
            {data.rows.map((row) => (
              <tr key={`${row.cohort}-${row.outcome}`}>
                <td>{row.cohort}</td>
                <td>{row.outcome_label}</td>
                <td>{row.stage}</td>
                <td>{row.native_unit}</td>
                <td className="num">{fmtNum(row.median, 2)}</td>
                <td className="num">{fmtNum(row.p25, 2)}</td>
                <td className="num">{fmtNum(row.p75, 2)}</td>
                <td className="num">{fmtNum(row.mean, 2)}</td>
                <td className="num">{fmtNum(row.sd, 3)}</td>
                <td className="num">{fmtInt(row.n)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <SourceList sources={data.provenance.sources} />
    </>
  );
}
