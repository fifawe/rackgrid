import React, { createContext, useContext, useMemo, useState } from "react";
import { login as loginRequest } from "../api/auth";

interface DecodedToken {
  sub: string;
  role: "Viewer" | "Editor" | "Admin";
  exp: number;
}

function decodeJwt(token: string): DecodedToken | null {
  try {
    const payload = token.split(".")[1];
    return JSON.parse(atob(payload.replace(/-/g, "+").replace(/_/g, "/")));
  } catch {
    return null;
  }
}

interface AuthContextValue {
  username: string | null;
  role: string | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  hasRole: (minimum: "Viewer" | "Editor" | "Admin") => boolean;
}

const ROLE_RANK: Record<string, number> = { Viewer: 0, Editor: 1, Admin: 2 };

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const existingToken = localStorage.getItem("access_token");
  const existingDecoded = existingToken ? decodeJwt(existingToken) : null;

  const [username, setUsername] = useState<string | null>(existingDecoded?.sub ?? null);
  const [role, setRole] = useState<string | null>(existingDecoded?.role ?? null);

  const value = useMemo<AuthContextValue>(
    () => ({
      username,
      role,
      isAuthenticated: Boolean(username),
      login: async (u: string, p: string) => {
        const token = await loginRequest(u, p);
        localStorage.setItem("access_token", token);
        const decoded = decodeJwt(token);
        setUsername(decoded?.sub ?? u);
        setRole(decoded?.role ?? null);
      },
      logout: () => {
        localStorage.removeItem("access_token");
        setUsername(null);
        setRole(null);
      },
      hasRole: (minimum) => {
        if (!role) return false;
        return ROLE_RANK[role] >= ROLE_RANK[minimum];
      },
    }),
    [username, role]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
