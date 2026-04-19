import React, { useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { ShieldCheck, SquaresFour, Upload, ClockClockwise, Gear, UsersThree, ClipboardText, SignOut, Lifebuoy } from "@phosphor-icons/react";
import { toast } from "sonner";

const nav = [
  { to: "/app/dashboard", label: "Dashboard", icon: SquaresFour, testid: "nav-dashboard" },
  { to: "/app/wizard", label: "Upload Records", icon: Upload, testid: "nav-upload" },
  { to: "/app/history", label: "History (24hr)", icon: ClockClockwise, testid: "nav-history" },
  { to: "/app/settings", label: "Settings", icon: Gear, testid: "nav-settings" },
  { to: "/app/help", label: "Help", icon: Lifebuoy, testid: "nav-help" },
];

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [warn, setWarn] = useState(false);
  const [count, setCount] = useState(60);

  useEffect(() => {
    const onWarn = () => { setWarn(true); setCount(60); };
    const onReset = () => setWarn(false);
    const onLogout = () => { toast.error("You were logged out due to 5 minutes of inactivity."); navigate("/login"); };
    window.addEventListener("chc:idle-warn", onWarn);
    window.addEventListener("chc:idle-reset", onReset);
    window.addEventListener("chc:idle-logout", onLogout);
    return () => {
      window.removeEventListener("chc:idle-warn", onWarn);
      window.removeEventListener("chc:idle-reset", onReset);
      window.removeEventListener("chc:idle-logout", onLogout);
    };
  }, [navigate]);

  useEffect(() => {
    if (!warn) return;
    const t = setInterval(() => setCount((c) => Math.max(0, c - 1)), 1000);
    return () => clearInterval(t);
  }, [warn]);

  const isAdmin = ["admin", "provider"].includes(user?.role);
  const adminLinks = isAdmin ? [
    { to: "/app/admin/pending", label: "Pending Approvals", icon: UsersThree, testid: "nav-admin-pending" },
    { to: "/app/admin/users", label: "All Users", icon: UsersThree, testid: "nav-admin-users" },
    { to: "/app/admin/audit", label: "Audit Log", icon: ClipboardText, testid: "nav-admin-audit" },
  ] : [];

  return (
    <div className="flex min-h-screen bg-background">
      {/* Sidebar */}
      <aside className="hidden md:flex w-64 flex-col border-r border-border bg-white" data-testid="sidebar">
        <div className="flex h-16 items-center gap-2 border-b border-border px-5">
          <div className="h-8 w-8 rounded-sm bg-chc-navy flex items-center justify-center">
            <ShieldCheck className="text-white" size={20} weight="fill" />
          </div>
          <div>
            <p className="text-sm font-semibold text-chc-ink leading-none">CHC Pro AI</p>
            <p className="text-[10px] uppercase tracking-widest text-chc-slate">HIPAA-aware</p>
          </div>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          <p className="px-3 text-[10px] font-semibold uppercase tracking-widest text-slate-400 mb-2">Workflow</p>
          {nav.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              data-testid={n.testid}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors ${
                  isActive ? "bg-chc-navy text-white font-medium" : "text-slate-600 hover:bg-slate-50 hover:text-chc-navy"
                }`
              }
            >
              <n.icon size={18} weight={n.to === window.location.pathname ? "fill" : "regular"} />
              {n.label}
            </NavLink>
          ))}
          {isAdmin && (
            <>
              <p className="mt-6 px-3 text-[10px] font-semibold uppercase tracking-widest text-slate-400 mb-2">Admin</p>
              {adminLinks.map((n) => (
                <NavLink
                  key={n.to}
                  to={n.to}
                  data-testid={n.testid}
                  className={({ isActive }) =>
                    `flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors ${
                      isActive ? "bg-chc-navy text-white font-medium" : "text-slate-600 hover:bg-slate-50 hover:text-chc-navy"
                    }`
                  }
                >
                  <n.icon size={18} />
                  {n.label}
                </NavLink>
              ))}
            </>
          )}
        </nav>
        <div className="border-t border-border p-4">
          <div className="mb-3 rounded-md bg-chc-mist p-3">
            <p className="text-[10px] uppercase tracking-widest text-chc-slate">Session</p>
            <p className="font-mono text-xs text-chc-ink truncate">{user?.email}</p>
            <p className="text-[10px] text-chc-slate">Role: <span className="font-mono">{user?.role}</span></p>
          </div>
          <button
            onClick={() => { logout(); navigate("/login"); }}
            data-testid="logout-btn"
            className="w-full flex items-center justify-center gap-2 rounded-md border border-border bg-white px-3 py-2 text-sm font-medium text-chc-navy hover:bg-chc-mist transition-colors"
          >
            <SignOut size={16} /> Sign out
          </button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col">
        <header className="h-16 bg-white border-b border-border flex items-center justify-between px-6" data-testid="topbar">
          <div className="flex items-center gap-3">
            <div className="md:hidden flex items-center gap-2">
              <div className="h-8 w-8 rounded-sm bg-chc-navy flex items-center justify-center">
                <ShieldCheck className="text-white" size={18} weight="fill" />
              </div>
              <p className="font-semibold text-chc-ink">CHC Pro AI</p>
            </div>
            <div className="hidden md:flex items-center gap-2 text-xs text-chc-slate">
              <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-emerald-700">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" /> Secure session
              </span>
              <span className="font-mono">24h auto-purge enabled</span>
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm font-medium text-chc-ink" data-testid="topbar-name">{user?.first_name} {user?.last_name}</p>
            <p className="text-[11px] text-chc-slate">{user?.facility_name}</p>
          </div>
        </header>
        <main className="flex-1 p-6 md:p-8">
          <Outlet />
        </main>
      </div>

      {warn && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-chc-ink/40" data-testid="idle-warning">
          <div className="w-full max-w-md rounded-md border border-border bg-white p-6 shadow-xl">
            <p className="text-[10px] uppercase tracking-widest text-chc-slate">Security</p>
            <h3 className="mt-1 text-xl font-semibold text-chc-ink">Still there?</h3>
            <p className="mt-2 text-sm text-chc-slate">For your protection, you'll be signed out in <span className="font-mono text-chc-navy">{count}s</span> due to inactivity. Move your mouse or press any key to stay signed in.</p>
            <div className="mt-5 h-2 w-full rounded-full bg-slate-100 overflow-hidden">
              <div className="h-full bg-chc-cyan transition-all" style={{ width: `${(count / 60) * 100}%` }} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}