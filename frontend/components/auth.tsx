"use client";
import { createContext, useContext, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, User } from "@/lib/api";
type Auth = {
  user: User | null;
  ready: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
};
const Ctx = createContext<Auth>({
  user: null,
  ready: false,
  login: async () => {},
  logout: () => {},
});
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null),
    [ready, setReady] = useState(false);
  useEffect(() => {
    if (!localStorage.getItem("apexgrid_token")) {
      setReady(true);
      return;
    }
    api<User>("/auth/me")
      .then(setUser)
      .catch(() => {
        localStorage.removeItem("apexgrid_token");
        setUser(null);
      })
      .finally(() => setReady(true));
  }, []);
  const login = async (email: string, password: string) => {
    const d = await api<{ access_token: string; user: User }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    localStorage.setItem("apexgrid_token", d.access_token);
    setUser(d.user);
  };
  const logout = () => {
    localStorage.removeItem("apexgrid_token");
    setUser(null);
    router.push("/login");
  };
  return (
    <Ctx.Provider value={{ user, ready, login, logout }}>
      {children}
    </Ctx.Provider>
  );
}
export const useAuth = () => useContext(Ctx);
