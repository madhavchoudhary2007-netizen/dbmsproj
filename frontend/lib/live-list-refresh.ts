import type { Dispatch, MutableRefObject, SetStateAction } from "react";
import { asArray, listAll, type Row } from "@/lib/api";
import type { LiveErrorSource } from "@/lib/live-stream-types";

export async function refreshLiveLists(
  listRequest: MutableRefObject<number>,
  setSessions: Dispatch<SetStateAction<Row[]>>,
  setDemoRaces: Dispatch<SetStateAction<Row[]>>,
  clearError: (source?: LiveErrorSource) => void,
): Promise<{ sessionRows: Row[]; raceRows: Row[]; current: boolean }> {
  const request = ++listRequest.current;
  const [s, r] = await Promise.all([
    listAll("/sessions"),
    listAll("/demo-races"),
  ]);
  const sessionRows = asArray(s);
  const raceRows = asArray(r);
  if (request === listRequest.current) {
    setSessions(sessionRows);
    setDemoRaces(raceRows);
    clearError("lists");
  }
  return { sessionRows, raceRows, current: request === listRequest.current };
}
