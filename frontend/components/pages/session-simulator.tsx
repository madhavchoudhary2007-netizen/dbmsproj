import type { Row } from "@/lib/api";
import { Button } from "@/components/ui";

type SessionSimulatorProps = {
  drivers: Row[];
  current: Row | undefined;
  simCars: number;
  setSimCars: (n: number) => void;
  simRate: number;
  setSimRate: (n: number) => void;
  simulate: (action: string) => Promise<unknown>;
};

export function SessionSimulator({
  drivers,
  current,
  simCars,
  setSimCars,
  simRate,
  setSimRate,
  simulate,
}: SessionSimulatorProps) {
  return (
    <div className="sim-controls">
      <div>
        <div className="eyebrow">TELEMETRY SIMULATOR</div>
        <p className="muted">
          Start telemetry simulation for the selected session.
        </p>
      </div>
      <label>
        Cars
        <input
          type="number"
          min="1"
          max={Math.max(
            1,
            drivers.filter((d) => d.eligibility === "ACTIVE").length,
          )}
          value={simCars}
          onChange={(e) => setSimCars(+e.target.value)}
        />
        <small className="muted">
          {drivers.filter((d) => d.eligibility === "ACTIVE").length}{" "}
          eligible drivers available
        </small>
      </label>
      <label>
        Rate Hz
        <input
          type="number"
          min="1"
          value={simRate}
          onChange={(e) => setSimRate(+e.target.value)}
        />
      </label>
      <div className="action-row">
        {["start", "pause", "resume", "stop", "reset"].map((a) => (
          <Button
            key={a}
            disabled={
              (a === "start" && current?.state !== "ACTIVE") ||
              (a === "reset" && current?.state !== "PAUSED")
            }
            kind={a === "stop" ? "danger" : "secondary"}
            onClick={() => void simulate(a)}
          >
            {a}
          </Button>
        ))}
      </div>
    </div>
  );
}
