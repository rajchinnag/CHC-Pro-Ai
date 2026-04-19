import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, formatApiError } from "@/lib/http";
import { useAuth } from "@/contexts/AuthContext";
import { BrandPanel } from "@/components/BrandPanel";
import { toast } from "sonner";
import { LockKey, EnvelopeSimple, ShieldCheck } from "@phosphor-icons/react";

export default function LoginPage() {
  const { storeTokens, reload } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [step, setStep] = useState("credentials"); // credentials | mfa
  const [mfaToken, setMfaToken] = useState("");
  const [mfaCode, setMfaCode] = useState("");
  const [loading, setLoading] = useState(false);

  const submitLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const { data } = await api.post("/auth/login", { email, password });
      if (data.mfa_required) {
        setMfaToken(data.mfa_token);
        setStep("mfa");
        toast.info("Enter the 6-digit code from your Authenticator app.");
      } else {
        storeTokens(data.access_token, data.refresh_token);
        await reload();
        const role = data.user?.role;
        toast.success("Welcome back.");
        navigate(role === "admin" || role === "provider" ? "/app/admin/pending" : "/app/dashboard");
      }
    } catch (err) {
      toast.error(formatApiError(err));
    } finally {
      setLoading(false);
    }
  };

  const submitMfa = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const { data } = await api.post("/auth/login-mfa", { mfa_token: mfaToken, code: mfaCode });
      storeTokens(data.access_token, data.refresh_token);
      await reload();
      toast.success("Signed in.");
      const role = data.user?.role;
      navigate(role === "admin" || role === "provider" ? "/app/admin/pending" : "/app/dashboard");
    } catch (err) {
      toast.error(formatApiError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid min-h-screen grid-cols-1 lg:grid-cols-2">
      <BrandPanel />
      <div className="flex items-center justify-center p-6 md:p-10">
        <div className="w-full max-w-md">
          <div className="mb-8 flex items-center gap-2 lg:hidden">
            <div className="h-9 w-9 rounded-sm bg-chc-navy flex items-center justify-center">
              <ShieldCheck className="text-white" weight="fill" size={18} />
            </div>
            <p className="font-semibold text-chc-ink">CHC Pro AI</p>
          </div>

          <p className="text-[11px] uppercase tracking-[0.25em] text-chc-slate">Sign in</p>
          <h2 className="mt-1 text-3xl font-semibold tracking-tight text-chc-ink">Welcome back</h2>
          <p className="mt-2 text-sm text-chc-slate">
            Don't have an account?{" "}
            <Link to="/register" data-testid="link-register" className="font-medium text-chc-blue hover:underline">Register</Link>
          </p>

          {step === "credentials" ? (
            <form className="mt-8 space-y-4" onSubmit={submitLogin} data-testid="login-form">
              <Field label="Work email" icon={EnvelopeSimple} type="email" value={email} onChange={setEmail} testid="login-email" required />
              <Field label="Password" icon={LockKey} type="password" value={password} onChange={setPassword} testid="login-password" required />
              <button
                type="submit"
                disabled={loading}
                data-testid="login-submit"
                className="w-full rounded-md bg-chc-navy px-4 py-2.5 text-sm font-medium text-white hover:bg-[#002f67] disabled:opacity-60 transition-colors"
              >
                {loading ? "Signing in…" : "Sign in"}
              </button>
              <p className="text-center text-xs text-chc-slate">
                Protected by MFA. Idle sessions auto-logout after 5 minutes.
              </p>
            </form>
          ) : (
            <form className="mt-8 space-y-4" onSubmit={submitMfa} data-testid="mfa-form">
              <div className="rounded-md border border-border bg-chc-mist p-4">
                <p className="text-[10px] uppercase tracking-widest text-chc-slate">Step 2 of 2</p>
                <p className="mt-1 text-sm text-chc-ink">Enter the 6-digit code from Microsoft/Google Authenticator.</p>
              </div>
              <Field label="Authenticator code" icon={ShieldCheck} value={mfaCode} onChange={setMfaCode} testid="login-mfa-code" inputMode="numeric" maxLength={6} required />
              <button type="submit" disabled={loading || mfaCode.length !== 6} data-testid="login-mfa-submit"
                className="w-full rounded-md bg-chc-navy px-4 py-2.5 text-sm font-medium text-white hover:bg-[#002f67] disabled:opacity-60 transition-colors">
                {loading ? "Verifying…" : "Verify & continue"}
              </button>
              <button type="button" onClick={() => setStep("credentials")} className="w-full text-xs text-chc-slate hover:text-chc-ink" data-testid="login-mfa-back">
                ← Use a different account
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

function Field({ label, icon: Icon, type = "text", value, onChange, testid, ...rest }) {
  return (
    <label className="block">
      <span className="block text-[11px] font-semibold uppercase tracking-widest text-chc-slate mb-1">{label}</span>
      <div className="relative">
        {Icon && <Icon className="absolute left-3 top-1/2 -translate-y-1/2 text-chc-slate" size={16} />}
        <input
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          data-testid={testid}
          className={`h-11 w-full rounded-md border border-border bg-white px-3 ${Icon ? "pl-9" : ""} text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#0073CF] focus:border-transparent transition`}
          {...rest}
        />
      </div>
    </label>
  );
}
