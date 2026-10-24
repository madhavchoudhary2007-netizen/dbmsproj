import { api, asArray, Row } from "./api";

export async function saveSessionResult(
  v: Row,
  selected: string,
  setBusy: (v: boolean) => void,
  setResults: (v: Row[]) => void,
  setResultsLoaded: (v: boolean) => void,
  setResultModal: (v: boolean) => void,
) {
  if (!selected) return;
  setBusy(true);
  try {
    const saved = await api(`/sessions/${selected}/results`, {
      method: "POST",
      body: JSON.stringify([
        {
          ...v,
          pole: v.pole === "true" || v.pole === true,
          fastest_lap: v.fastest_lap === "true" || v.fastest_lap === true,
          classified: v.classified === "true" || v.classified === true,
        },
      ]),
    });
    setResults(asArray(saved));
    setResultsLoaded(true);
    setResultModal(false);
  } finally {
    setBusy(false);
  }
}

export async function saveSession(
  v: Row,
  fields: readonly { name: string }[],
  editModal: boolean,
  selected: string,
  setBusy: (v: boolean) => void,
  setModal: (v: boolean) => void,
  setEditModal: (v: boolean) => void,
  load: () => Promise<void>,
) {
  setBusy(true);
  try {
    const payload = Object.fromEntries(
      fields
        .map(({ name }) => [name, v[name]] as const)
        .filter(([, value]) => value !== undefined),
    );
    await api(editModal && selected ? `/sessions/${selected}` : "/sessions", {
      method: editModal ? "PATCH" : "POST",
      body: JSON.stringify(payload),
    });
    setModal(false);
    setEditModal(false);
    await load();
  } finally {
    setBusy(false);
  }
}

export async function deleteSessionRecord(
  selected: string,
  setBusy: (v: boolean) => void,
  setSelected: (v: string) => void,
  setResults: (v: Row[]) => void,
  load: () => Promise<void>,
  setActionMsg: (v: string) => void,
) {
  if (!selected) return;
  setBusy(true);
  try {
    await api(`/sessions/${selected}`, { method: "DELETE" });
    setSelected("");
    setResults([]);
    await load();
  } catch (e) {
    setActionMsg(e instanceof Error ? e.message : "Unable to delete session");
  } finally {
    setBusy(false);
  }
}
