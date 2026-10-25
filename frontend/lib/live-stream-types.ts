import type { Dispatch, SetStateAction } from "react";
import type { Row } from "./api";

export type LiveTimingState = {
  cars?: Row[];
  safety_car?: boolean;
  [key: string]: unknown;
};

export type LiveErrorSource = "lists" | "snapshot" | "demo";

export type LiveStreamContext = {
  session: string;
  clearError: (source?: LiveErrorSource) => void;
  reportError: (source: LiveErrorSource, message: string) => void;
  setStatus: Dispatch<SetStateAction<string>>;
  setSessionDrivers: Dispatch<SetStateAction<Row[]>>;
  setPackets: Dispatch<SetStateAction<Row[]>>;
  setCompletedLaps: Dispatch<SetStateAction<Row[]>>;
  setLiveIncidents: Dispatch<SetStateAction<Row[]>>;
  setLivePitStops: Dispatch<SetStateAction<Row[]>>;
  setTiming: Dispatch<SetStateAction<LiveTimingState>>;
  setSnapshot: Dispatch<SetStateAction<Record<string, unknown> | null>>;
};
