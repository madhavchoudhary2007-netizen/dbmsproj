import { Row } from "@/lib/api";
import { Button, DataTable } from "../ui";

export function SessionResults({
  results,
  canControl,
  setResultModal,
}: {
  results: Row[];
  canControl: boolean;
  setResultModal: (value: boolean) => void;
}) {
  return (
    <div className="results-table">
      {results.some((result) => result.provisional === true) && (
        <div className="notice">
          Historical time and grid penalties are recorded but not applied to official order or points. Review the penalties before treating results as final.
        </div>
      )}
      <div className="panel-heading">
        <div>
          <div className="eyebrow">
            {results.some((result) => result.provisional === true)
              ? "PROVISIONAL RESULTS"
              : "OFFICIAL RESULTS"}
          </div>
          <h2>{results.length} classified entries</h2>
        </div>
        {canControl && (
          <Button onClick={() => setResultModal(true)}>
            Update a result
          </Button>
        )}
      </div>
      <DataTable
        rows={results}
        columns={Object.keys(results[0]).filter(
          (k) => typeof results[0][k] !== "object",
        )}
      />
    </div>
  );
}
