import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { api } from "@/lib/http";
import { ArrowRight, Upload, ClockClockwise, ShieldCheck } from "@phosphor-icons/react";

export default function Dashboard() {
  const { user } = useAuth();
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const { data } = await api.get("/coding/sessions");
        setSessions(data);
      } finally { setLoading(false); }
    })();
  }, []);

  return (
    <div className="space-y-6" data-testid="dashboard-page">
      <div>
        <p className="text-[11px] uppercase tracking-[0.25em] text-chc-slate">Dashboard</p>
        <h1 className="mt-1 text-3xl font-semibold tracking-tight text-chc-ink">
          Welcome, {user?.first_name} <span className="text-chc-slate font-normal">· {user?.facility_name}</span>
        </h1>
        <p className="mt-1 text-sm text-chc-slate">Start a new coding session or review what's active in the last 24 hours.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard testid="stat-active" label="Active sessions" value={loading ? "…" : sessions.length} hint="/ 2 maximum" />
        <StatCard testid="stat-retention" label="Retention" value="24h" hint="Auto-purge enforced" />
        <StatCard testid="stat-external" label="External AI" value="0" hint="In-process PHI redaction" accent />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Link to="/app/wizard" data-testid="cta-new-session"
          className="group relative overflow-hidden rounded-md border border-border bg-chc-navy p-6 text-white transition-all hover:shadow-lg">
          <div className="absolute inset-0 grid-paper opacity-20" />
          <div className="relative flex items-start justify-between">
            <div>
              <p className="text-[11px] uppercase tracking-widest text-chc-cyan">New coding session</p>
              <h3 className="mt-2 text-2xl font-semibold">Upload records & generate codes</h3>
              <p className="mt-2 text-sm text-white/80 max-w-xs">Guided 6-step wizard — OCR, PHI purge, and multi-payer coding in one flow.</p>
            </div>
            <div className="rounded-md bg-white/10 p-3 border border-white/20">
              <Upload size={22} />
            </div>
          </div>
          <div className="relative mt-8 inline-flex items-center gap-2 text-sm font-medium text-chc-cyan">
            Start now <ArrowRight size={16} className="transition-transform group-hover:translate-x-1" />
          </div>
        </Link>

        <div className="rounded-md border border-border bg-white p-6">
          <p className="text-[11px] uppercase tracking-widest text-chc-slate">Security posture</p>
          <ul className="mt-3 space-y-2 text-sm text-chc-ink">
            <li className="flex items-center gap-2"><ShieldCheck weight="fill" className="text-emerald-600" size={16} /> 5-min idle logout enforced</li>
            <li className="flex items-center gap-2"><ShieldCheck weight="fill" className="text-emerald-600" size={16} /> TOTP MFA (RFC 6238)</li>
            <li className="flex items-center gap-2"><ShieldCheck weight="fill" className="text-emerald-600" size={16} /> JWT rotation, 15-min access tokens</li>
            <li className="flex items-center gap-2"><ShieldCheck weight="fill" className="text-emerald-600" size={16} /> 24-hour file auto-purge</li>
            <li className="flex items-center gap-2"><ShieldCheck weight="fill" className="text-emerald-600" size={16} /> Audit trail on every action</li>
          </ul>
        </div>

        <div className="rounded-md border border-border bg-white p-6">
          <p className="text-[11px] uppercase tracking-widest text-chc-slate">Recent sessions</p>
          {loading ? (
            <p className="mt-3 text-sm text-chc-slate">Loading…</p>
          ) : sessions.length === 0 ? (
            <div className="mt-3 rounded-md border border-dashed border-border p-4 text-sm text-chc-slate" data-testid="no-sessions">
              No sessions yet. Start your first from the wizard.
            </div>
          ) : (
            <ul className="mt-3 space-y-3">
              {sessions.map((s) => (
                <li key={s.id} className="flex items-center justify-between rounded-md border border-border p-3">
                  <div>
                    <p className="font-mono text-xs text-chc-ink">{s.id.slice(0, 8)}</p>
                    <p className="text-[11px] text-chc-slate">{s.claim_type} · {s.payer}</p>
                  </div>
                  <Link to={`/app/results/${s.id}`} data-testid={`session-link-${s.id}`} className="text-xs text-chc-blue hover:underline">Open →</Link>
                </li>
              ))}
            </ul>
          )}
          <Link to="/app/history" data-testid="view-history" className="mt-4 inline-flex items-center gap-1.5 text-xs text-chc-blue hover:underline">
            <ClockClockwise size={14} /> View 24-hour history
          </Link>
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, hint, accent, testid }) {
  return (
    <div className={`rounded-md border p-5 ${accent ? "border-chc-cyan/40 bg-chc-mist" : "border-border bg-white"}`} data-testid={testid}>
      <p className="text-[11px] uppercase tracking-widest text-chc-slate">{label}</p>
      <p className={`mt-1 text-3xl font-semibold tracking-tight ${accent ? "text-chc-navy" : "text-chc-ink"}`}>{value}</p>
      <p className="mt-1 text-xs text-chc-slate">{hint}</p>
    </div>
  );
}
