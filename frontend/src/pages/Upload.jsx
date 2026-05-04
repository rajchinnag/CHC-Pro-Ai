import React, { useState, useCallback, useRef } from "react";
import { useNavigate } from "react-router-dom";
import {
  uploadFile, submitContext,
  SPECIALTIES, PAYER_TYPES, CLAIM_FORMS, CODE_SETS, US_STATES,
} from "../services/uploadService";

const STEPS = ["Upload File", "Clinical Context", "Review & Submit"];

export default function Upload() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  const [step, setStep] = useState(0);
  const [dragging, setDragging] = useState(false);
  const [file, setFile] = useState(null);
  const [uploadId, setUploadId] = useState(null);
  const [progress, setProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const [ctx, setCtx] = useState({
    specialty: "",
    payer_name: "",
    payer_type: "",
    state: "",
    claim_form: "",
    code_sets: [],
    visit_date: "",
    patient_dob_year: "",
    notes: "",
  });

  // ── Drag & Drop ─────────────────────────────────────────────────────────────
  const onDragOver = useCallback((e) => { e.preventDefault(); setDragging(true); }, []);
  const onDragLeave = useCallback(() => setDragging(false), []);
  const onDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) validateAndSetFile(dropped);
  }, []);

  function validateAndSetFile(f) {
    setError("");
    if (f.size > 52_428_800) { setError("File too large. Max 50 MB."); return; }
    const allowed = ["application/pdf", "image/jpeg", "image/png", "image/tiff",
                     "application/json", "text/plain"];
    if (!allowed.includes(f.type) && !f.name.endsWith(".hl7")) {
      setError("Unsupported format. Accepted: PDF, JPG, PNG, TIFF, HL7, FHIR JSON.");
      return;
    }
    setFile(f);
  }

  // ── Step 0: Upload file to S3 ────────────────────────────────────────────────
  async function handleUpload() {
    if (!file) return;
    setUploading(true);
    setError("");
    try {
      const id = await uploadFile(file, setProgress);
      setUploadId(id);
      setStep(1);
    } catch (e) {
      setError(e.response?.data?.detail || "Upload failed. Try again.");
    } finally {
      setUploading(false);
    }
  }

  // ── Step 1: Context form change ──────────────────────────────────────────────
  function handleCtxChange(field, value) {
    setCtx(prev => ({ ...prev, [field]: value }));
  }

  function toggleCodeSet(val) {
    setCtx(prev => ({
      ...prev,
      code_sets: prev.code_sets.includes(val)
        ? prev.code_sets.filter(c => c !== val)
        : [...prev.code_sets, val],
    }));
  }

  function ctxValid() {
    return ctx.specialty && ctx.payer_name && ctx.payer_type &&
           ctx.state && ctx.claim_form && ctx.code_sets.length > 0;
  }

  // ── Step 2: Submit ────────────────────────────────────────────────────────────
  async function handleSubmit() {
    setSubmitting(true);
    setError("");
    try {
      await submitContext({
        upload_id: uploadId,
        ...ctx,
        visit_date: ctx.visit_date || undefined,
        patient_dob_year: ctx.patient_dob_year ? parseInt(ctx.patient_dob_year) : undefined,
        notes: ctx.notes || undefined,
      });
      navigate("/history");
    } catch (e) {
      setError(e.response?.data?.detail || "Submission failed. Try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        {/* Header */}
        <div style={styles.header}>
          <h1 style={styles.title}>Medical Record Upload</h1>
          <p style={styles.subtitle}>Secure · HIPAA-compliant · PHI-purged before processing</p>
        </div>

        {/* Stepper */}
        <div style={styles.stepper}>
          {STEPS.map((s, i) => (
            <div key={i} style={styles.stepItem}>
              <div style={{
                ...styles.stepCircle,
                background: i < step ? "#10b981" : i === step ? "#003F87" : "#e2e8f0",
                color: i <= step ? "#fff" : "#94a3b8",
              }}>
                {i < step ? "✓" : i + 1}
              </div>
              <span style={{ ...styles.stepLabel, color: i === step ? "#003F87" : "#94a3b8" }}>{s}</span>
              {i < STEPS.length - 1 && <div style={styles.stepLine} />}
            </div>
          ))}
        </div>

        {error && <div style={styles.error}>{error}</div>}

        {/* ── Step 0: Drop zone ── */}
        {step === 0 && (
          <div style={styles.section}>
            <div
              style={{ ...styles.dropzone, ...(dragging ? styles.dropzoneActive : {}) }}
              onDragOver={onDragOver}
              onDragLeave={onDragLeave}
              onDrop={onDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                style={{ display: "none" }}
                accept=".pdf,.jpg,.jpeg,.png,.tiff,.json,.hl7"
                onChange={e => validateAndSetFile(e.target.files[0])}
              />
              <div style={styles.dropIcon}>📄</div>
              {file ? (
                <div>
                  <div style={styles.fileName}>{file.name}</div>
                  <div style={styles.fileSize}>{(file.size / 1024 / 1024).toFixed(2)} MB</div>
                </div>
              ) : (
                <div>
                  <div style={styles.dropText}>Drop your medical record here</div>
                  <div style={styles.dropSub}>PDF, JPG, PNG, TIFF, HL7, FHIR JSON · Max 50 MB</div>
                </div>
              )}
            </div>

            {uploading && (
              <div style={styles.progressWrap}>
                <div style={styles.progressBar}>
                  <div style={{ ...styles.progressFill, width: `${progress}%` }} />
                </div>
                <div style={styles.progressText}>{progress}% — Uploading securely…</div>
              </div>
            )}

            <button
              style={{ ...styles.btn, opacity: (!file || uploading) ? 0.5 : 1 }}
              disabled={!file || uploading}
              onClick={handleUpload}
            >
              {uploading ? "Uploading…" : "Upload Securely →"}
            </button>

            <div style={styles.hipaaNote}>
              🔒 Files are encrypted in transit and at rest. PHI is purged before AI processing.
            </div>
          </div>
        )}

        {/* ── Step 1: Context form ── */}
        {step === 1 && (
          <div style={styles.section}>
            <h2 style={styles.sectionTitle}>Clinical Context</h2>
            <p style={styles.sectionSub}>Tell us what codes are needed so we apply the correct guidelines.</p>

            <div style={styles.grid2}>
              <div style={styles.field}>
                <label style={styles.label}>Specialty *</label>
                <select style={styles.input} value={ctx.specialty}
                  onChange={e => handleCtxChange("specialty", e.target.value)}>
                  <option value="">Select specialty</option>
                  {SPECIALTIES.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>

              <div style={styles.field}>
                <label style={styles.label}>State *</label>
                <select style={styles.input} value={ctx.state}
                  onChange={e => handleCtxChange("state", e.target.value)}>
                  <option value="">Select state</option>
                  {US_STATES.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>

              <div style={styles.field}>
                <label style={styles.label}>Payer Type *</label>
                <select style={styles.input} value={ctx.payer_type}
                  onChange={e => handleCtxChange("payer_type", e.target.value)}>
                  <option value="">Select payer type</option>
                  {PAYER_TYPES.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
                </select>
              </div>

              <div style={styles.field}>
                <label style={styles.label}>Payer Name *</label>
                <input style={styles.input} placeholder="e.g. Blue Cross Blue Shield"
                  value={ctx.payer_name}
                  onChange={e => handleCtxChange("payer_name", e.target.value)} />
              </div>

              <div style={styles.field}>
                <label style={styles.label}>Claim Form *</label>
                <select style={styles.input} value={ctx.claim_form}
                  onChange={e => handleCtxChange("claim_form", e.target.value)}>
                  <option value="">Select form</option>
                  {CLAIM_FORMS.map(f => <option key={f.value} value={f.value}>{f.label}</option>)}
                </select>
              </div>

              <div style={styles.field}>
                <label style={styles.label}>Visit Date</label>
                <input type="date" style={styles.input} value={ctx.visit_date}
                  onChange={e => handleCtxChange("visit_date", e.target.value)} />
              </div>
            </div>

            <div style={styles.field}>
              <label style={styles.label}>Code Sets Needed *</label>
              <div style={styles.checkGroup}>
                {CODE_SETS.map(c => (
                  <label key={c.value} style={styles.checkLabel}>
                    <input type="checkbox" checked={ctx.code_sets.includes(c.value)}
                      onChange={() => toggleCodeSet(c.value)} style={{ marginRight: 8 }} />
                    {c.label}
                  </label>
                ))}
              </div>
            </div>

            <div style={styles.field}>
              <label style={styles.label}>Additional Notes</label>
              <textarea style={{ ...styles.input, height: 80, resize: "vertical" }}
                placeholder="Any additional context for the coding engine…"
                value={ctx.notes}
                onChange={e => handleCtxChange("notes", e.target.value)} />
            </div>

            <div style={styles.btnRow}>
              <button style={styles.btnSecondary} onClick={() => setStep(0)}>← Back</button>
              <button style={{ ...styles.btn, opacity: ctxValid() ? 1 : 0.5 }}
                disabled={!ctxValid()} onClick={() => setStep(2)}>
                Review →
              </button>
            </div>
          </div>
        )}

        {/* ── Step 2: Review ── */}
        {step === 2 && (
          <div style={styles.section}>
            <h2 style={styles.sectionTitle}>Review & Submit</h2>

            <div style={styles.reviewCard}>
              <div style={styles.reviewRow}><span style={styles.reviewKey}>File</span><span>{file?.name}</span></div>
              <div style={styles.reviewRow}><span style={styles.reviewKey}>Specialty</span><span>{ctx.specialty}</span></div>
              <div style={styles.reviewRow}><span style={styles.reviewKey}>Payer</span><span>{ctx.payer_name} ({ctx.payer_type})</span></div>
              <div style={styles.reviewRow}><span style={styles.reviewKey}>State</span><span>{ctx.state}</span></div>
              <div style={styles.reviewRow}><span style={styles.reviewKey}>Claim Form</span><span>{ctx.claim_form?.toUpperCase()}</span></div>
              <div style={styles.reviewRow}><span style={styles.reviewKey}>Code Sets</span><span>{ctx.code_sets.join(", ")}</span></div>
              {ctx.visit_date && <div style={styles.reviewRow}><span style={styles.reviewKey}>Visit Date</span><span>{ctx.visit_date}</span></div>}
              {ctx.notes && <div style={styles.reviewRow}><span style={styles.reviewKey}>Notes</span><span>{ctx.notes}</span></div>}
            </div>

            <div style={styles.hipaaNote}>
              By submitting, you confirm this record has been authorized for AI-assisted coding under your signed HIPAA BAA.
            </div>

            <div style={styles.btnRow}>
              <button style={styles.btnSecondary} onClick={() => setStep(1)}>← Edit</button>
              <button style={{ ...styles.btn, opacity: submitting ? 0.5 : 1 }}
                disabled={submitting} onClick={handleSubmit}>
                {submitting ? "Submitting…" : "Submit for Coding ✓"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

const styles = {
  page: { minHeight: "100vh", background: "#f0f4f8", display: "flex", alignItems: "flex-start", justifyContent: "center", padding: "40px 16px" },
  card: { background: "#fff", borderRadius: 16, boxShadow: "0 4px 24px rgba(0,0,0,0.08)", width: "100%", maxWidth: 720, overflow: "hidden" },
  header: { background: "linear-gradient(135deg, #003F87 0%, #0066cc 100%)", padding: "32px 40px", color: "#fff" },
  title: { margin: 0, fontSize: 24, fontWeight: 700, fontFamily: "'IBM Plex Sans', sans-serif" },
  subtitle: { margin: "8px 0 0", fontSize: 14, opacity: 0.8 },
  stepper: { display: "flex", alignItems: "center", padding: "24px 40px", borderBottom: "1px solid #e2e8f0" },
  stepItem: { display: "flex", alignItems: "center", flex: 1 },
  stepCircle: { width: 28, height: 28, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13, fontWeight: 700, flexShrink: 0 },
  stepLabel: { fontSize: 12, fontWeight: 600, marginLeft: 8, whiteSpace: "nowrap" },
  stepLine: { flex: 1, height: 2, background: "#e2e8f0", margin: "0 8px" },
  section: { padding: "32px 40px" },
  sectionTitle: { margin: "0 0 8px", fontSize: 20, fontWeight: 700, color: "#1e293b" },
  sectionSub: { margin: "0 0 24px", fontSize: 14, color: "#64748b" },
  dropzone: { border: "2px dashed #cbd5e1", borderRadius: 12, padding: "48px 24px", textAlign: "center", cursor: "pointer", transition: "all 0.2s", marginBottom: 24 },
  dropzoneActive: { borderColor: "#003F87", background: "#eff6ff" },
  dropIcon: { fontSize: 48, marginBottom: 16 },
  dropText: { fontSize: 16, fontWeight: 600, color: "#1e293b", marginBottom: 8 },
  dropSub: { fontSize: 13, color: "#64748b" },
  fileName: { fontSize: 15, fontWeight: 600, color: "#003F87" },
  fileSize: { fontSize: 13, color: "#64748b", marginTop: 4 },
  progressWrap: { marginBottom: 20 },
  progressBar: { height: 6, background: "#e2e8f0", borderRadius: 3, overflow: "hidden", marginBottom: 8 },
  progressFill: { height: "100%", background: "#003F87", borderRadius: 3, transition: "width 0.3s" },
  progressText: { fontSize: 13, color: "#64748b", textAlign: "center" },
  btn: { width: "100%", padding: "14px", background: "#003F87", color: "#fff", border: "none", borderRadius: 8, fontSize: 15, fontWeight: 700, cursor: "pointer", transition: "opacity 0.2s" },
  btnSecondary: { padding: "14px 24px", background: "transparent", color: "#003F87", border: "2px solid #003F87", borderRadius: 8, fontSize: 14, fontWeight: 600, cursor: "pointer" },
  btnRow: { display: "flex", gap: 12, marginTop: 24 },
  hipaaNote: { fontSize: 12, color: "#64748b", textAlign: "center", marginTop: 16, padding: "12px", background: "#f8fafc", borderRadius: 8 },
  error: { margin: "0 40px 16px", padding: "12px 16px", background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 8, color: "#dc2626", fontSize: 14 },
  grid2: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 },
  field: { marginBottom: 16 },
  label: { display: "block", fontSize: 13, fontWeight: 600, color: "#374151", marginBottom: 6 },
  input: { width: "100%", padding: "10px 12px", border: "1px solid #d1d5db", borderRadius: 8, fontSize: 14, color: "#1e293b", background: "#fff", boxSizing: "border-box" },
  checkGroup: { display: "flex", flexDirection: "column", gap: 10 },
  checkLabel: { fontSize: 14, color: "#374151", display: "flex", alignItems: "center", cursor: "pointer" },
  reviewCard: { background: "#f8fafc", borderRadius: 12, padding: 24, marginBottom: 24 },
  reviewRow: { display: "flex", justifyContent: "space-between", padding: "8px 0", borderBottom: "1px solid #e2e8f0", fontSize: 14 },
  reviewKey: { fontWeight: 600, color: "#64748b" },
};
