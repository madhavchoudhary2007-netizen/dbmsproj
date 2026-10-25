import { StateMessage } from "@/components/ui";
import { NbBadge } from "@/components/nb/badge";
import { NbButton } from "@/components/nb/button";
import { NbCard } from "@/components/nb/card";
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
      <div className="grid min-w-0 gap-4 lg:grid-cols-[2fr_3fr]">
      <SessionOverview
        canManage={canManage}
        primary={!modal && !resultModal}
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
      {current && (
        <NbCard className="session-control min-w-0">
          {actionMsg && <div className="notice border-4 border-ink bg-paper p-4 text-ink shadow-nb-4">{actionMsg}</div>}
          <div className="panel-heading">
            <div>
              <div className="eyebrow">SELECTED SESSION</div>
              <h2 className="text-[length:var(--fs-h3)] font-bold">
                {String(
                  current.event_name || current.session_type || "Session",
                )}
              </h2>
            </div>
            <NbBadge status={String(current.state)}>{String(current.state)}</NbBadge>
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
          {simMessage && <div className="notice border-4 border-ink bg-paper p-4 text-ink shadow-nb-4">{simMessage}</div>}
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
              <NbButton
                variant="danger"
                disabled={busy}
                onClick={() => void deleteSession()}
              >
                Delete session
              </NbButton>
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
        </NbCard>
      )}
      {!current && (
        <NbCard className="session-control min-w-0">
          {actionMsg && <div className="notice border-4 border-ink bg-paper p-4 text-ink shadow-nb-4">{actionMsg}</div>}
          <p className="eyebrow text-[length:var(--fs-label)]">SELECTED SESSION</p>
          <h2 className="text-[length:var(--fs-h3)] font-bold">No session selected</h2>
          <p>Select a session from the list to review its controls and classified results.</p>
        </NbCard>
      )}
      </div>
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
