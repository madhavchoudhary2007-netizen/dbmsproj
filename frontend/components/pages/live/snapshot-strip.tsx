import { pretty } from "@/lib/api";

export function SnapshotStrip({
  snapshot,
}: {
  snapshot: Record<string, unknown> | null;
}) {
  return (
    <div className="snapshot-strip">
      {Object.entries(snapshot || {})
        .filter(
          ([k, v]) =>
            !["participants", "drivers", "timing", "safety_car"].includes(
              k,
            ) && typeof v !== "object",
        )
        .map(([k, v]) => (
          <div key={k}>
            <small>{k.replaceAll("_", " ")}</small>
            <b>{pretty(v)}</b>
          </div>
        ))}
    </div>
  );
}
