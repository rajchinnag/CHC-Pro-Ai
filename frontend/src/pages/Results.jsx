import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../services/authService";
import { CheckCircle, AlertTriangle, Download, RefreshCw, FilePlus, ShieldCheck, FileText } from "lucide-react";

export default function ResultsPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async () => {
    try {
      const { data } = await api.get(`/v1/upload/${id}/coding`);
      setSession(data);
    } catch (e) {
      setError(e.message || "Failed to load results.");
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => { load(); }, [id]);

  const rerun = async () => {
    setLoading(true);
    await load();
  };

  const exportPDF = async () => {
    try {
      const token = sessionStorage.getItem("chc_access_token");
      const res = await fetch(
        `${process.env.REACT_APP_API_BASE_URL}/api/v1/upload/${id}/coding/pdf`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!res.ok) throw new Error("PDF export failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `chc-codes-${id.slice(0, 8)}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error(e);
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
    const csv = rows.map((row) => row.map((x) => `"${x ?? ""}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `chc-codes-${id.slice(0, 8)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (loading) return <div style={styles.loading}>Loading results…</div>;
  if (error)   return <div style={styles.error}>{error}</div>;
  if (!session) return <div style={styles.loading}>Session not found.</div>;

  const r = session.coding_result;
  const phi = session.phi_report || {};
  const ctx = session.context || {};
  const totalRedactions = Object.values(phi.redactions || {}).reduce((a, b) => a + b, 0);

  return (
    <div style={styles.page}>
      <div style={styles.container}>
        {/* Header */}
        <div style={styles.header}>
          <div>
            <p style={styles.eyebrow}>Coding results</p>
            <h1 style={styles.title}>
              {session.original_filename}{" "}
              <span style={styles.idBadge}>{id.slice(0, 8)}</span>
            </h1>
            <p style={styles.meta}>
              {ctx.claim_form?.toUpperCase()} · {ctx.payer_name} · {ctx.specialty}
            </p>
          </div>
          <div style={styles.btnRow}>
            <button onClick={exportPDF} style={styles.btnSecondary}>
              <FileText size={14} style={{ marginRight: 4 }} /> PDF
            </button>
            <button onClick={exportCSV} style={styles.btnSecondary}>
              <Download size={14} style={{ marginRight: 4 }} /> CSV
            </button>
            <button onClick={rerun} style={styles.btnSecondary}>
              <RefreshCw size={14} style={{ marginRight: 4 }} /> Refresh
            </button>
            <button onClick={() => navigate("/upload")} style={styles.btnPrimary}>
              <FilePlus size={14} style={{ marginRight: 4 }} /> New Upload
            </button>
          </div>
        </div>

        {/* PHI report */}
        <div style={styles.phiBanner}>
          <ShieldCheck size={20} color="#059669" style={{ flexShrink: 0 }} />
          <div style={{ flex: 1 }}>
            <p style={styles.phiTitle}>
              PHI successfully removed · {totalRedactions} identifiers redacted
            </p>
            <p style={styles.phiSub}>
              Categories: {(phi.categories_found || []).join(" · ") || "none detected"} · Pages: {session.page_count ?? "—"}
            </p>
          </div>
        </div>

        {/* Status */}
        {session.status !== "coding_complete" && (
          <div style={styles.statusBox}>
            <p style={styles.statusText}>
              Status: <strong>{session.status?.replace(/_/g, " ")}</strong>
              {session.status === "error" && session.error_message
                ? ` — ${session.error_message}`
                : " — processing in progress, refresh in a moment."}
            </p>
          </div>
        )}

        {/* Results */}
        {r ? (
          <div style={styles.resultsGrid}>
            <div style={styles.mainCol}>
              <Section title="Principal diagnosis (ICD-10-CM)">
                <CodeRow c={r.principal_diagnosis} />
              </Section>
              <Section title="Secondary diagnoses" empty="No secondary diagnoses matched.">
                {(r.secondary_diagnoses || []).map((c, i) => <CodeRow key={c.code + i} c={c} />)}
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
              {ctx.claim_form === "ub04" && (
                <>
                  <Section title="Revenue codes" empty="None matched.">
                    {(r.revenue_codes || []).map((c) => <CodeRow key={c.code} c={c} />)}
                  </Section>
                  <Section title="Condition codes" empty="None matched.">
                    {(r.condition_codes || []).map((c) => <CodeRow key={c.code} c={c} />)}
                  </Section>
                </>
              )}
              {(r.modifiers || []).length > 0 && (
                <Section title="Modifiers">
                  {r.modifiers.map((c) => <CodeRow key={c.code} c={c} />)}
                </Section>
              )}
            </div>
            <div style={styles.sideCol}>
              <Section title="Processing log">
                <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
                  {(r.processing_log || []).map((l, i) => (
                    <li key={i} style={styles.logItem}>
                      <CheckCircle size={14} color="#3b82f6" style={{ flexShrink: 0, marginTop: 2 }} />
                      <span style={styles.logText}>{l}</span>
                    </li>
                  ))}
                </ul>
              </Section>
              {(r.mue_checks || []).length > 0 && (
                <Section title="MUE edits">
                  <ul style={{ listStyle: "none", padding: 0 }}>
                    {r.mue_checks.map((m, i) => <li key={i} style={styles.editItem}>• {m}</li>)}
                  </ul>
                </Section>
              )}
              {(r.ncci_checks || []).length > 0 && (
                <Section title="NCCI edits">
                  <ul style={{ listStyle: "none", padding: 0 }}>
                    {r.ncci_checks.map((m, i) => <li key={i} style={styles.editItem}>• {m}</li>)}
                  </ul>
                </Section>
              )}
            </div>
          </div>
        ) : (
          <div style={styles.noResult}>
            {session.status === "error"
              ? `Error: ${session.error_message || "Unknown error occurred."}`
              : "Coding is in progress. This page will refresh automatically."}
          </div>
        )}
      </div>
    </div>
  );
}

const styles = {
  page:       { minHeight: "100vh", background: "#f0f4f8", padding: "32px 24px" },
  container:  { maxWidth: 1200, margin: "0 auto" },
  header:     { display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20, flexWrap: "wrap", gap: 16 },
  eyebrow:    { fontSize: 11, textTransform: "uppercase", letterSpacing: "0.2em", color: "#64748b", margin: "0 0 4px" },
  title:      { fontSize: 22, fontWeight: 700, color: "#1e293b", margin: "0 0 4px" },
  idBadge:    { fontFamily: "monospace", fontSize: 16, color: "#003F87" },
  meta:       { fontSize: 13, color: "#64748b", margin: 0 },
  btnRow:     { display: "flex", gap: 8, flexWrap: "wrap" },
  btnPrimary: { display: "flex", alignItems: "center", padding: "8px 14px", background: "#003F87", color: "#fff", border: "none", borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: "pointer" },
  btnSecondary:{ display: "flex", alignItems: "center", padding: "8px 14px", background: "#fff", color: "#003F87", border: "1px solid #cbd5e1", borderRadius: 8, fontSize: 13, cursor: "pointer" },
  phiBanner:  { display: "flex", alignItems: "flex-start", gap: 12, background: "#ecfdf5", border: "1px solid #a7f3d0", borderRadius: 10, padding: "12px 16px", marginBottom: 16 },
  phiTitle:   { fontWeight: 600, color: "#065f46", fontSize: 14, margin: "0 0 2px" },
  phiSub:     { fontSize: 12, color: "#047857", margin: 0 },
  statusBox:  { background: "#ede9fe", border: "1px solid #c4b5fd", borderRadius: 10, padding: "12px 16px", marginBottom: 16 },
  statusText: { fontSize: 14, color: "#5b21b6", margin: 0 },
  resultsGrid:{ display: "grid", gridTemplateColumns: "1fr minmax(0, 320px)", gap: 20 },
  mainCol:    { display: "flex", flexDirection: "column", gap: 16 },
  sideCol:    { display: "flex", flexDirection: "column", gap: 16 },
  noResult:   { background: "#fff", borderRadius: 10, border: "1px solid #e2e8f0", padding: 24, fontSize: 14, color: "#64748b" },
  loading:    { textAlign: "center", padding: 48, fontSize: 14, color: "#64748b" },
  error:      { margin: 24, padding: "12px 16px", background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 8, color: "#dc2626", fontSize: 14 },
  logItem:    { display: "flex", alignItems: "flex-start", gap: 8, marginBottom: 6 },
  logText:    { fontFamily: "monospace", fontSize: 12, color: "#1e293b" },
  editItem:   { fontFamily: "monospace", fontSize: 12, color: "#1e293b", marginBottom: 4 },
};

function Section({ title, children, empty }) {
  const hasChildren = React.Children.toArray(children).some((c) => c !== null && c !== undefined && c !== false);
  return (
    <section style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: 10, overflow: "hidden" }}>
      <header style={{ borderBottom: "1px solid #e2e8f0", padding: "10px 16px" }}>
        <h3 style={{ fontSize: 13, fontWeight: 600, color: "#1e293b", margin: 0 }}>{title}</h3>
      </header>
      <div style={{ padding: "12px 16px", display: "flex", flexDirection: "column", gap: 8 }}>
        {hasChildren ? children : <p style={{ fontSize: 12, color: "#94a3b8", fontStyle: "italic", margin: 0 }}>{empty || "—"}</p>}
      </div>
    </section>
  );
}

function CodeRow({ c }) {
  if (!c) return null;
  const verified = c.status === "verified";
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 8, padding: "10px 14px", flexWrap: "wrap" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, minWidth: 0 }}>
        <span style={{ fontFamily: "monospace", fontSize: 14, fontWeight: 700, padding: "2px 8px", background: "#fff", border: "1px solid #e2e8f0", borderRadius: 6, color: "#003F87", flexShrink: 0 }}>
          {c.code}
        </span>
        <div style={{ minWidth: 0 }}>
          <p style={{ fontSize: 13, color: "#1e293b", margin: "0 0 2px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{c.description}</p>
          <p style={{ fontSize: 11, color: "#64748b", margin: 0 }}>{c.code_type} · {c.guideline_ref}</p>
          {c.note && <p style={{ fontSize: 11, color: "#b45309", margin: "2px 0 0" }}>{c.note}</p>}
        </div>
      </div>
      <span style={{
        display: "inline-flex", alignItems: "center", gap: 4, fontSize: 11, fontWeight: 600,
        padding: "3px 10px", borderRadius: 99,
        background: verified ? "#ecfdf5" : "#fffbeb",
        border: `1px solid ${verified ? "#a7f3d0" : "#fde68a"}`,
        color: verified ? "#065f46" : "#92400e",
        flexShrink: 0,
      }}>
        {verified
          ? <CheckCircle size={12} color="#059669" />
          : <AlertTriangle size={12} color="#d97706" />}
        {verified ? "Verified" : "Review"}
      </span>
    </div>
  );
}
