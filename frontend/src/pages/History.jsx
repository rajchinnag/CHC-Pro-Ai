import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getUploadHistory, deleteUpload } from "../services/uploadService";

const STATUS_COLORS = {
  pending:          { bg: "#fef3c7", color: "#92400e" },
  uploaded:         { bg: "#dbeafe", color: "#1e40af" },
  context_complete: { bg: "#e0e7ff", color: "#3730a3" },
  ocr_complete:     { bg: "#d1fae5", color: "#065f46" },
  phi_purged:       { bg: "#d1fae5", color: "#065f46" },
  phi_verified:     { bg: "#d1fae5", color: "#065f46" },
  ready:            { bg: "#d1fae5", color: "#065f46" },
  coding_complete:  { bg: "#dcfce7", color: "#14532d" },
  error:            { bg: "#fee2e2", color: "#991b1b" },
};

function StatusBadge({ status }) {
  const c = STATUS_COLORS[status] || { bg: "#f1f5f9", color: "#475569" };
  return (
    <span style={{ ...styles.badge, background: c.bg, color: c.color }}>
      {status.replace(/_/g, " ")}
    </span>
  );
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit",
  });
}

export default function History() {
  const navigate = useNavigate();
  const [uploads, setUploads] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deletingId, setDeletingId] = useState(null);

  const PAGE_SIZE = 10;

  async function load(p = 1) {
    setLoading(true);
    setError("");
    try {
      const data = await getUploadHistory(p, PAGE_SIZE);
      setUploads(data.uploads);
      setTotal(data.total);
      setPage(p);
    } catch (e) {
      setError("Failed to load upload history.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(1); }, []);

  async function handleDelete(uploadId) {
    if (!window.confirm("Delete this upload? This cannot be undone.")) return;
    setDeletingId(uploadId);
    try {
      await deleteUpload(uploadId);
      load(page);
    } catch (e) {
      setError(e.response?.data?.detail || "Delete failed.");
    } finally {
      setDeletingId(null);
    }
  }

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div style={styles.page}>
      <div style={styles.container}>
        {/* Header */}
        <div style={styles.header}>
          <div>
            <h1 style={styles.title}>Upload History</h1>
            <p style={styles.subtitle}>{total} record{total !== 1 ? "s" : ""} uploaded</p>
          </div>
          <button style={styles.newBtn} onClick={() => navigate("/upload")}>
            + New Upload
          </button>
        </div>

        {error && <div style={styles.error}>{error}</div>}

        {loading ? (
          <div style={styles.loading}>Loading…</div>
        ) : uploads.length === 0 ? (
          <div style={styles.empty}>
            <div style={styles.emptyIcon}>📂</div>
            <div style={styles.emptyTitle}>No uploads yet</div>
            <div style={styles.emptySub}>Upload your first medical record to get started.</div>
            <button style={styles.newBtn} onClick={() => navigate("/upload")}>Upload Now</button>
          </div>
        ) : (
          <>
            <div style={styles.table}>
              {/* Table header */}
              <div style={styles.tableHeader}>
                <span style={{ flex: 3 }}>File</span>
                <span style={{ flex: 1 }}>Format</span>
                <span style={{ flex: 1 }}>Size</span>
                <span style={{ flex: 1.5 }}>Specialty</span>
                <span style={{ flex: 1.5 }}>Payer</span>
                <span style={{ flex: 1.5 }}>Status</span>
                <span style={{ flex: 1.5 }}>Uploaded</span>
                <span style={{ flex: 1 }}>Actions</span>
              </div>

              {/* Rows */}
              {uploads.map(u => (
                <div key={u.upload_id} style={styles.tableRow}>
                  <span style={{ flex: 3, fontWeight: 600, color: "#1e293b", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {u.original_filename}
                  </span>
                  <span style={{ flex: 1, textTransform: "uppercase", fontSize: 12, color: "#64748b" }}>{u.file_format}</span>
                  <span style={{ flex: 1, fontSize: 13, color: "#64748b" }}>{formatBytes(u.file_size_bytes)}</span>
                  <span style={{ flex: 1.5, fontSize: 13, color: "#374151" }}>{u.specialty || "—"}</span>
                  <span style={{ flex: 1.5, fontSize: 13, color: "#374151" }}>{u.payer_name || "—"}</span>
                  <span style={{ flex: 1.5 }}><StatusBadge status={u.status} /></span>
                  <span style={{ flex: 1.5, fontSize: 12, color: "#64748b" }}>{formatDate(u.created_at)}</span>
                  <span style={{ flex: 1, display: "flex", gap: 8 }}>
                    {u.status === "ready" || u.status === "coding_complete" ? (
                      <button style={styles.actionBtn} onClick={() => navigate(`/results/${u.upload_id}`)}>
                        View
                      </button>
                    ) : !u.has_context && u.status === "uploaded" ? (
                      <button style={styles.actionBtn} onClick={() => navigate("/upload", { state: { upload_id: u.upload_id, step: 1 } })}>
                        Add Context
                      </button>
                    ) : null}
                    {["pending", "uploaded", "error"].includes(u.status) && (
                      <button
                        style={{ ...styles.actionBtn, color: "#dc2626", borderColor: "#fecaca" }}
                        disabled={deletingId === u.upload_id}
                        onClick={() => handleDelete(u.upload_id)}
                      >
                        {deletingId === u.upload_id ? "…" : "Del"}
                      </button>
                    )}
                  </span>
                </div>
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div style={styles.pagination}>
                <button style={styles.pageBtn} disabled={page === 1} onClick={() => load(page - 1)}>← Prev</button>
                <span style={styles.pageInfo}>Page {page} of {totalPages}</span>
                <button style={styles.pageBtn} disabled={page === totalPages} onClick={() => load(page + 1)}>Next →</button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

const styles = {
  page: { minHeight: "100vh", background: "#f0f4f8", padding: "32px 24px" },
  container: { maxWidth: 1100, margin: "0 auto" },
  header: { display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 24 },
  title: { margin: 0, fontSize: 24, fontWeight: 700, color: "#1e293b" },
  subtitle: { margin: "4px 0 0", fontSize: 14, color: "#64748b" },
  newBtn: { padding: "10px 20px", background: "#003F87", color: "#fff", border: "none", borderRadius: 8, fontSize: 14, fontWeight: 600, cursor: "pointer" },
  error: { padding: "12px 16px", background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 8, color: "#dc2626", fontSize: 14, marginBottom: 16 },
  loading: { textAlign: "center", padding: 48, color: "#64748b" },
  empty: { textAlign: "center", padding: 64, background: "#fff", borderRadius: 16 },
  emptyIcon: { fontSize: 48, marginBottom: 16 },
  emptyTitle: { fontSize: 18, fontWeight: 700, color: "#1e293b", marginBottom: 8 },
  emptySub: { fontSize: 14, color: "#64748b", marginBottom: 24 },
  table: { background: "#fff", borderRadius: 12, overflow: "hidden", boxShadow: "0 1px 4px rgba(0,0,0,0.06)" },
  tableHeader: { display: "flex", padding: "12px 20px", background: "#f8fafc", borderBottom: "1px solid #e2e8f0", fontSize: 12, fontWeight: 700, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.05em" },
  tableRow: { display: "flex", padding: "14px 20px", borderBottom: "1px solid #f1f5f9", alignItems: "center", fontSize: 14, transition: "background 0.15s" },
  badge: { padding: "3px 10px", borderRadius: 99, fontSize: 11, fontWeight: 700, textTransform: "capitalize" },
  actionBtn: { padding: "4px 10px", border: "1px solid #cbd5e1", borderRadius: 6, fontSize: 12, fontWeight: 600, cursor: "pointer", background: "transparent", color: "#003F87" },
  pagination: { display: "flex", justifyContent: "center", alignItems: "center", gap: 16, padding: "20px 0" },
  pageBtn: { padding: "8px 16px", border: "1px solid #cbd5e1", borderRadius: 8, fontSize: 14, cursor: "pointer", background: "#fff" },
  pageInfo: { fontSize: 14, color: "#64748b" },
};
