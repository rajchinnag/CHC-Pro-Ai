import React from "react";
import { Lifebuoy, Lock, ShieldCheck } from "@phosphor-icons/react";

export default function HelpPage() {
  return (
    <div className="space-y-6 max-w-3xl" data-testid="help-page">
      <div>
        <p className="text-[11px] uppercase tracking-[0.25em] text-chc-slate">Help & FAQ</p>
        <h1 className="mt-1 text-3xl font-semibold tracking-tight text-chc-ink">Need a hand?</h1>
      </div>
      {[
        { q: "Why do my records disappear after 24 hours?", a: "CHC Pro AI enforces a strict 24-hour auto-purge of all uploaded files and coding results. There is no manual extension — this is a HIPAA safeguard." },
        { q: "Does my data leave the server?", a: "No. OCR, PHI redaction, and coding run entirely in-process. We never call external AI services." },
        { q: "How does MFA work?", a: "Time-based One-Time Passwords (TOTP, RFC 6238) via Microsoft/Google Authenticator. Required for every login after initial setup." },
        { q: "What happens after 5 minutes idle?", a: "You are automatically signed out. A 60-second warning banner appears before logout." },
        { q: "Why is my account still pending?", a: "All coder accounts must be approved by your Facility Provider/Administrator before first login." },
      ].map((f, i) => (
        <div key={i} className="rounded-md border border-border bg-white p-5">
          <p className="font-semibold text-chc-ink">{f.q}</p>
          <p className="mt-1 text-sm text-chc-slate">{f.a}</p>
        </div>
      ))}
    </div>
  );
}
