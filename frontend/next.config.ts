import type { NextConfig } from "next";

const rawApiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
let apiUrl: URL;
try {
  apiUrl = new URL(rawApiUrl);
  if (apiUrl.protocol !== "http:" && apiUrl.protocol !== "https:") {
    throw new Error("Unsupported API URL protocol");
  }
} catch {
  apiUrl = new URL("http://localhost:8000");
}

const apiOrigin = apiUrl.origin;
const websocketUrl = new URL(apiOrigin);
websocketUrl.protocol = apiUrl.protocol === "https:" ? "wss:" : "ws:";
const scriptSources = ["'self'", "'unsafe-inline'"];
// Next.js needs inline bootstrap scripts; unsafe-eval is limited to the development toolchain.
if (process.env.NODE_ENV === "development") scriptSources.push("'unsafe-eval'");

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          {
            key: "Content-Security-Policy",
            value: [
              "default-src 'self'",
              `connect-src 'self' ${apiOrigin} ${websocketUrl.origin}`,
              "font-src 'self'",
              "img-src 'self' data:",
              "style-src 'self' 'unsafe-inline'",
              `script-src ${scriptSources.join(" ")}`,
              "frame-ancestors 'none'",
              "object-src 'none'",
              "base-uri 'self'",
            ].join("; "),
          },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "X-Frame-Options", value: "DENY" },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=()",
          },
        ],
      },
    ];
  },
};
export default nextConfig;
