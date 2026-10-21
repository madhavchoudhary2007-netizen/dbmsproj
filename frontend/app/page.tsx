"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/auth";

export default function Home() {
  const router = useRouter();
  const { user, ready } = useAuth();

  useEffect(() => {
    if (ready) router.replace(user ? "/dashboard" : "/login");
  }, [ready, router, user]);

  return (
    <div className="loading-screen">
      APEXGRID{" "}
      <span>{ready ? "Opening operations…" : "Checking session…"}</span>
    </div>
  );
}
