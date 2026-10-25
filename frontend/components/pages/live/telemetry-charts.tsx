import type { Row } from "@/lib/api";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { NbActiveDot, NbChartTooltip } from "@/components/nb/chart-frame";
import { chartTheme } from "@/components/nb/chart-theme";

export function TelemetryCharts({
  driver,
  shown,
  chartPackets,
  hasTireTemperatures,
}: {
  driver: string;
  shown: Row[];
  chartPackets: Row[];
  hasTireTemperatures: boolean;
}) {
  return (
    <>
      {driver && shown.length > 0 && (
        <div className="telemetry-charts">
          {[
            ["speed_kph", "Speed · km/h"],
            ["throttle_pct", "Throttle · %"],
            ["brake_pct", "Brake · %"],
            ["lap_time_ms", "Lap time · ms"],
            ["tire_wear_pct", "Tire wear · %"],
          ].map(([key, title]) => (
            <div className="panel chart-panel" key={key}>
              <div className="eyebrow">SELECTED DRIVER TELEMETRY</div>
              <h2>{title}</h2>
              <div className="chart">
                <ResponsiveContainer width="100%" height={190}>
                  <LineChart
                    data={chartPackets}
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
              </div>
            </div>
          ))}
          {hasTireTemperatures && (
            <div className="panel chart-panel">
              <div className="eyebrow">SELECTED DRIVER TELEMETRY</div>
              <h2>Tire temperatures · °C</h2>
              <div className="chart">
                <ResponsiveContainer width="100%" height={190}>
                  <LineChart
                    data={chartPackets}
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
              </div>
            </div>
          )}
        </div>
      )}
    </>
  );
}
