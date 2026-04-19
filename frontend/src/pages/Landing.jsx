import React from "react";
import { Link } from "react-router-dom";
import { BrandPanel } from "@/components/BrandPanel";
import { ArrowRight, ShieldCheck, ScanSmiley, ClipboardText, Lock, Lightbulb, ChartBar } from "@phosphor-icons/react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      <header className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
        <div className="flex items-center gap-2">
          <div className="h-9 w-9 rounded-sm bg-chc-navy flex items-center justify-center">
            <ShieldCheck className="text-white" weight="fill" size={18} />
          </div>
          <div>
            <p className="text-sm font-semibold text-chc-ink leading-none">CHC Pro AI</p>
            <p className="text-[10px] uppercase tracking-widest text-chc-slate">Medical coding platform</p>
          </div>
        </div>
        <nav className="flex items-center gap-3">
          <Link to="/login" data-testid="landing-login" className="text-sm font-medium text-chc-navy hover:text-chc-blue">Sign in</Link>
          <Link to="/register" data-testid="landing-register" className="rounded-md bg-chc-navy px-3 py-1.5 text-sm font-medium text-white hover:bg-[#002f67]">Register</Link>
        </nav>
      </header>

      <section className="grid grid-cols-1 lg:grid-cols-2">
        <BrandPanel />
        <div className="flex items-center justify-center p-10 md:p-16">
          <div>
            <p className="text-[11px] uppercase tracking-[0.25em] text-chc-slate">For Medical Coders & Providers</p>
            <h1 className="mt-2 text-4xl md:text-5xl font-semibold tracking-tight text-chc-ink leading-[1.05]">
              Accurate coding.<br />
              <span className="text-chc-navy">Nothing sent to external AI.</span>
            </h1>
            <p className="mt-4 max-w-lg text-sm text-chc-slate leading-relaxed">
              CHC Pro AI performs OCR, redacts PHI in-process, and applies CMS / AMA / NUBC guidelines
              to produce ICD-10, CPT, HCPCS, MS-DRG, Revenue, Condition, Occurrence and Value codes for
              UB-04 and CMS-1500 claims. Records auto-purge after 24 hours.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link to="/register" data-testid="landing-cta-register" className="inline-flex items-center gap-2 rounded-md bg-chc-navy px-5 py-2.5 text-sm font-medium text-white hover:bg-[#002f67]">
                Create your account <ArrowRight size={16} />
              </Link>
              <Link to="/login" data-testid="landing-cta-login" className="inline-flex items-center gap-2 rounded-md border border-border bg-white px-5 py-2.5 text-sm font-medium text-chc-navy hover:bg-chc-mist">
                Sign in
              </Link>
            </div>

            <dl className="mt-12 grid grid-cols-2 gap-5 max-w-md">
              {[
                ["ICD-10", "CM + PCS"],
                ["CPT / HCPCS", "AMA & CMS"],
                ["MS-DRG", "CMS IPPS v41"],
                ["UB-04 + 1500", "NUBC compliant"],
              ].map(([t, s]) => (
                <div key={t} className="rounded-md border border-border bg-white p-3">
                  <dt className="text-[11px] uppercase tracking-widest text-chc-slate">{t}</dt>
                  <dd className="mt-1 font-mono text-sm text-chc-ink">{s}</dd>
                </div>
              ))}
            </dl>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-6 py-16">
        <p className="text-[11px] uppercase tracking-[0.25em] text-chc-slate">Why CHC Pro AI</p>
        <h2 className="mt-1 text-3xl font-semibold tracking-tight text-chc-ink">Built for the audit trail, not the demo reel.</h2>
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { icon: Lock, title: "Zero external AI", body: "OCR, PHI purge and coding all run in-process. Nothing leaves the server." },
            { icon: ScanSmiley, title: "Real OCR + PHI", body: "Tesseract OCR with a Safe-Harbor redaction pipeline — 18 PHI categories." },
            { icon: ClipboardText, title: "Payer-aware", body: "Payer-specific LCD/NCD and state Medicaid fee schedule evaluation." },
            { icon: Lightbulb, title: "MUE + NCCI", body: "Every output passes Medically Unlikely Edits and NCCI bundling checks." },
            { icon: ShieldCheck, title: "HIPAA guardrails", body: "MFA, 5-min idle logout, 24h auto-purge, full audit logs." },
            { icon: ChartBar, title: "Explainable codes", body: "Every code ships with a guideline citation and validation status." },
          ].map(({ icon: Icon, title, body }) => (
            <div key={title} className="rounded-md border border-border bg-white p-5">
              <div className="h-9 w-9 rounded-md bg-chc-mist flex items-center justify-center">
                <Icon className="text-chc-navy" size={18} />
              </div>
              <p className="mt-3 font-semibold text-chc-ink">{title}</p>
              <p className="mt-1 text-sm text-chc-slate">{body}</p>
            </div>
          ))}
        </div>
      </section>

      <footer className="border-t border-border">
        <div className="mx-auto max-w-7xl px-6 py-6 text-xs text-chc-slate flex items-center justify-between">
          <p>© 2026 CHC Pro AI · All processing occurs within this application server.</p>
          <p className="font-mono">HIPAA • Safe Harbor • NUBC • CMS • AMA</p>
        </div>
      </footer>
    </div>
  );
}
