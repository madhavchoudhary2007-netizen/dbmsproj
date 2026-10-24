"use client";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/auth";
import { LoginArt } from "@/components/login-art";
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
      <div className="login-main">
        <form className="login-form" onSubmit={submit}>
          <div className="eyebrow">AUTHENTICATED ACCESS</div>
          <h1>Sign in to ApexGrid</h1>
          <p>Use your assigned operations account to continue.</p>
          <label>
            Email address
            <input
              type="email"
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="name@team.com"
            />
          </label>
          <label>
            Password
            <input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="Enter your password"
            />
          </label>
          {error && <div className="form-error">{error}</div>}
          <button disabled={busy} data-primary="true" className="button primary login-submit">
            {busy ? "Authenticating…" : "Sign in"}
            <ArrowUpRight size={16} />
          </button>
          <small className="api-address">
            API · {process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}
            /api
          </small>
        </form>
        <div className="login-copyright">
          APEXGRID MOTORSPORT OPERATIONS · SECURE ACCESS
        </div>
      </div>
    </div>
  );
}
