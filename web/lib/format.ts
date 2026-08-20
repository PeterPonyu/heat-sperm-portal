export function fmtInt(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return Math.round(value).toLocaleString("en-US");
}

export function fmtNum(value: number | null | undefined, digits = 3): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return value.toLocaleString("en-US", {
    minimumFractionDigits: 0,
    maximumFractionDigits: digits,
  });
}

export function fmtFixed(value: number | null | undefined, digits: number): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return value.toFixed(digits);
}

export function fmtP(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  if (value !== 0 && Math.abs(value) < 0.0001) return value.toExponential(2);
  return value.toFixed(4);
}

export function fmtYearSpan(start: number | null | undefined, end: number | null | undefined): string {
  if (start == null && end == null) return "—";
  if (start == null) return String(end);
  if (end == null) return String(start);
  return `${start}–${end}`;
}

export function uniqueSorted(values: Array<string | null | undefined>): string[] {
  return Array.from(new Set(values.filter((v): v is string => Boolean(v)))).sort();
}
