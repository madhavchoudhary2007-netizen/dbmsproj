import { NbField } from "@/components/nb/field";
import { NbInput } from "@/components/nb/input";

type StewardSanctionsProps = {
  points: number;
  seconds: number;
  grid: number;
  setPoints: (n: number) => void;
  setSeconds: (n: number) => void;
  setGrid: (n: number) => void;
};

export function StewardSanctions({
  points,
  seconds,
  grid,
  setPoints,
  setSeconds,
  setGrid,
}: StewardSanctionsProps) {
  return (
    <>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <NbField id="penalty-points" label="Penalty points">
          <NbInput
            type="number"
            min={0}
            value={points}
            onChange={(e) => setPoints(+e.target.value)}
          />
        </NbField>
        <NbField id="time-penalty-seconds" label="Time penalty (seconds)">
          <NbInput
            type="number"
            min={0}
            value={seconds}
            onChange={(e) => setSeconds(+e.target.value)}
            disabled
            aria-describedby="sanction-limit-explanation"
          />
        </NbField>
        <NbField id="grid-places" label="Grid places">
          <NbInput
            type="number"
            min={0}
            value={grid}
            onChange={(e) => setGrid(+e.target.value)}
            disabled
            aria-describedby="sanction-limit-explanation"
          />
        </NbField>
      </div>
      <p id="sanction-limit-explanation" className="mt-4 max-w-prose font-sans text-[length:var(--fs-body)] leading-relaxed text-ink">
        Official timing/grid enforcement is unavailable. Use penalty points and notes for now.
      </p>
    </>
  );
}
