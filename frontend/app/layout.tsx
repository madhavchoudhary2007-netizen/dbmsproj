import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/components/auth";
import { Shell } from "@/components/shell";
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
    <html lang="en">
      <body>
        <AuthProvider>
          <Shell>{children}</Shell>
        </AuthProvider>
      </body>
    </html>
  );
}
