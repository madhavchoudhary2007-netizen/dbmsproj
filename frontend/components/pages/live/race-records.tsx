import type { Dispatch, SetStateAction } from "react";
import { Row } from "@/lib/api";
import { Button, DataTable } from "../../ui";

type RaceRecordsProps = {
  selectedLaps: Row[];
  recordsError: string;
  showAllLaps: boolean;
  setShowAllLaps: Dispatch<SetStateAction<boolean>>;
  visibleLaps: Row[];
  namedDrivers: Map<string, Row>;
  liveIncidents: Row[];
  livePitStops: Row[];
};

export function RaceRecords({
  selectedLaps,
  recordsError,
  showAllLaps,
  setShowAllLaps,
  visibleLaps,
  namedDrivers,
  liveIncidents,
  livePitStops,
}: RaceRecordsProps) {
  return (
    <>
      <div className="panel">
        <div className="panel-heading"><div><div className="eyebrow">RECORDED LAPS</div><h2>Driver lap and sector history</h2></div><span className="muted">{selectedLaps.length} completed driver laps</span></div>
        {recordsError && <div className="notice error-notice" role="status">Lap and race-control records could not be refreshed: {recordsError}. Retrying automatically in 5 seconds.</div>}
        {selectedLaps.length > 100 && <div className="inline-form"><span className="muted">Showing {showAllLaps ? "all" : "latest 100"} laps</span><Button kind="secondary" onClick={() => setShowAllLaps((value) => !value)}>{showAllLaps ? "Show latest 100" : "Show all laps"}</Button></div>}
        <DataTable rows={visibleLaps.map((lap) => ({
          driver_name: namedDrivers.get(String(lap.driver_id))?.full_name || lap.driver_id,
          lap: lap.lap,
          sector_1_ms: Array.isArray(lap.sector_ms) ? lap.sector_ms[0] : null,
          sector_2_ms: Array.isArray(lap.sector_ms) ? lap.sector_ms[1] : null,
          sector_3_ms: Array.isArray(lap.sector_ms) ? lap.sector_ms[2] : null,
          lap_time_ms: lap.lap_time_ms,
          position: lap.position,
        }))} columns={["driver_name","lap","sector_1_ms","sector_2_ms","sector_3_ms","lap_time_ms","position"]} />
      </div>
      <div className="panel">
        <div className="panel-heading"><div><div className="eyebrow">RACE CONTROL RECORDS</div><h2>Incidents and pit stops</h2></div></div>
        <h3>Incidents</h3>
        <DataTable rows={liveIncidents} columns={["driver_name","lap","description","state"]} />
        <h3>Pit stops</h3>
        <DataTable rows={livePitStops} columns={["driver_name","team_name","box_number","starts_at","ends_at","status"]} />
      </div>
    </>
  );
}
