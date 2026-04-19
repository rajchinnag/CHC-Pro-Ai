import React, { useState } from "react";
import { api, formatApiError } from "@/lib/http";
import { useAuth } from "@/contexts/AuthContext";
import { toast } from "sonner";

export default function SettingsPage() {
  const { user } = useAuth();
  const [cur, setCur] = useState("");
  const [nw, setNw] = useState("");
  const [busy, setBusy] = useState(false);
  const [mfaData, setMfaData] = useState(null);
  const [mfaCode, setMfaCode] = useState("");
  const [mfaPw, setMfaPw] = useState("");

  const changePassword = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      await api.post("/settings/change-password", { current_password: cur, new_password: nw });
      toast.success("Password updated");
      setCur(""); setNw("");
    } catch (err) { toast.error(formatApiError(err)); }
    finally { setBusy(false); }
  };

  const resetMFA = async () => {
    setBusy(true);
    try {
      const { data } = await api.post("/settings/reset-mfa", { password: mfaPw });
      setMfaData(data);
      toast.info("Scan the new QR and confirm with a 6-digit code.");
    } catch (err) { toast.error(formatApiError(err)); }
    finally { setBusy(false); }
  };

  const confirmMFA = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      await api.post("/settings/confirm-mfa-reset", { registration_token: "", code: mfaCode });
      toast.success("MFA re-enabled");
      setMfaData(null); setMfaCode(""); setMfaPw("");
    } catch (err) { toast.error(formatApiError(err)); }
    finally { setBusy(false); }
  };

  return (
    <div className="space-y-6 max-w-3xl" data-testid="settings-page">
      <div>
        <p className="text-[11px] uppercase tracking-[0.25em] text-chc-slate">Settings</p>
        <h1 className="mt-1 text-3xl font-semibold tracking-tight text-chc-ink">Account & security</h1>
      </div>

      <Section title="Account status">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <Info label="Email" value={user?.email} />
          <Info label="Role" value={user?.role} />
          <Info label="NPI" value={user?.npi} />
          <Info label="Status" value={user?.approved ? "Approved" : "Pending approval"} />
          <Info label="MFA" value={user?.mfa_enabled ? "Enabled" : "Not enabled"} />
          <Info label="Security question" value={user?.security_question} />
        </div>
      </Section>

      <Section title="Change password">
        <form onSubmit={changePassword} className="grid grid-cols-1 md:grid-cols-2 gap-3" data-testid="change-password-form">
          <Field label="Current password" type="password" value={cur} onChange={setCur} testid="cp-current" />
          <Field label="New password (12+ chars)" type="password" value={nw} onChange={setNw} testid="cp-new" />
          <div className="md:col-span-2">
            <button type="submit" disabled={busy} data-testid="cp-submit" className="rounded-md bg-chc-navy px-4 py-2 text-sm font-medium text-white hover:bg-[#002f67] disabled:opacity-60">
              Update password
            </button>
          </div>
        </form>
      </Section>

      <Section title="Reset MFA device">
        <p className="text-xs text-chc-slate">Re-verify your password, then re-scan a new QR code in your Authenticator app.</p>
        {!mfaData ? (
          <div className="mt-3 flex items-end gap-3" data-testid="reset-mfa-form">
            <Field label="Current password" type="password" value={mfaPw} onChange={setMfaPw} testid="mfa-reset-password" />
            <button disabled={busy} onClick={resetMFA} data-testid="mfa-reset-submit" className="rounded-md bg-chc-navy px-4 py-2 text-sm font-medium text-white hover:bg-[#002f67] disabled:opacity-60">
              Reset MFA
            </button>
          </div>
        ) : (
          <form className="mt-3 rounded-md border border-border p-4 flex flex-col md:flex-row items-start gap-5" onSubmit={confirmMFA}>
            <img src={mfaData.mfa_qr_png} alt="MFA QR" className="h-40 w-40 border border-border rounded-md" data-testid="mfa-reset-qr" />
            <div className="flex-1 space-y-3">
              <p className="text-xs text-chc-slate">Scan with Microsoft/Google Authenticator.</p>
              <Field label="6-digit code" value={mfaCode} onChange={setMfaCode} maxLength={6} testid="mfa-reset-code" />
              <button disabled={busy || mfaCode.length !== 6} className="rounded-md bg-chc-navy px-4 py-2 text-sm font-medium text-white hover:bg-[#002f67] disabled:opacity-60" data-testid="mfa-reset-confirm">Confirm</button>
            </div>
          </form>
        )}
      </Section>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <section className="rounded-md border border-border bg-white p-5">
      <h3 className="text-sm font-semibold text-chc-ink mb-4">{title}</h3>
      {children}
    </section>
  );
}
function Info({ label, value }) {
  return (
    <div>
      <p className="text-[11px] uppercase tracking-widest text-chc-slate">{label}</p>
      <p className="mt-0.5 text-sm text-chc-ink font-mono break-all">{value || "—"}</p>
    </div>
  );
}
function Field({ label, type = "text", value, onChange, testid, ...rest }) {
  return (
    <label className="block">
      <span className="block text-[11px] font-semibold uppercase tracking-widest text-chc-slate mb-1">{label}</span>
      <input type={type} value={value} onChange={(e) => onChange(e.target.value)} data-testid={testid}
        className="h-10 w-full rounded-md border border-border bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#0073CF]" {...rest} />
    </label>
  );
}
