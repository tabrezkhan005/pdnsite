"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import api from "@/lib/api";

type User = {
  id: string;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  role: "ADMIN" | "STAFF" | "STUDENT" | "GUARDIAN";
};

type AuthContextType = {
  user: User | null;
  isLoading: boolean;
  login: (phone: string, otp: string) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchUser = async () => {
    try {
      const { data } = await api.get("/v1/auth/me/");
      setUser(data);
    } catch {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchUser();
  }, []);

  const login = async (phone: string, otp: string) => {
    // Ensure CSRF token is set before login
    await api.get("/v1/auth/csrf/");
    const { data } = await api.post("/v1/auth/verify-otp/", { phone, otp });
    setUser(data);
  };

  const logout = async () => {
    await api.post("/v1/auth/logout/");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
