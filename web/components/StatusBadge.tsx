import type { DataStatus } from "@/lib/types";

export function StatusBadge({ status }: { status: DataStatus }) {
  return <span className={`badge ${status}`}>{status}</span>;
}
