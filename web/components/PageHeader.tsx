import { StatusBadge } from "@/components/StatusBadge";
import type { Envelope } from "@/lib/types";

export function PageHeader({ data, title }: { data: Envelope; title?: string }) {
  return (
    <header>
      <p className="meta">
        <StatusBadge status={data.data_status} /> · schema {data.schema_version} · {data.n_rows ?? 0} rows · generated {data.generated_utc}
      </p>
      <h1>{title ?? data.dataset.replace(/_/g, " ")}</h1>
      <p className="lede">{data.description}</p>
    </header>
  );
}
