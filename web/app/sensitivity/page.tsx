import { NotesList } from "@/components/NotesList";
import { PageHeader } from "@/components/PageHeader";
import { SensitivityTable } from "@/components/SensitivityTable";
import { SourceList } from "@/components/SourceList";
import { sensitivity } from "@/lib/data";

export const metadata = { title: "Sensitivity" };

export default function SensitivityPage() {
  const data = sensitivity;
  return (
    <>
      <PageHeader data={data} title="Sensitivity analyses" />
      <SensitivityTable rows={data.rows} families={data.families} />
      <NotesList notes={data.notes} />
      <SourceList sources={data.provenance.sources} />
    </>
  );
}
