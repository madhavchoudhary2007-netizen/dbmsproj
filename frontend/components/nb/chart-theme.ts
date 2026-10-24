export const chartTheme = {
  line: {
    stroke: "#000000",
    strokeWidth: 3,
    dot: false,
  },
  secondary: {
    stroke: "#7CC4FF",
    strokeDasharray: "8 4",
  },
  tertiary: {
    stroke: "#FF6B6B",
    strokeDasharray: "2 4",
  },
  grid: {
    stroke: "#000000",
    strokeDasharray: "4 4",
    strokeOpacity: 0.25,
  },
  axis: {
    fontFamily: "var(--font-mono)",
    fontSize: 12,
    axisLine: {
      stroke: "#000000",
      strokeWidth: 2,
    },
    tickLine: {
      stroke: "#000000",
      strokeWidth: 2,
    },
  },
} as const;

export type ChartTheme = typeof chartTheme;
