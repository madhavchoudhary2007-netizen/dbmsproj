import { api, asArray, Row } from "@/lib/api";

export async function performSessionAction(
  action: string,
  selected: string,
  setActionMsg: (value: string) => void,
  load: () => Promise<void>,
) {
  if (!selected) return;
  setActionMsg("");
  try {
    await api(`/sessions/${selected}/action`, {
      method: "POST",
      body: JSON.stringify({ action }),
    });
    setActionMsg(`Session ${action} request completed.`);
    await load();
  } catch (e) {
    setActionMsg(e instanceof Error ? e.message : "Action failed");
  }
}

export async function simulateSession(
  action: string,
  selected: string,
  setSimMessage: (value: string) => void,
  simCars: number,
  simRate: number,
  load: () => Promise<void>,
) {
  if (!selected) return;
  setSimMessage("");
  try {
    const response = await api<{ state?: string; cars?: number; rate_hz?: number }>(`/sessions/${selected}/simulate`, {
      method: "POST",
      body: JSON.stringify({ action, cars: simCars, rate_hz: simRate }),
    });
    setSimMessage(
      `Simulator ${response.state}. ${response.cars} cars at ${response.rate_hz} Hz.`,
    );
    await load();
  } catch (e) {
    setSimMessage(
      e instanceof Error ? e.message : "Simulator request failed",
    );
  }
}

export async function readSessionResults(
  selected: string,
  setResults: (value: Row[]) => void,
  setResultsLoaded: (value: boolean) => void,
  setSimMessage: (value: string) => void,
) {
  if (!selected) return;
  try {
    setResults(asArray(await api(`/sessions/${selected}/results`)));
    setResultsLoaded(true);
  } catch (e) {
    setSimMessage(e instanceof Error ? e.message : "Results request failed");
  }
}
