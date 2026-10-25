import type { Row } from "@/lib/api";
import type { ViewState } from "@/lib/data-state";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { NbActiveDot, NbChartFrame, NbChartTooltip } from "@/components/nb/chart-frame";
import { chartTheme } from "@/components/nb/chart-theme";

export function TelemetryCharts({
  driver,
  chartPackets,
  hasTireTemperatures,
  loading,
  error,
  retry,
}: {
  driver: string;
  shown: Row[];
  chartPackets: Row[];
  hasTireTemperatures: boolean;
  loading: boolean;
  error: string;
  retry: () => void;
}) {
  const state: ViewState<Row[]> = chartPackets.length
    ? error
      ? { status: "partial", data: chartPackets, filter: { label: "Retry snapshot", clear: retry }, totalCount: chartPackets.length }
      : { status: "populated", data: chartPackets }
    : loading
      ? { status: "loading" }
      : error
        ? { status: "error", error: { message: error, retryable: true }, retry }
        : { status: "empty", reason: "no-data" };
  return (
    <>
      {driver && (
        <div className="telemetry-charts min-w-0">
          {[
            ["speed_kph", "Speed · km/h"],
            ["throttle_pct", "Throttle · %"],
            ["brake_pct", "Brake · %"],
            ["lap_time_ms", "Lap time · ms"],
            ["tire_wear_pct", "Tire wear · %"],
          ].map(([key, title]) => (
            <NbChartFrame key={key} title={title} state={state} empty="Waiting for timing and telemetry packets from this session." description="SELECTED DRIVER TELEMETRY" sourceMessage={error || undefined} className="min-w-0">
              {(data) => <div className="chart min-w-0">
                <ResponsiveContainer width="100%" height={190}>
                  <LineChart
                    data={data}
                    margin={{ top: 15, right: 8, bottom: 0, left: -16 }}
                  >
                    <CartesianGrid {...chartTheme.grid} />
                    <XAxis
                      dataKey="lap"
                      stroke={chartTheme.line.stroke}
                      axisLine={chartTheme.axis.axisLine}
                      tickLine={chartTheme.axis.tickLine}
                      tick={{
                        fontFamily: chartTheme.axis.fontFamily,
                        fontSize: chartTheme.axis.fontSize,
                      }}
                    />
                    <YAxis
                      stroke={chartTheme.line.stroke}
                      axisLine={chartTheme.axis.axisLine}
                      tickLine={chartTheme.axis.tickLine}
                      tick={{
                        fontFamily: chartTheme.axis.fontFamily,
                        fontSize: chartTheme.axis.fontSize,
                      }}
                    />
                    <Tooltip content={<NbChartTooltip />} />
                    <Line
                      type="monotone"
                      dataKey={key}
                      {...chartTheme.line}
                      activeDot={<NbActiveDot />}
                      connectNulls
                      isAnimationActive={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>}
            </NbChartFrame>
          ))}
          {hasTireTemperatures && (
            <NbChartFrame title="Tire temperatures · °C" state={state} empty="Waiting for timing and telemetry packets from this session." description="SELECTED DRIVER TELEMETRY" sourceMessage={error || undefined} className="min-w-0">
              {(data) => <div className="chart min-w-0">
                <dl className="mb-4 grid min-w-0 grid-cols-2 gap-3 sm:grid-cols-4">
                  {(["temp_fl", "temp_fr", "temp_rl", "temp_rr"] as const).map((key, index) => {
                    const value = data[data.length - 1]?.[key];
                    const label = ["Front left", "Front right", "Rear left", "Rear right"][index];
                    return <div className="min-w-0 border-4 border-ink p-3" key={key}>
                      <dt className="text-[length:var(--fs-label)] font-bold">{label}</dt>
                      <dd className="font-mono tabular-nums">{typeof value === "number" && Number.isFinite(value) ? value : "—"}</dd>
                    </div>;
                  })}
                </dl>
                <ResponsiveContainer width="100%" height={190}>
                  <LineChart
                    data={data}
                    margin={{ top: 15, right: 8, bottom: 0, left: -16 }}
                  >
                    <CartesianGrid {...chartTheme.grid} />
                    <XAxis
                      dataKey="lap"
                      stroke={chartTheme.line.stroke}
                      axisLine={chartTheme.axis.axisLine}
                      tickLine={chartTheme.axis.tickLine}
                      tick={{
                        fontFamily: chartTheme.axis.fontFamily,
                        fontSize: chartTheme.axis.fontSize,
                      }}
                    />
                    <YAxis
                      stroke={chartTheme.line.stroke}
                      axisLine={chartTheme.axis.axisLine}
                      tickLine={chartTheme.axis.tickLine}
                      tick={{
                        fontFamily: chartTheme.axis.fontFamily,
                        fontSize: chartTheme.axis.fontSize,
                      }}
                    />
                    <Tooltip content={<NbChartTooltip />} />
                    <Line
                      type="monotone"
                      dataKey="temp_fl"
                      name="Front left"
                      {...chartTheme.line}
                      activeDot={<NbActiveDot />}
                      connectNulls
                      isAnimationActive={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="temp_fr"
                      name="Front right"
                      {...chartTheme.line}
                      {...chartTheme.secondary}
                      activeDot={<NbActiveDot />}
                      connectNulls
                      isAnimationActive={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="temp_rl"
                      name="Rear left"
                      {...chartTheme.line}
                      {...chartTheme.tertiary}
                      activeDot={<NbActiveDot />}
                      connectNulls
                      isAnimationActive={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="temp_rr"
                      name="Rear right"
                      stroke={chartTheme.line.stroke}
                      strokeDasharray="1 3"
                      strokeWidth={chartTheme.line.strokeWidth}
                      dot={chartTheme.line.dot}
                      activeDot={<NbActiveDot />}
                      connectNulls
                      isAnimationActive={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>}
            </NbChartFrame>
          )}
        </div>
      )}
    </>
  );
}
