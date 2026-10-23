import type { Metadata } from "next";
import { Space_Grotesk, Space_Mono } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/components/auth";
import { Shell } from "@/components/shell";
const spaceGrotesk = Space_Grotesk({ subsets: ["latin"], weight: ["500", "700"], display: "swap", variable: "--font-space-grotesk" });
const spaceMono = Space_Mono({ subsets: ["latin"], weight: ["400", "700"], display: "swap", variable: "--font-space-mono" });
export const metadata: Metadata = {
  title: "ApexGrid | Race Operations",
  description: "Motorsport league and live race operations platform",
};
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${spaceGrotesk.variable} ${spaceMono.variable} bg-cream text-ink`}>
      <body className="font-sans">
        <a className="skip-link" href="#main-content">Skip to content</a>
        <AuthProvider>
          <Shell>{children}</Shell>
        </AuthProvider>
      </body>
    </html>
  );
}
