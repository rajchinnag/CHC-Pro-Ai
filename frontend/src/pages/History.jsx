import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "@/lib/http";
import { FileText, Trash } from "@phosphor-icons/react";
import { toast } from "sonner";

export default function HistoryPage() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    const { data } = await api.get("/coding/sessions");
    setSessions(data);
    setLoading(false);
  };
  useEffect(() => { load(); }, []);

  const remove = async (id) => {
    if (!window.confirm("Delete this session? This cannot be undone.")) return;
    await api.delete(`/coding/sessions/${id}`);
    toast.success("Session deleted");
    load();
  };

  return (
    <div className="space-y-6" data-testid="history-page">
      <div>
        <p className="text-[11px] uppercase tracking-[0.25em] text-chc-slate">History</p>
        <h1 className="mt-1 text-3xl font-semibold tracking-tight text-chc-ink">Last 24 hours</h1>
        <p className="mt-1 text-sm text-chc-slate">No PHI is displayed here. Sessions auto-purge after 24 hours; a maximum of 2 sessions are retained.</p>
      </div>

      {loading ? (
        <p className="text-sm text-chc-slate">Loading…</p>
      ) : sessions.length === 0 ? (
        <div className="rounded-md border border-dashed border-border p-10 text-center" data-testid="history-empty">
          <FileText size={28} className="mx-auto text-chc-slate" />
          <p className="mt-3 text-sm text-chc-ink">No sessions in the last 24 hours.</p>
        </div>
      ) : (
        <ul className="space-y-3">
          {sessions.map((s) => (
            <li key={s.id} className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 rounded-md border border-border bg-white p-4" data-testid={`history-row-${s.id}`}>
              <div className="flex items-center gap-4">
                <div className="h-10 w-10 rounded-md bg-chc-mist flex items-center justify-center">
                  <FileText className="text-chc-navy" size={18} />
                </div>
                <div>
                  <p className="font-mono text-sm text-chc-ink">Session {s.id.slice(0, 8)}</p>
                  <p className="text-[11px] text-chc-slate">{s.claim_type} · {s.payer}{s.state ? ` / ${s.state}` : ""} · {new Date(s.created_at).toLocaleString()}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-[11px] px-2 py-0.5 rounded-full border ${s.status === "processed" ? "border-emerald-200 bg-emerald-50 text-emerald-700" : "border-border bg-slate-50 text-chc-slate"}`}>
                  {s.status}
                </span>
                <Link to={`/app/results/${s.id}`} className="text-xs text-chc-blue hover:underline" data-testid={`history-open-${s.id}`}>Open →</Link>
                <button onClick={() => remove(s.id)} className="text-chc-slate hover:text-rose-600" data-testid={`history-delete-${s.id}`}>
                  <Trash size={16} />
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
