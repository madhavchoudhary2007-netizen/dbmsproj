"use client";
import { createContext, useContext, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, User } from "@/lib/api";
type Auth = {
  user: User | null;
  ready: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
};
const Ctx = createContext<Auth>({
  user: null,
  ready: false,
  login: async () => {},
  logout: async () => {},
});
function clearLegacyToken() {
  try {
    window.localStorage.removeItem("apexgrid_token");
  } catch {}
}
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null),
    [ready, setReady] = useState(false);
  useEffect(() => {
    clearLegacyToken();
    api<User>("/auth/me")
      .then(setUser)
      .catch(() => {
        setUser(null);
      })
      .finally(() => setReady(true));
  }, []);
  const login = async (email: string, password: string) => {
    const d = await api<{ user: User }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    clearLegacyToken();
    setUser(d.user);
  };
  const logout = async () => {
    try {
      await api<void>("/auth/logout", { method: "POST" });
      clearLegacyToken();
      setUser(null);
      router.push("/login");
    } catch (error) {
      const reason = error instanceof Error ? error.message : "request failed";
      window.alert(`Could not sign out: ${reason}. Please try again.`);
    }
  };
  return (
    <Ctx.Provider value={{ user, ready, login, logout }}>
      {children}
    </Ctx.Provider>
  );
}
export const useAuth = () => useContext(Ctx);
