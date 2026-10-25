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
            ["speed_kph", "Speed · km/h", "#d9ff3f"],
            ["throttle_pct", "Throttle · %", "#8eafff"],
            ["brake_pct", "Brake · %", "#ff6b62"],
            ["lap_time_ms", "Lap time · ms", "#4fd4bd"],
            ["tire_wear_pct", "Tire wear · %", "#ffc45c"],
          ].map(([key, title, color]) => (
            <div className="panel chart-panel" key={key}>
              <div className="eyebrow">SELECTED DRIVER TELEMETRY</div>
              <h2>{title}</h2>
              <div className="chart">
                <ResponsiveContainer width="100%" height={190}>
                  <LineChart
                    data={chartPackets}
                    margin={{ top: 15, right: 8, bottom: 0, left: -16 }}
                  >
                    <CartesianGrid stroke="#29313a" strokeDasharray="3 4" />
                    <XAxis
                      dataKey="lap"
                      stroke="#77818b"
                      tick={{ fontSize: 9 }}
                      tickLine={false}
                    />
                    <YAxis
                      stroke="#77818b"
                      tick={{ fontSize: 9 }}
                      tickLine={false}
                    />
                    <Tooltip
                      contentStyle={{
                        background: "#11161c",
                        border: "1px solid #37414b",
                        fontSize: 10,
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey={key}
                      stroke={color}
                      dot={false}
                      connectNulls
                      strokeWidth={2}
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
                    <CartesianGrid stroke="#29313a" strokeDasharray="3 4" />
                    <XAxis
                      dataKey="lap"
                      stroke="#77818b"
                      tick={{ fontSize: 9 }}
                      tickLine={false}
                    />
                    <YAxis
                      stroke="#77818b"
                      tick={{ fontSize: 9 }}
                      tickLine={false}
                    />
                    <Tooltip
                      contentStyle={{
                        background: "#11161c",
                        border: "1px solid #37414b",
                        fontSize: 10,
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="temp_fl"
                      name="Front left"
                      stroke="#ff6b62"
                      dot={false}
                      connectNulls
                      strokeWidth={2}
                    />
                    <Line
                      type="monotone"
                      dataKey="temp_fr"
                      name="Front right"
                      stroke="#ffc45c"
                      dot={false}
                      connectNulls
                      strokeWidth={2}
                    />
                    <Line
                      type="monotone"
                      dataKey="temp_rl"
                      name="Rear left"
                      stroke="#8eafff"
                      dot={false}
                      connectNulls
                      strokeWidth={2}
                    />
                    <Line
                      type="monotone"
                      dataKey="temp_rr"
                      name="Rear right"
                      stroke="#4fd4bd"
                      dot={false}
                      connectNulls
                      strokeWidth={2}
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
