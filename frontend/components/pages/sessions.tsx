import { Button, StateMessage } from "@/components/ui";
import { useSessionPage } from "@/lib/use-session-page";
import { SessionControls } from "./session-controls";
import { SessionEditorModal, SessionResultModal } from "./session-modals";
import { SessionOverview } from "./session-overview";
import { SessionResults } from "./session-results";
import { SessionSimulator } from "./session-simulator";

export function SessionPage() {
  const {
    resultModal,
    setResultModal,
    editModal,
    setEditModal,
    resultsLoaded,
    setResultsLoaded,
    selected,
    setSelected,
    actionMsg,
    setActionMsg,
    modal,
    setModal,
    busy,
    simCars,
    setSimCars,
    simRate,
    setSimRate,
    simMessage,
    results,
    setResults,
    rows,
    events,
    drivers,
    err,
    loading,
    load,
    canManage,
    canControl,
    current,
    perform,
    saveResult,
    simulate,
    getResults,
    fields,
    save,
    deleteSession,
  } = useSessionPage();
  return (
    <>
      <SessionOverview
        canManage={canManage}
        setEditModal={setEditModal}
        setModal={setModal}
        rows={rows}
        events={events}
        err={err}
        loading={loading}
        load={load}
        setSelected={setSelected}
        setResults={setResults}
        setResultsLoaded={setResultsLoaded}
        setActionMsg={setActionMsg}
      />
      {actionMsg && <div className="notice">{actionMsg}</div>}
      {current && (
        <div className="panel session-control">
          <div className="panel-heading">
            <div>
              <div className="eyebrow">SELECTED SESSION</div>
              <h2>
                {String(
                  current.event_name || current.session_type || "Session",
                )}
              </h2>
            </div>
            <span className="state-pill">{String(current.state)}</span>
          </div>
          <SessionControls
            current={current}
            canManage={canManage}
            canControl={canControl}
            setEditModal={setEditModal}
            setModal={setModal}
            perform={perform}
            setResultModal={setResultModal}
            getResults={getResults}
          />
          {canControl && (
            <SessionSimulator
              drivers={drivers}
              current={current}
              simCars={simCars}
              setSimCars={setSimCars}
              simRate={simRate}
              setSimRate={setSimRate}
              simulate={simulate}
            />
          )}
          {simMessage && <div className="notice">{simMessage}</div>}
          {resultsLoaded && results.length === 0 && (
            <StateMessage empty="No result rows are recorded for this session." />
          )}
          {results.length > 0 && (
            <SessionResults
              results={results}
              canControl={canControl}
              setResultModal={setResultModal}
            />
          )}
          {canManage && (
            <div className="form-actions destructive-row">
              <Button
                kind="danger"
                disabled={busy}
                onClick={() => void deleteSession()}
              >
                Delete session
              </Button>
            </div>
          )}
          {resultModal && canControl && (
            <SessionResultModal
              drivers={drivers}
              busy={busy}
              saveResult={saveResult}
              setResultModal={setResultModal}
            />
          )}
        </div>
      )}
      {modal && canManage && (
        <SessionEditorModal
          editModal={editModal}
          current={current}
          fields={fields}
          save={save}
          busy={busy}
          setModal={setModal}
        />
      )}
    </>
  );
}
