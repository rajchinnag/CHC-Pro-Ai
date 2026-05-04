/**
 * CHC Pro AI – Upload Service (Layer 2)
 * Handles: presigned URL flow, context submission, history fetch.
 */
import axios from "axios";

const API = process.env.REACT_APP_API_URL || "http://localhost:8000";

const authHeader = () => {
  const token = localStorage.getItem("chc_access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
};

// ── Step 1: Initiate upload — get presigned S3 URL ────────────────────────────
export async function initiateUpload({ filename, fileFormat, fileSizeBytes }) {
  const res = await axios.post(
    `${API}/api/v1/upload/init`,
    {
      original_filename: filename,
      file_format: fileFormat,
      file_size_bytes: fileSizeBytes,
    },
    { headers: authHeader() }
  );
  return res.data; // { upload_id, presigned_url, s3_key, expires_in }
}

// ── Step 2: PUT file directly to S3 ──────────────────────────────────────────
export async function putFileToS3(presignedUrl, file, onProgress) {
  await axios.put(presignedUrl, file, {
    headers: { "Content-Type": file.type },
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    },
  });
}

// ── Step 3: Confirm upload received ──────────────────────────────────────────
export async function confirmUpload(uploadId) {
  const res = await axios.post(
    `${API}/api/v1/upload/confirm`,
    { upload_id: uploadId },
    { headers: authHeader() }
  );
  return res.data; // { upload_id, status, message }
}

// ── Step 4: Submit context form ───────────────────────────────────────────────
export async function submitContext(contextData) {
  const res = await axios.post(
    `${API}/api/v1/upload/context`,
    contextData,
    { headers: authHeader() }
  );
  return res.data; // { context_id, upload_id, status, message }
}

// ── Full upload flow (convenience wrapper) ────────────────────────────────────
export async function uploadFile(file, onProgress) {
  const fileFormat = detectFormat(file);

  // 1. Get presigned URL
  const { upload_id, presigned_url } = await initiateUpload({
    filename: file.name,
    fileFormat,
    fileSizeBytes: file.size,
  });

  // 2. PUT to S3
  await putFileToS3(presigned_url, file, onProgress);

  // 3. Confirm
  await confirmUpload(upload_id);

  return upload_id;
}

// ── History ───────────────────────────────────────────────────────────────────
export async function getUploadHistory(page = 1, pageSize = 20) {
  const res = await axios.get(`${API}/api/v1/upload/history`, {
    headers: authHeader(),
    params: { page, page_size: pageSize },
  });
  return res.data; // { uploads, total, page, page_size }
}

export async function getUploadDetail(uploadId) {
  const res = await axios.get(`${API}/api/v1/upload/${uploadId}`, {
    headers: authHeader(),
  });
  return res.data;
}

export async function deleteUpload(uploadId) {
  await axios.delete(`${API}/api/v1/upload/${uploadId}`, {
    headers: authHeader(),
  });
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function detectFormat(file) {
  const name = file.name.toLowerCase();
  const type = file.type.toLowerCase();

  if (type === "application/pdf" || name.endsWith(".pdf")) return "pdf";
  if (type.startsWith("image/")) return "image";
  if (name.endsWith(".hl7") || name.endsWith(".hl7v2")) return "hl7";
  if (
    name.endsWith(".json") ||
    type === "application/fhir+json" ||
    type === "application/json"
  )
    return "fhir";

  return "pdf"; // default
}

export const SPECIALTIES = [
  "Internal Medicine", "Family Medicine", "Emergency Medicine",
  "Cardiology", "Orthopedics", "Neurology", "Oncology",
  "Radiology", "Anesthesiology", "Surgery - General",
  "Surgery - Orthopedic", "Surgery - Cardiothoracic",
  "Obstetrics & Gynecology", "Pediatrics", "Psychiatry",
  "Dermatology", "Ophthalmology", "ENT", "Urology",
  "Nephrology", "Gastroenterology", "Pulmonology",
  "Rheumatology", "Endocrinology", "Hematology",
  "Infectious Disease", "Physical Medicine & Rehabilitation",
  "Hospital Medicine", "Critical Care", "Other",
];

export const PAYER_TYPES = [
  { value: "medicare", label: "Medicare" },
  { value: "medicaid", label: "Medicaid" },
  { value: "commercial", label: "Commercial" },
  { value: "tricare", label: "TRICARE" },
  { value: "va", label: "VA" },
];

export const CLAIM_FORMS = [
  { value: "cms1500", label: "CMS-1500 (Professional)" },
  { value: "ub04", label: "UB-04 (Institutional)" },
];

export const CODE_SETS = [
  { value: "ICD10CM", label: "ICD-10-CM (Diagnoses)" },
  { value: "ICD10PCS", label: "ICD-10-PCS (Procedures - Inpatient)" },
  { value: "CPT", label: "CPT (Procedures - Outpatient)" },
  { value: "HCPCS", label: "HCPCS Level II" },
  { value: "DRG", label: "MS-DRG (Inpatient)" },
];

export const US_STATES = [
  "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA",
  "HI","ID","IL","IN","IA","KS","KY","LA","ME","MD",
  "MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
  "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC",
  "SD","TN","TX","UT","VT","VA","WA","WV","WI","WY","DC",
];
