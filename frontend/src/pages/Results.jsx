import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "@/lib/http";
import { CheckCircle, WarningCircle, Download, ArrowsClockwise, FilePlus, ShieldCheck } from "@phosphor-icons/react";

export default function ResultsPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    const { data } = await api.get(`/coding/sessions/${id}`);
    setSession(data);
    setLoading(false);
  };
  useEffect(() => { load(); }, [id]);

  const rerun = async () => {
    setLoading(true);
    try {
      await api.post(`/coding/sessions/${id}/process`);
      await load();
    } catch (e) {
      await load();
    }
  };

  const exportCSV = () => {
    const r = session?.coding_result;
    if (!r) return;
    const rows = [["CodeType","Code","Description","GuidelineRef","Status","Note"]];
    const push = (c) => c && rows.push([c.code_type, c.code, (c.description || "").replace(/"/g, '""'), (c.guideline_ref || "").replace(/"/g, '""'), c.status, c.note || ""]);
    push(r.principal_diagnosis);
    (r.secondary_diagnoses || []).forEach(push);
    push(r.principal_procedure);
    (r.additional_procedures || []).forEach(push);
    push(r.ms_drg);
    (r.revenue_codes || []).forEach(push);
    (r.condition_codes || []).forEach(push);
    (r.occurrence_codes || []).forEach(push);
    (r.value_codes || []).forEach(push);
    (r.modifiers || []).forEach(push);
    const csv = rows.map((row) => row.map((x) => `"${x ?? ""}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `chc-codes-${session.id.slice(0, 8)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (loading) return <div className="p-6 text-sm text-chc-slate" data-testid="results-loading">Loading results…</div>;
  if (!session) return <div className="p-6 text-sm text-chc-slate">Session not found.</div>;

  const r = session.coding_result;
  const phi = session.phi_report || {};
  const totalRedactions = Object.values(phi.redactions || {}).reduce((a, b) => a + b, 0);

  return (
    <div className="space-y-6" data-testid="results-page">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        <div>
          <p className="text-[11px] uppercase tracking-[0.25em] text-chc-slate">Coding results</p>
          <h1 className="mt-1 text-3xl font-semibold tracking-tight text-chc-ink">Session <span className="font-mono text-chc-navy">{session.id.slice(0, 8)}</span></h1>
          <p className="mt-1 text-sm text-chc-slate">{session.claim_type} · {session.payer}{session.state ? ` / ${session.state}` : ""} · {(session.specialty || []).join(", ")}</p>
        </div>
        <div className="flex gap-2">
          <button onClick={exportCSV} data-testid="export-csv" className="inline-flex items-center gap-2 rounded-md border border-border bg-white px-3 py-2 text-xs font-medium text-chc-navy hover:bg-chc-mist">
            <Download size={14} /> Download CSV
          </button>
          <button onClick={rerun} data-testid="rerun-btn" className="inline-flex items-center gap-2 rounded-md border border-border bg-white px-3 py-2 text-xs font-medium text-chc-navy hover:bg-chc-mist">
            <ArrowsClockwise size={14} /> Review again
          </button>
          <button onClick={() => navigate("/app/wizard")} data-testid="new-session-btn" className="inline-flex items-center gap-2 rounded-md bg-chc-navy px-3 py-2 text-xs font-medium text-white hover:bg-[#002f67]">
            <FilePlus size={14} /> Start new record
          </button>
        </div>
      </div>

      {/* PHI report */}
      <div className="rounded-md border border-emerald-200 bg-emerald-50 p-4" data-testid="phi-report">
        <div className="flex items-start gap-3">
          <ShieldCheck className="text-emerald-600 mt-0.5" size={20} weight="fill" />
          <div className="flex-1">
            <p className="font-medium text-emerald-900">PHI successfully removed · {totalRedactions} identifiers redacted</p>
            <p className="mt-0.5 text-xs text-emerald-800">Categories: {(phi.categories_found || []).join(" · ") || "none detected"}</p>
          </div>
          <p className="text-[11px] text-emerald-800 font-mono">OCR pages: {session.ocr_pages ?? "—"}</p>
        </div>
      </div>

      {r ? (
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          <div className="xl:col-span-2 space-y-6">
            <Section title="Principal diagnosis (ICD-10-CM)">
              <CodeRow c={r.principal_diagnosis} />
            </Section>
            <Section title="Secondary diagnoses" empty="No secondary diagnoses matched.">
              {(r.secondary_diagnoses || []).map((c) => <CodeRow key={c.code} c={c} />)}
            </Section>
            <Section title="Principal procedure">
              <CodeRow c={r.principal_procedure} />
            </Section>
            <Section title="Additional procedures" empty="None.">
              {(r.additional_procedures || []).map((c, i) => <CodeRow key={c.code + i} c={c} />)}
            </Section>
            {r.ms_drg && (
              <Section title="MS-DRG assignment">
                <CodeRow c={r.ms_drg} />
              </Section>
            )}
            {session.claim_type === "UB-04" && (
              <>
                <Section title="Revenue codes" empty="None matched.">
                  {(r.revenue_codes || []).map((c) => <CodeRow key={c.code} c={c} />)}
                </Section>
                <Section title="Condition codes" empty="None matched.">
                  {(r.condition_codes || []).map((c) => <CodeRow key={c.code} c={c} />)}
                </Section>
                <Section title="Occurrence codes" empty="None matched.">
                  {(r.occurrence_codes || []).map((c) => <CodeRow key={c.code} c={c} />)}
                </Section>
                <Section title="Value codes" empty="None matched.">
                  {(r.value_codes || []).map((c) => <CodeRow key={c.code} c={c} />)}
                </Section>
              </>
            )}
            {(r.modifiers || []).length > 0 && (
              <Section title="Modifiers">
                {r.modifiers.map((c) => <CodeRow key={c.code} c={c} />)}
              </Section>
            )}
          </div>

          <div className="space-y-6">
            <Section title="Processing log" mono>
              <ul className="space-y-2 text-xs">
                {(r.processing_log || []).map((l, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <CheckCircle size={14} weight="fill" className="text-chc-blue mt-0.5" />
                    <span className="text-chc-ink font-mono">{l}</span>
                  </li>
                ))}
              </ul>
            </Section>
            <Section title="MUE edits">
              <ul className="text-xs text-chc-ink space-y-1 font-mono">
                {(r.mue_checks || []).map((m, i) => <li key={i}>• {m}</li>)}
              </ul>
            </Section>
            <Section title="NCCI edits">
              <ul className="text-xs text-chc-ink space-y-1 font-mono">
                {(r.ncci_checks || []).map((m, i) => <li key={i}>• {m}</li>)}
              </ul>
            </Section>
          </div>
        </div>
      ) : (
        <div className="rounded-md border border-border bg-white p-6 text-sm text-chc-slate">No coding result yet.</div>
      )}
    </div>
  );
}

function Section({ title, children, empty, mono }) {
  const hasChildren = React.Children.toArray(children).some((c) => c !== null && c !== undefined && c !== false);
  return (
    <section className="rounded-md border border-border bg-white">
      <header className="border-b border-border px-5 py-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-chc-ink tracking-tight">{title}</h3>
      </header>
      <div className={`p-4 space-y-2 ${mono ? "font-mono" : ""}`}>
        {hasChildren ? children : <p className="text-xs text-chc-slate italic">{empty || "—"}</p>}
      </div>
    </section>
  );
}

function CodeRow({ c }) {
  if (!c) return null;
  const verified = c.status === "verified";
  return (
    <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2 rounded-md border border-border px-4 py-3 bg-chc-mist/40">
      <div className="flex items-center gap-3 min-w-0">
        <span className="font-mono text-sm font-semibold px-2 py-0.5 rounded bg-white border border-border text-chc-navy">{c.code}</span>
        <div className="min-w-0">
          <p className="text-sm text-chc-ink truncate">{c.description}</p>
          <p className="text-[11px] text-chc-slate">{c.code_type} · {c.guideline_ref}</p>
          {c.note && <p className="text-[11px] text-amber-700">{c.note}</p>}
        </div>
      </div>
      <span className={`inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full border ${
        verified ? "bg-emerald-50 border-emerald-200 text-emerald-700" : "bg-amber-50 border-amber-200 text-amber-700"
      }`}>
        {verified ? <CheckCircle weight="fill" size={12} /> : <WarningCircle weight="fill" size={12} />}
        {verified ? "Verified" : "Review Suggested"}
      </span>
    </div>
  );
}
