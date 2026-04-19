import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { api } from "@/lib/http";

const AuthCtx = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadMe = useCallback(async () => {
    const token = localStorage.getItem("chc_access_token");
    if (!token) {
      setUser(false);
      setLoading(false);
      return;
    }
    try {
      const { data } = await api.get("/auth/me");
      setUser(data);
    } catch (e) {
      localStorage.removeItem("chc_access_token");
      localStorage.removeItem("chc_refresh_token");
      setUser(false);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadMe(); }, [loadMe]);

  // 5-minute idle logout
  useEffect(() => {
    if (!user) return;
    let timer;
    let warnTimer;
    const IDLE_MS = 5 * 60 * 1000;   // 5 min
    const WARN_MS = IDLE_MS - 60 * 1000; // warn at 4 min

    const reset = () => {
      window.dispatchEvent(new CustomEvent("chc:idle-reset"));
      clearTimeout(timer); clearTimeout(warnTimer);
      warnTimer = setTimeout(() => window.dispatchEvent(new CustomEvent("chc:idle-warn")), WARN_MS);
      timer = setTimeout(() => {
        window.dispatchEvent(new CustomEvent("chc:idle-logout"));
        doLogout();
      }, IDLE_MS);
    };
    const events = ["mousemove", "keydown", "click", "scroll", "touchstart"];
    events.forEach((e) => window.addEventListener(e, reset));
    reset();
    return () => {
      events.forEach((e) => window.removeEventListener(e, reset));
      clearTimeout(timer); clearTimeout(warnTimer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const storeTokens = (access, refresh) => {
    localStorage.setItem("chc_access_token", access);
    if (refresh) localStorage.setItem("chc_refresh_token", refresh);
  };

  const doLogout = async () => {
    try { await api.post("/auth/logout"); } catch {}
    localStorage.removeItem("chc_access_token");
    localStorage.removeItem("chc_refresh_token");
    setUser(false);
  };

  return (
    <AuthCtx.Provider value={{ user, setUser, loading, storeTokens, logout: doLogout, reload: loadMe }}>
      {children}
    </AuthCtx.Provider>
  );
}

export function useAuth() {
  return useContext(AuthCtx);
}
