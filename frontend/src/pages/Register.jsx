import React, { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, formatApiError } from "@/lib/http";
import { BrandPanel } from "@/components/BrandPanel";
import { toast } from "sonner";
import { CheckCircle, Shield, Fingerprint, EnvelopeSimple, Warning } from "@phosphor-icons/react";

const STEPS = ["Account", "Email OTP", "Setup MFA", "Complete"];

const SECURITY_QUESTIONS = [
  "What was the name of your first pet?",
  "In what city were you born?",
  "What is your mother's maiden name?",
  "What was the model of your first car?",
  "What was the name of your elementary school?",
];

export default function RegisterPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);

  // step 0 - account
  const [form, setForm] = useState({
    npi: "",
    tax_id: "",
    email: "",
    first_name: "",
    middle_name: "",
    last_name: "",
    date_of_birth: "",
    security_question: SECURITY_QUESTIONS[0],
    security_answer: "",
    password: "",
    verify_password: "",
    captcha_answer: "",
  });
  const [captcha, setCaptcha] = useState({ token: "", question: "" });

  // tokens
  const [regToken, setRegToken] = useState("");
  const [devOtp, setDevOtp] = useState(""); // dev mode display
  const [otp, setOtp] = useState("");

  // mfa
  const [mfaQr, setMfaQr] = useState("");
  const [mfaSecret, setMfaSecret] = useState("");
  const [mfaCode, setMfaCode] = useState("");

  const loadCaptcha = async () => {
    const { data } = await api.get("/captcha");
    setCaptcha(data);
  };
  useEffect(() => { loadCaptcha(); }, []);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target?.value ?? e });

  const pwStrength = useMemo(() => {
    const p = form.password || "";
    let s = 0;
    if (p.length >= 12) s++;
    if (/[A-Z]/.test(p)) s++;
    if (/[a-z]/.test(p)) s++;
    if (/\d/.test(p)) s++;
    if (/[^A-Za-z0-9]/.test(p)) s++;
    return s;
  }, [form.password]);

  const submitAccount = async (e) => {
    e.preventDefault();
    if (form.password !== form.verify_password) {
      toast.error("Passwords do not match"); return;
    }
    setLoading(true);
    try {
      const payload = { ...form, captcha_token: captcha.token };
      const { data } = await api.post("/auth/register", payload);
      setRegToken(data.registration_token);
      if (data.dev_otp) setDevOtp(data.dev_otp);
      setStep(1);
      toast.success("Account created. Verify the OTP sent to your email.");
    } catch (err) {
      toast.error(formatApiError(err));
      loadCaptcha();
    } finally {
      setLoading(false);
    }
  };

  const submitOtp = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const { data } = await api.post("/auth/verify-otp", { registration_token: regToken, otp });
      setRegToken(data.registration_token);
      setMfaQr(data.mfa_qr_png);
      setMfaSecret(data.mfa_secret);
      setStep(2);
      toast.success("Email verified. Now scan the QR code.");
    } catch (err) {
      toast.error(formatApiError(err));
    } finally { setLoading(false); }
  };

  const submitMfa = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.post("/auth/confirm-mfa", { registration_token: regToken, code: mfaCode });
      setStep(3);
    } catch (err) {
      toast.error(formatApiError(err));
    } finally { setLoading(false); }
  };

  return (
    <div className="grid min-h-screen grid-cols-1 lg:grid-cols-2">
      <BrandPanel />
      <div className="flex items-center justify-center p-6 md:p-10 overflow-y-auto">
        <div className="w-full max-w-xl">
          <div className="mb-6">
            <p className="text-[11px] uppercase tracking-[0.25em] text-chc-slate">Create account</p>
            <h2 className="mt-1 text-3xl font-semibold tracking-tight text-chc-ink">Register as a Medical Coder</h2>
            <p className="mt-2 text-sm text-chc-slate">
              Already have an account? <Link to="/login" className="font-medium text-chc-blue hover:underline" data-testid="link-login">Sign in</Link>
            </p>
          </div>

          <Stepper steps={STEPS} current={step} />

          {step === 0 && (
            <form onSubmit={submitAccount} className="mt-6 space-y-4" data-testid="register-form">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Field label="NPI (10 digits)" testid="reg-npi" value={form.npi} onChange={set("npi")} maxLength={10} inputMode="numeric" required />
                <Field label="Tax ID / EIN (9 digits)" testid="reg-taxid" value={form.tax_id} onChange={set("tax_id")} maxLength={9} inputMode="numeric" required />
              </div>
              <Field label="Work email" type="email" testid="reg-email" value={form.email} onChange={set("email")} icon={EnvelopeSimple} required />
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <Field label="First name" testid="reg-firstname" value={form.first_name} onChange={set("first_name")} required />
                <Field label="Middle (optional)" testid="reg-middlename" value={form.middle_name} onChange={set("middle_name")} />
                <Field label="Last name" testid="reg-lastname" value={form.last_name} onChange={set("last_name")} required />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Field label="Date of birth" type="date" testid="reg-dob" value={form.date_of_birth} onChange={set("date_of_birth")} required />
                <label className="block">
                  <span className="block text-[11px] font-semibold uppercase tracking-widest text-chc-slate mb-1">Security question</span>
                  <select
                    data-testid="reg-secq"
                    value={form.security_question}
                    onChange={set("security_question")}
                    className="h-11 w-full rounded-md border border-border bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#0073CF]"
                  >
                    {SECURITY_QUESTIONS.map((q) => <option key={q} value={q}>{q}</option>)}
                  </select>
                </label>
              </div>
              <Field label="Answer to security question" testid="reg-seca" value={form.security_answer} onChange={set("security_answer")} required />

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <Field label="Password" type="password" testid="reg-password" value={form.password} onChange={set("password")} required />
                  <div className="mt-2 h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                    <div className={`h-full transition-all ${
                      pwStrength < 3 ? "bg-rose-400" : pwStrength < 5 ? "bg-amber-400" : "bg-emerald-500"
                    }`} style={{ width: `${(pwStrength / 5) * 100}%` }} />
                  </div>
                  <p className="mt-1 text-[10px] text-chc-slate">12+ chars, upper, lower, number, special.</p>
                </div>
                <Field label="Verify password" type="password" testid="reg-verify-password" value={form.verify_password} onChange={set("verify_password")} required />
              </div>

              <div className="rounded-md border border-border bg-chc-mist p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-[11px] uppercase tracking-widest text-chc-slate">Human check</p>
                    <p className="mt-1 font-mono text-lg text-chc-navy" data-testid="reg-captcha-question">{captcha.question}</p>
                  </div>
                  <button type="button" onClick={loadCaptcha} className="text-xs text-chc-blue hover:underline" data-testid="reg-captcha-refresh">refresh</button>
                </div>
                <input
                  data-testid="reg-captcha-answer"
                  value={form.captcha_answer}
                  onChange={set("captcha_answer")}
                  inputMode="numeric"
                  className="mt-3 h-10 w-36 rounded-md border border-border bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#0073CF]"
                  placeholder="Answer"
                  required
                />
              </div>

              <button type="submit" disabled={loading} data-testid="reg-submit"
                className="w-full rounded-md bg-chc-navy px-4 py-2.5 text-sm font-medium text-white hover:bg-[#002f67] disabled:opacity-60 transition-colors">
                {loading ? "Submitting…" : "Create account"}
              </button>
            </form>
          )}

          {step === 1 && (
            <form onSubmit={submitOtp} className="mt-6 space-y-4" data-testid="otp-form">
              <div className="rounded-md border border-border bg-chc-mist p-4">
                <p className="text-[11px] uppercase tracking-widest text-chc-slate">Email verification</p>
                <p className="mt-1 text-sm text-chc-ink">Enter the 6-digit code sent to <span className="font-mono">{form.email}</span>.</p>
                {devOtp && (
                  <div className="mt-3 flex items-center gap-2 rounded-md border border-amber-300 bg-amber-50 p-2 text-xs text-amber-800" data-testid="dev-otp-banner">
                    <Warning size={14} /> <span>Dev mode: your OTP is <span className="font-mono font-bold">{devOtp}</span></span>
                  </div>
                )}
              </div>
              <Field label="Email OTP" testid="otp-input" value={otp} onChange={setOtp} maxLength={6} inputMode="numeric" required />
              <button type="submit" disabled={loading || otp.length !== 6} data-testid="otp-submit"
                className="w-full rounded-md bg-chc-navy px-4 py-2.5 text-sm font-medium text-white hover:bg-[#002f67] disabled:opacity-60">
                {loading ? "Verifying…" : "Verify email"}
              </button>
            </form>
          )}

          {step === 2 && (
            <form onSubmit={submitMfa} className="mt-6 space-y-4" data-testid="mfa-setup-form">
              <div className="rounded-md border border-border bg-white p-5 flex flex-col sm:flex-row items-center gap-5">
                {mfaQr && <img src={mfaQr} alt="MFA QR" className="h-40 w-40 rounded-md border border-border" data-testid="mfa-qr-img" />}
                <div className="flex-1">
                  <p className="text-[11px] uppercase tracking-widest text-chc-slate">Multi-factor authentication</p>
                  <p className="mt-1 text-sm text-chc-ink">Scan the QR with <b>Microsoft Authenticator</b> or <b>Google Authenticator</b>, then enter the 6-digit code below.</p>
                  <div className="mt-3 rounded-md border border-border bg-chc-mist p-3">
                    <p className="text-[10px] uppercase tracking-widest text-chc-slate">Secret key</p>
                    <p className="mt-1 font-mono text-xs break-all text-chc-ink" data-testid="mfa-secret">{mfaSecret}</p>
                  </div>
                </div>
              </div>
              <Field label="6-digit authenticator code" testid="mfa-code" value={mfaCode} onChange={setMfaCode} maxLength={6} inputMode="numeric" required />
              <button type="submit" disabled={loading || mfaCode.length !== 6} data-testid="mfa-submit"
                className="w-full rounded-md bg-chc-navy px-4 py-2.5 text-sm font-medium text-white hover:bg-[#002f67] disabled:opacity-60">
                {loading ? "Confirming…" : "Confirm MFA & submit for approval"}
              </button>
            </form>
          )}

          {step === 3 && (
            <div className="mt-8 rounded-md border border-emerald-200 bg-emerald-50 p-6" data-testid="register-complete">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-full bg-emerald-500 flex items-center justify-center">
                  <CheckCircle className="text-white" weight="fill" size={24} />
                </div>
                <div>
                  <p className="text-[11px] uppercase tracking-widest text-emerald-700">Submitted</p>
                  <h3 className="text-lg font-semibold text-chc-ink">Your registration is pending approval</h3>
                </div>
              </div>
              <p className="mt-3 text-sm text-chc-slate leading-relaxed">
                Your account is pending approval from your Facility Provider/Administrator.
                You will receive an email once approved. MFA is now active on this device.
              </p>
              <button onClick={() => navigate("/login")} data-testid="register-goto-login" className="mt-4 rounded-md bg-chc-navy px-4 py-2 text-sm font-medium text-white hover:bg-[#002f67]">
                Return to login
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Stepper({ steps, current }) {
  return (
    <ol className="flex items-center gap-2" data-testid="register-stepper">
      {steps.map((label, i) => {
        const done = i < current;
        const active = i === current;
        return (
          <li key={label} className="flex-1">
            <div className={`h-1 w-full rounded-full ${done ? "bg-chc-cyan" : active ? "bg-chc-navy" : "bg-slate-200"}`} />
            <div className="mt-2 flex items-center gap-1.5 text-[11px]">
              <span className={`h-1.5 w-1.5 rounded-full ${done ? "bg-chc-cyan" : active ? "bg-chc-navy" : "bg-slate-300"}`} />
              <span className={`${active ? "text-chc-ink font-semibold" : "text-chc-slate"}`}>{label}</span>
            </div>
          </li>
        );
      })}
    </ol>
  );
}

function Field({ label, type = "text", icon: Icon, value, onChange, testid, ...rest }) {
  return (
    <label className="block">
      <span className="block text-[11px] font-semibold uppercase tracking-widest text-chc-slate mb-1">{label}</span>
      <div className="relative">
        {Icon && <Icon className="absolute left-3 top-1/2 -translate-y-1/2 text-chc-slate" size={16} />}
        <input
          type={type}
          value={value}
          onChange={onChange}
          data-testid={testid}
          className={`h-11 w-full rounded-md border border-border bg-white px-3 ${Icon ? "pl-9" : ""} text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#0073CF] transition`}
          {...rest}
        />
      </div>
    </label>
  );
}
