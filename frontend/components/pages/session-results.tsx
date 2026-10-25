import { pretty, type Row } from "@/lib/api";
import { NbBadge } from "@/components/nb/badge";
import { NbButton } from "@/components/nb/button";
import { NbTable } from "@/components/nb/table";

export function SessionResults({
  results,
  canControl,
  setResultModal,
}: {
  results: Row[];
  canControl: boolean;
  setResultModal: (value: boolean) => void;
}) {
  const provisional = results.some((result) => result.provisional === true);
  const columns = Object.keys(results[0]).filter(
    (key) => typeof results[0][key] !== "object",
  ).map((key) => ({
    key,
    title: key.replaceAll("_", " "),
    numeric: typeof results[0][key] === "number",
    render: (row: Row) => {
      const value = pretty(row[key]);
      if (key !== "position" || ![1, 2, 3].includes(Number(row[key]))) return value;
      return (
        <span className="inline-flex min-h-[44px] min-w-[44px] items-center justify-center border-4 border-ink bg-yellow px-3 py-2 font-bold tabular-nums text-ink">
          {value}
        </span>
      );
    },
  }));

  return (
    <div className="results-table">
      {provisional && (
        <div className="notice border-4 border-ink bg-paper p-4 text-ink shadow-nb-4">
          Historical time and grid penalties are recorded but not applied to official order or points. Review the penalties before treating results as final.
        </div>
      )}
      <div className="panel-heading">
        <div>
          {provisional ? (
            <NbBadge status="PROVISIONAL">PROVISIONAL RESULTS</NbBadge>
          ) : (
            <div className="eyebrow">OFFICIAL RESULTS</div>
          )}
          <h2>{results.length} classified entries</h2>
        </div>
        {canControl && (
          <NbButton variant="secondary" onClick={() => setResultModal(true)}>
            Update a result
          </NbButton>
        )}
      </div>
      <NbTable
        state={{ status: "populated", data: results }}
        columns={columns}
        rowKey={(row, index) => String(row.id || index)}
        caption="Session results"
      />
    </div>
  );
}
