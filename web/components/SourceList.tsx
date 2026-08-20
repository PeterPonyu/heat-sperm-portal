import type { SourceRef } from "@/lib/types";

export function SourceList({ sources }: { sources: SourceRef[] }) {
  return (
    <>
      <h2>Sources</h2>
      <ul className="source-list">
        {sources.map((source) => (
          <li key={source.file}>
            <code>{source.file}</code>
            {source.kind ? ` — ${source.kind}` : null}
          </li>
        ))}
      </ul>
    </>
  );
}
