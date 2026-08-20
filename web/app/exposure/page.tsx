import { NotesList } from "@/components/NotesList";
import { PageHeader } from "@/components/PageHeader";
import { SourceList } from "@/components/SourceList";
import { ExposureTable } from "@/components/ExposureTable";
import { exposureResponse } from "@/lib/data";

export const metadata = { title: "Exposure–response" };

export default function ExposurePage() {
  const data = exposureResponse;
  return (
    <>
      <PageHeader data={data} title="Confirmatory exposure–response" />
      <ExposureTable rows={data.rows} />
      <NotesList notes={data.notes} />
      {data.models ? (
        <p className="meta">{Object.values(data.models).join(" ")}</p>
      ) : null}
      <SourceList sources={data.provenance.sources} />
    </>
  );
}
