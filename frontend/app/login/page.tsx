"use client";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/auth";
import { LoginArt } from "@/components/login-art";
import { NbButton } from "@/components/nb/button";
import { NbCard } from "@/components/nb/card";
import { NbField } from "@/components/nb/field";
import { NbInput } from "@/components/nb/input";
import { ArrowUpRight } from "lucide-react";
export default function Login() {
  const { login, user, ready } = useAuth(),
    router = useRouter(),
    [email, setEmail] = useState(""),
    [password, setPassword] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  useEffect(() => {
    if (ready && user) router.replace("/dashboard");
  }, [ready, router, user]);
  if (ready && user) {
    return null;
  }
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await login(email, password);
      router.replace("/dashboard");
    } catch (x) {
      setError(x instanceof Error ? x.message : "Sign in failed");
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="login-screen nb-login">
      <LoginArt />
      <NbCard tone="paper" shadow={12} className="login-main">
        <form className="login-form" onSubmit={submit}>
          <div className="eyebrow">AUTHENTICATED ACCESS</div>
          <h1>Sign in to ApexGrid</h1>
          <p>Use your assigned operations account to continue.</p>
          <NbField id="email" label="Email address">
            <NbInput
              type="email"
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={busy}
              placeholder="name@team.com"
              aria-describedby={error ? "form-error" : undefined}
            />
          </NbField>
          <NbField id="password" label="Password">
            <NbInput
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={busy}
              placeholder="Enter your password"
              aria-describedby={error ? "form-error" : undefined}
            />
          </NbField>
          {error && <div id="form-error" className="form-error" role="alert">{error}</div>}
          <NbButton
            type="submit"
            variant="primary"
            disabled={busy}
            aria-busy={busy || undefined}
            data-primary="true"
            className="login-submit"
          >
            {busy ? "Authenticating…" : "Sign in"}
            <ArrowUpRight size={16} />
          </NbButton>
          <small className="api-address">
            API · {process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}
            /api
          </small>
        </form>
        <div className="login-copyright">
          APEXGRID MOTORSPORT OPERATIONS · SECURE ACCESS
        </div>
      </NbCard>
    </div>
  );
}
