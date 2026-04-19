import React, { useEffect, useState } from "react";
import { api } from "@/lib/http";
import { toast } from "sonner";
import { UsersThree, CheckCircle, XCircle } from "@phosphor-icons/react";

export function AdminPending() {
  const [pending, setPending] = useState([]);
  const [loading, setLoading] = useState(true);
  const load = async () => {
    const { data } = await api.get("/admin/pending");
    setPending(data);
    setLoading(false);
  };
  useEffect(() => { load(); }, []);

  const approve = async (id) => {
    await api.post(`/admin/users/${id}/approve`, { reason: "" });
    toast.success("User approved");
    load();
  };
  const reject = async (id) => {
    const reason = window.prompt("Reason for rejection:");
    if (reason === null) return;
    await api.post(`/admin/users/${id}/reject`, { reason });
    toast.success("User rejected");
    load();
  };

  return (
    <div className="space-y-6" data-testid="admin-pending-page">
      <div>
        <p className="text-[11px] uppercase tracking-[0.25em] text-chc-slate">Admin</p>
        <h1 className="mt-1 text-3xl font-semibold tracking-tight text-chc-ink">Pending approvals</h1>
        <p className="mt-1 text-sm text-chc-slate">Review new registrations from your facility.</p>
      </div>
      {loading ? <p className="text-sm text-chc-slate">Loading…</p> : pending.length === 0 ? (
        <div className="rounded-md border border-dashed border-border p-10 text-center" data-testid="admin-pending-empty">
          <UsersThree size={28} className="mx-auto text-chc-slate" />
          <p className="mt-3 text-sm text-chc-ink">No users are currently pending approval.</p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-md border border-border bg-white">
          <table className="w-full text-sm">
            <thead className="bg-chc-mist text-[10px] uppercase tracking-widest text-chc-slate">
              <tr>
                <th className="px-4 py-3 text-left">Name</th>
                <th className="px-4 py-3 text-left">NPI</th>
                <th className="px-4 py-3 text-left">Email</th>
                <th className="px-4 py-3 text-left">Submitted</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {pending.map((u) => (
                <tr key={u.id} className="border-t border-border" data-testid={`pending-${u.id}`}>
                  <td className="px-4 py-3 text-chc-ink">{u.first_name} {u.last_name}</td>
                  <td className="px-4 py-3 font-mono text-xs">{u.npi}</td>
                  <td className="px-4 py-3 text-chc-slate">{u.email}</td>
                  <td className="px-4 py-3 text-xs text-chc-slate">{new Date(u.created_at).toLocaleString()}</td>
                  <td className="px-4 py-3 text-right space-x-2">
                    <button onClick={() => approve(u.id)} data-testid={`approve-${u.id}`} className="inline-flex items-center gap-1 rounded-md bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-emerald-700">
                      <CheckCircle size={14} weight="fill" /> Approve
                    </button>
                    <button onClick={() => reject(u.id)} data-testid={`reject-${u.id}`} className="inline-flex items-center gap-1 rounded-md border border-rose-200 bg-white px-3 py-1.5 text-xs font-medium text-rose-600 hover:bg-rose-50">
                      <XCircle size={14} /> Reject
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export function AdminUsers() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const load = async () => {
    const { data } = await api.get("/admin/users");
    setUsers(data);
    setLoading(false);
  };
  useEffect(() => { load(); }, []);

  const suspend = async (id) => {
    await api.post(`/admin/users/${id}/suspend`);
    toast.success("User suspended");
    load();
  };

  return (
    <div className="space-y-6" data-testid="admin-users-page">
      <div>
        <p className="text-[11px] uppercase tracking-[0.25em] text-chc-slate">Admin</p>
        <h1 className="mt-1 text-3xl font-semibold tracking-tight text-chc-ink">All users</h1>
      </div>
      {loading ? <p className="text-sm text-chc-slate">Loading…</p> : (
        <div className="overflow-hidden rounded-md border border-border bg-white">
          <table className="w-full text-sm">
            <thead className="bg-chc-mist text-[10px] uppercase tracking-widest text-chc-slate">
              <tr>
                <th className="px-4 py-3 text-left">Name</th>
                <th className="px-4 py-3 text-left">Role</th>
                <th className="px-4 py-3 text-left">Email</th>
                <th className="px-4 py-3 text-left">Status</th>
                <th className="px-4 py-3 text-left">MFA</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-t border-border" data-testid={`user-row-${u.id}`}>
                  <td className="px-4 py-3">{u.first_name} {u.last_name}</td>
                  <td className="px-4 py-3 font-mono text-xs">{u.role}</td>
                  <td className="px-4 py-3 text-chc-slate">{u.email}</td>
                  <td className="px-4 py-3">
                    <span className={`text-[11px] px-2 py-0.5 rounded-full border ${u.approved ? "border-emerald-200 bg-emerald-50 text-emerald-700" : "border-amber-200 bg-amber-50 text-amber-700"}`}>
                      {u.approved ? "Active" : "Pending/Suspended"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs">{u.mfa_enabled ? "Enabled" : "—"}</td>
                  <td className="px-4 py-3 text-right">
                    {u.role === "coder" && (
                      <button onClick={() => suspend(u.id)} data-testid={`suspend-${u.id}`} className="text-xs rounded-md border border-border bg-white px-3 py-1 text-chc-navy hover:bg-chc-mist">Suspend</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export function AdminAudit() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    (async () => {
      const { data } = await api.get("/admin/audit?limit=200");
      setLogs(data);
      setLoading(false);
    })();
  }, []);

  return (
    <div className="space-y-6" data-testid="admin-audit-page">
      <div>
        <p className="text-[11px] uppercase tracking-[0.25em] text-chc-slate">Admin</p>
        <h1 className="mt-1 text-3xl font-semibold tracking-tight text-chc-ink">Audit log</h1>
        <p className="mt-1 text-sm text-chc-slate">Every login, upload, coding request and logout is recorded (no PHI in logs).</p>
      </div>
      <div className="overflow-hidden rounded-md border border-border bg-white">
        <table className="w-full text-xs font-mono">
          <thead className="bg-chc-mist text-[10px] uppercase tracking-widest text-chc-slate">
            <tr>
              <th className="px-4 py-3 text-left">Time</th>
              <th className="px-4 py-3 text-left">User</th>
              <th className="px-4 py-3 text-left">Action</th>
              <th className="px-4 py-3 text-left">Metadata</th>
            </tr>
          </thead>
          <tbody>
            {loading ? <tr><td className="p-4 text-chc-slate">Loading…</td></tr> :
              logs.map((l) => (
                <tr key={l.id} className="border-t border-border">
                  <td className="px-4 py-2 text-chc-slate">{new Date(l.timestamp).toLocaleString()}</td>
                  <td className="px-4 py-2">{(l.user_id || "—").slice(0, 8)}</td>
                  <td className="px-4 py-2 text-chc-navy">{l.action}</td>
                  <td className="px-4 py-2 text-chc-slate truncate max-w-xs">{JSON.stringify(l.meta)}</td>
                </tr>
              ))
            }
          </tbody>
        </table>
      </div>
    </div>
  );
}
