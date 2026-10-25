import { api, asArray, API_BASE, type Row } from "./api";
import { belongsToLiveRun } from "./live-timing-data";
import type { LiveStreamContext } from "./live-stream-types";

export function startLiveStream(context: LiveStreamContext): (() => void) | undefined {
  const {
    session, clearError, reportError, setStatus,
    setSessionDrivers, setPackets, setCompletedLaps,
    setLiveIncidents, setLivePitStops, setTiming, setSnapshot,
  } = context;

  if (!session) { setStatus("Choose an active session"); return; }
  setStatus("Connecting · live stream");
  setSessionDrivers([]);
  setPackets([]);
  setTiming({ cars: [], safety_car: false });
  setSnapshot(null);
  let alive = true,
    ws: WebSocket | undefined,
    timer: ReturnType<typeof setTimeout> | undefined,
    attempt = 0,
    startedAt: string | undefined,
    refreshRequest = 0,
    sessionState = "",
    streamConnected = false;
  const updateStreamStatus = () => {
    if (sessionState === "COMPLETED") setStatus("Completed · final timing");
    else if (sessionState === "PAUSED") setStatus(streamConnected ? "Paused · stream connected" : "Paused · reconnecting");
    else if (sessionState === "SCHEDULED") setStatus("Scheduled · waiting to start");
    else if (sessionState === "CANCELLED") setStatus("Cancelled · stream stopped");
    else setStatus(streamConnected ? "Connected · live stream" : "Connecting · live stream");
  };
  const belongsToCurrentRun = (packet: Row) =>
    belongsToLiveRun(packet, session, startedAt);
  const refresh = async () => {
    const request = ++refreshRequest;
    try {
      const s = await api<{ session?: Row; drivers?: Row[]; packets?: Row[] } & Record<string, unknown>>(`/sessions/${session}/live`);
      if (!alive || request !== refreshRequest) return;
      if (alive) {
        const sessionData = s.session || s;
        sessionState = String(sessionData.state || sessionState);
        setSnapshot(sessionData);
        setSessionDrivers(asArray(s.drivers));
        startedAt = (sessionData.started_at as string | undefined) || startedAt;
        setTiming((prev) => ({
          ...prev,
          safety_car: (s.session?.safety_car as boolean | undefined) ?? prev.safety_car,
        }));
        if (Array.isArray(s.packets))
          setPackets(s.packets.filter(belongsToCurrentRun));
        clearError("snapshot");
        updateStreamStatus();
        if (sessionState === "COMPLETED" || sessionState === "CANCELLED")
          ws?.close();
      }
    } catch (e) {
      if (alive && request === refreshRequest)
        reportError("snapshot", e instanceof Error ? e.message : "Unable to fetch snapshot");
    }
  };
  const connect = () => {
    if (!alive) return;
    const wsBase = API_BASE.replace(/^http/, "ws");
    ws = new WebSocket(`${wsBase}/api/ws/sessions/${session}`);
    ws.onopen = () => {
      if (!alive) return;
      attempt = 0;
      streamConnected = true;
      updateStreamStatus();
    };
    ws.onmessage = (e) => {
      if (!alive) return;
      try {
        const msg = JSON.parse(e.data);
        if (
          msg.type === "session.state" &&
          String(msg.session_id || session) === session
        ) {
          const stateData = msg.data || {};
          const nextStartedAt = stateData.started_at || msg.started_at;
          const startsNewRun = Boolean(nextStartedAt && startedAt && String(nextStartedAt) !== startedAt);
          const resetsRun = stateData.state === "PAUSED" &&
            Object.prototype.hasOwnProperty.call(stateData, "started_at") &&
            !stateData.started_at && Boolean(startedAt);
          if (startsNewRun || resetsRun) {
            setPackets([]);
            setCompletedLaps([]);
            setLiveIncidents([]);
            setLivePitStops([]);
            setTiming({ cars: [], safety_car: false });
            if (resetsRun) startedAt = undefined;
          }
          if (nextStartedAt) startedAt = String(nextStartedAt);
          sessionState = String(stateData.state || sessionState);
          updateStreamStatus();
          if (sessionState === "CANCELLED") ws?.close();
          void refresh();
        }
        setSnapshot((prev) => ({
          ...prev,
          ...(msg.data || {}),
          last_event: msg,
        }));
        if (
          msg.type === "timing.update" &&
          String(msg.session_id || session) === session &&
          !Array.isArray(msg.data)
        ) {
          setTiming(msg.data || { cars: [] });
        }
        if (
          msg.type === "telemetry.sample" &&
          belongsToCurrentRun(msg.data || {})
        )
          setPackets((p) => [...p, msg.data].slice(-100));
      } catch {}
    };
    ws.onerror = () => {
      if (!alive) return;
      streamConnected = false;
      if (sessionState === "COMPLETED" || sessionState === "PAUSED" || sessionState === "SCHEDULED" || sessionState === "CANCELLED") updateStreamStatus();
      else setStatus("Stream interrupted · reconnecting");
    };
    ws.onclose = () => {
      if (!alive) return;
      streamConnected = false;
      if (sessionState === "COMPLETED" || sessionState === "PAUSED" || sessionState === "SCHEDULED" || sessionState === "CANCELLED") updateStreamStatus();
      else setStatus("Disconnected · reconnecting");
      if (sessionState === "COMPLETED" || sessionState === "CANCELLED") return;
      const delay = Math.min(1000 * 2 ** attempt++, 15000);
      timer = setTimeout(() => {
        void refresh();
        connect();
      }, delay);
    };
  };
  void refresh();
  connect();
  return () => {
    alive = false;
    clearTimeout(timer);
    ws?.close();
  };
}
