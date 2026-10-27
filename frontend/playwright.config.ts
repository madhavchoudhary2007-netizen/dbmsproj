import { defineConfig, devices } from "@playwright/test";

const port = process.env.PLAYWRIGHT_PORT ?? "3100";
const mode = process.env.PLAYWRIGHT_MODE ?? "production";
if (mode !== "production" && mode !== "guide" && mode !== "real-stack") {
  throw new Error(`Unsupported PLAYWRIGHT_MODE: ${mode}`);
}
const isGuideMode = mode === "guide";
function validateRealStackApiUrl(value: string | undefined): string {
  if (!value) throw new Error("PLAYWRIGHT_REAL_STACK_API_URL is required in real-stack mode");
  let apiUrl: URL;
  try {
    apiUrl = new URL(value);
  } catch {
    throw new Error("PLAYWRIGHT_REAL_STACK_API_URL must be a disposable loopback URL on port 18000");
  }
  if (
    apiUrl.protocol !== "http:" ||
    !["localhost", "127.0.0.1", "[::1]"].includes(apiUrl.hostname) ||
    apiUrl.port !== "18000" ||
    !["", "/"].includes(apiUrl.pathname) ||
    apiUrl.search !== "" ||
    apiUrl.hash !== "" ||
    apiUrl.username !== "" ||
    apiUrl.password !== ""
  ) {
    throw new Error("PLAYWRIGHT_REAL_STACK_API_URL must be a disposable loopback URL on port 18000");
  }
  return apiUrl.origin;
}
const realStackApiUrl = mode === "real-stack"
  ? validateRealStackApiUrl(process.env.PLAYWRIGHT_REAL_STACK_API_URL)
  : undefined;

const standardViewports = [
  { name: "mobile-320", use: { viewport: { width: 320, height: 568 }, hasTouch: true, isMobile: true } },
  { name: "mobile-375", use: { ...devices["iPhone 13"], browserName: "chromium" as const, viewport: { width: 375, height: 812 } } },
  { name: "tablet-768", use: { viewport: { width: 768, height: 1024 }, hasTouch: true } },
  { name: "desktop-1440", use: { viewport: { width: 1440, height: 900 } } },
  { name: "ultrawide-32x9", use: { viewport: { width: 5120, height: 1440 } } },
];

const guideSpecs = ["**/nb-primitives.spec.ts", "**/motion-hooks.spec.ts"];
const projects = isGuideMode
  ? standardViewports.map(({ name, use }) => ({
      name: `guide-${name}`,
      testMatch: guideSpecs,
      use,
    }))
  : mode === "production"
    ? [
      ...standardViewports.map(({ name, use }) => ({
        name,
        testIgnore: ["**/real-stack.spec.ts", ...guideSpecs],
        use,
      })),
    ]
    : [
      { name: "real-stack", testMatch: "**/real-stack.spec.ts", use: { viewport: { width: 1440, height: 900 } } },
      { name: "real-stack-mobile-375", testMatch: "**/real-stack.spec.ts", use: { ...devices["iPhone 13"], browserName: "chromium" as const, viewport: { width: 375, height: 812 } } },
    ];

export default defineConfig({
  testDir: "./e2e",
  testMatch: "**/*.spec.ts",
  use: { baseURL: `http://localhost:${port}`, trace: "retain-on-failure" },
  webServer: {
    command: isGuideMode
      ? `npm run dev -- --hostname 127.0.0.1 --port ${port}`
      : realStackApiUrl
        ? `NEXT_PUBLIC_API_URL=${realStackApiUrl} npm run build && NEXT_PUBLIC_API_URL=${realStackApiUrl} npm run start -- --hostname 127.0.0.1 --port ${port}`
        : `npm run start -- --hostname 127.0.0.1 --port ${port}`,
    url: `http://127.0.0.1:${port}`,
    reuseExistingServer: realStackApiUrl ? false : !process.env.CI,
    ...(realStackApiUrl ? { env: { NEXT_PUBLIC_API_URL: realStackApiUrl } } : {}),
  },
  projects,
});
