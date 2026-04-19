import React from "react";

export function BrandPanel({ overlay = true, children }) {
  return (
    <div className="relative hidden lg:flex h-full w-full flex-col justify-between overflow-hidden bg-chc-navy text-white">
      <div className="absolute inset-0 grid-paper opacity-30" />
      <div className="absolute inset-0 bg-gradient-to-br from-chc-navy via-[#0b4a96] to-chc-blue" />
      {overlay && <div className="absolute inset-0 bg-chc-navy/50" />}
      <div className="relative z-10 p-10">
        <div className="inline-flex items-center gap-3 rounded-md border border-white/20 bg-white/10 px-3 py-1.5 backdrop-blur">
          <span className="h-2 w-2 rounded-full bg-chc-cyan animate-pulse" />
          <span className="text-[11px] uppercase tracking-[0.2em]">HIPAA-aware • SOC 2 ready</span>
        </div>
        <h1 className="mt-10 text-4xl md:text-5xl font-semibold leading-[1.05] tracking-tight">
          Precision medical coding,<br />
          <span className="text-chc-cyan">de-identified by design.</span>
        </h1>
        <p className="mt-5 max-w-md text-sm text-white/80 leading-relaxed">
          CHC Pro AI reads your records, purges PHI in-process, and returns
          payer-accurate ICD-10, CPT, HCPCS, MS-DRG and UB-04 codes — with full audit trail and 24-hour auto-purge.
        </p>
        <div className="mt-10 grid grid-cols-3 gap-4 max-w-md">
          {[
            ["In-process OCR", "No 3rd-party AI"],
            ["Safe-Harbor", "PHI redaction"],
            ["MUE / NCCI", "Edit checks"],
          ].map(([h, s]) => (
            <div key={h} className="rounded-md border border-white/15 bg-white/5 p-3 backdrop-blur">
              <p className="text-[10px] uppercase tracking-widest text-chc-cyan">{h}</p>
              <p className="mt-1 text-xs font-medium">{s}</p>
            </div>
          ))}
        </div>
      </div>
      <div className="relative z-10 p-10 border-t border-white/10">
        <p className="text-[10px] uppercase tracking-[0.25em] text-white/60">Trusted across</p>
        <p className="mt-2 font-mono text-xs text-white/80">Hospitals · Home Health · SNF · Ambulance · Outpatient · Professional</p>
      </div>
      {children}
    </div>
  );
}
