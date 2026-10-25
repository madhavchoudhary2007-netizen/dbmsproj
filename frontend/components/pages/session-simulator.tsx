import type { Row } from "@/lib/api";
import { NbButton } from "@/components/nb/button";
import { NbCard } from "@/components/nb/card";
import { NbField } from "@/components/nb/field";
import { NbInput } from "@/components/nb/input";

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
    <NbCard tone="cream" className="sim-controls space-y-4">
      <div>
        <div className="eyebrow font-bold text-ink">TELEMETRY SIMULATOR</div>
        <p className="font-sans text-[length:var(--fs-body)] text-ink">
          Start telemetry simulation for the selected session.
        </p>
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <NbField
          id="sim-cars"
          label="Cars"
          description={`${drivers.filter((d) => d.eligibility === "ACTIVE").length} eligible drivers available`}
        >
          <NbInput
            type="number"
            min="1"
            max={Math.max(1, drivers.filter((d) => d.eligibility === "ACTIVE").length)}
            value={simCars}
            onChange={(e) => setSimCars(+e.target.value)}
          />
        </NbField>
        <NbField id="sim-rate" label="Rate Hz">
          <NbInput
            type="number"
            min="1"
            value={simRate}
            onChange={(e) => setSimRate(+e.target.value)}
          />
        </NbField>
      </div>
      <div className="action-row flex flex-wrap gap-2">
        {["start", "pause", "resume", "stop", "reset"].map((a) => (
          <NbButton
            key={a}
            disabled={
              (a === "start" && current?.state !== "ACTIVE") ||
              (a === "reset" && current?.state !== "PAUSED")
            }
            variant={a === "stop" ? "danger" : "secondary"}
            onClick={() => void simulate(a)}
          >
            {a}
          </NbButton>
        ))}
      </div>
    </NbCard>
  );
}
