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
      <div className="form-grid three">
        <label>
          Penalty points
          <input
            type="number"
            min="0"
            value={points}
            onChange={(e) => setPoints(+e.target.value)}
          />
        </label>
        <label>
          Time penalty (seconds)
          <input
            type="number"
            min="0"
            value={seconds}
            onChange={(e) => setSeconds(+e.target.value)}
            disabled
            aria-describedby="sanction-limit-explanation"
          />
        </label>
        <label>
          Grid places
          <input
            type="number"
            min="0"
            value={grid}
            onChange={(e) => setGrid(+e.target.value)}
            disabled
            aria-describedby="sanction-limit-explanation"
          />
        </label>
      </div>
      <p id="sanction-limit-explanation" className="muted">
        Official timing/grid enforcement is unavailable. Use penalty points and notes for now.
      </p>
    </>
  );
}
