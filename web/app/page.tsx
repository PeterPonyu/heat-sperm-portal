import Link from "next/link";
import { StatusBadge } from "@/components/StatusBadge";
import { manifest } from "@/lib/data";

const ROUTES: Record<string, string> = {
  cohort_summary: "/cohort/",
  baseline_table: "/baseline/",
  exposure_response: "/exposure/",
  interaction_tests: "/interaction/",
  sensitivity: "/sensitivity/",
  provenance_manifest: "/provenance/",
};

export default function HomePage() {
  return (
    <>
      <h1>Published aggregates</h1>
      <p className="lede">
        Six JSON datasets, rebuilt from grouped model output. The index below is{" "}
        <code>manifest.json</code>. Individual-level data are not present (
        <code>contains_individual_level_data</code>: {String(manifest.contains_individual_level_data)}
        ).
      </p>
      <div className="banner policy">
        Donor-level tables never leave the analysis host. This site only renders the files in{" "}
        <code>public/data/</code>.
      </div>
      <p className="meta">
        Schema {manifest.schema_version} · generated {manifest.generated_utc}
      </p>
      <div className="card-grid">
        {manifest.datasets.map((dataset) => (
          <article className="card" key={dataset.file}>
            <StatusBadge status={dataset.data_status} />
            <h2>
              <Link href={ROUTES[dataset.dataset] ?? "/"}>{dataset.dataset.replace(/_/g, " ")}</Link>
            </h2>
            <p>{dataset.description}</p>
            <p className="card-meta">
              {dataset.n_rows ?? 0} rows · {dataset.file}
            </p>
          </article>
        ))}
      </div>
    </>
  );
}
