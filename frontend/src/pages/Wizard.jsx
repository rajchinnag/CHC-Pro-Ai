import React, { useMemo, useState, useCallback, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { api, formatApiError } from "@/lib/http";
import { toast } from "sonner";
import { FileText, Stethoscope, Building, CreditCard, Sparkle, CheckCircle, X, UploadSimple } from "@phosphor-icons/react";

const STEPS = [
  { key: "upload", label: "Upload" },
  { key: "claim", label: "Claim type" },
  { key: "codes", label: "Codes" },
  { key: "specialty", label: "Specialty" },
  { key: "payer", label: "Payer" },
  { key: "process", label: "Process" },
];

const SPECIALTIES = [
  "Internal Medicine","Cardiology","Orthopedics","Neurology","Oncology","Radiology","Emergency Medicine","Psychiatry","Obstetrics & Gynecology","Pediatrics","Urology","Gastroenterology","Pulmonology","Nephrology","Dermatology","General Surgery","Physical Therapy","Home Health","Skilled Nursing Facility","Hospice","Ambulance/Transport","Outpatient Surgery",
];

const CODE_OPTIONS = [
  { key: "ICD-10-CM", label: "ICD-10-CM (Diagnosis)" },
  { key: "ICD-10-PCS", label: "ICD-10-PCS (UB-04 only)" },
  { key: "CPT", label: "CPT Codes" },
  { key: "HCPCS", label: "HCPCS Level II" },
  { key: "MS-DRG", label: "MS-DRG / APR-DRG" },
  { key: "REVENUE", label: "Revenue Codes (UB-04)" },
  { key: "CONDITION", label: "Condition Codes (UB-04)" },
  { key: "OCCURRENCE", label: "Occurrence Codes" },
  { key: "VALUE", label: "Value Codes" },
];

const US_STATES = ["AL","AK","AZ","AR","CA","CO","CT","DE","DC","FL","GA","HI","ID","IL","IN","IA","KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT","VA","WA","WV","WI","WY"];

export default function WizardPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);

  const [files, setFiles] = useState([]);
  const [claimType, setClaimType] = useState("CMS-1500");
  const [allCodes, setAllCodes] = useState(true);
  const [codesRequired, setCodesRequired] = useState([]);
  const [specialty, setSpecialty] = useState([]);
  const [payer, setPayer] = useState("MEDICARE");
  const [state, setState] = useState("");

  const [processing, setProcessing] = useState(false);
  const [processSteps, setProcessSteps] = useState([]);
  const [sessionId, setSessionId] = useState(null);

  const dropRef = useRef(null);
  const inputRef = useRef(null);

  const onFiles = useCallback((fl) => {
    const arr = Array.from(fl).filter((f) => f.size <= 15 * 1024 * 1024);
    setFiles((prev) => [...prev, ...arr]);
  }, []);

  const onDrop = (e) => {
    e.preventDefault();
    dropRef.current?.classList.remove("ring-2", "ring-chc-blue");
    onFiles(e.dataTransfer.files);
  };
  const onDragOver = (e) => {
    e.preventDefault();
    dropRef.current?.classList.add("ring-2", "ring-chc-blue");
  };
  const onDragLeave = () => dropRef.current?.classList.remove("ring-2", "ring-chc-blue");

  const canNext = useMemo(() => {
    if (step === 0) return files.length > 0;
    if (step === 1) return !!claimType;
    if (step === 2) return allCodes || codesRequired.length > 0;
    if (step === 3) return specialty.length > 0;
    if (step === 4) return payer === "MEDICAID" ? !!state : true;
    return true;
  }, [step, files, claimType, allCodes, codesRequired, specialty, payer, state]);

  const run = async () => {
    setProcessing(true);
    const appendStep = (label) => setProcessSteps((prev) => [...prev, { label, done: false }]);
    const markDone = () => setProcessSteps((prev) => prev.map((s, i) => i === prev.length - 1 ? { ...s, done: true } : s));
    try {
      appendStep("Creating secure session…");
      const { data: s } = await api.post("/coding/sessions", {
        claim_type: claimType,
        codes_required: allCodes ? ["ALL"] : codesRequired,
        specialty,
        payer,
        state: payer === "MEDICAID" ? state : null,
      });
      markDone();

      appendStep(`Uploading ${files.length} document(s)…`);
      const fd = new FormData();
      files.forEach((f) => fd.append("files", f));
      await api.post(`/coding/sessions/${s.id}/upload`, fd, { headers: { "Content-Type": "multipart/form-data" } });
      markDone();

      appendStep("Reading medical records (OCR)…");
      appendStep("Purging Protected Health Information…");
      appendStep("Matching diagnoses & procedures to payer guidelines…");
      appendStep("Running MUE + NCCI edit checks…");

      const { data: result } = await api.post(`/coding/sessions/${s.id}/process`);
      setProcessSteps((prev) => prev.map((x) => ({ ...x, done: true })));
      setSessionId(s.id);
      toast.success("Coding complete.");
      setTimeout(() => navigate(`/app/results/${s.id}`), 700);
    } catch (err) {
      toast.error(formatApiError(err));
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="wizard-page">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-[11px] uppercase tracking-[0.25em] text-chc-slate">Guided workflow</p>
          <h1 className="mt-1 text-3xl font-semibold tracking-tight text-chc-ink">Medical Record Coding Wizard</h1>
        </div>
        <button onClick={() => navigate("/app/dashboard")} className="text-xs text-chc-slate hover:text-chc-ink" data-testid="wizard-cancel">Cancel</button>
      </div>

      <StepIndicator steps={STEPS} current={step} />

      <div className="rounded-md border border-border bg-white p-6 md:p-8 animate-fade-up" data-testid={`wizard-step-${STEPS[step].key}`}>
        {step === 0 && (
          <UploadStep dropRef={dropRef} inputRef={inputRef} files={files} setFiles={setFiles} onDrop={onDrop} onDragOver={onDragOver} onDragLeave={onDragLeave} onFiles={onFiles} />
        )}
        {step === 1 && (
          <ClaimTypeStep value={claimType} setValue={setClaimType} />
        )}
        {step === 2 && (
          <CodesStep allCodes={allCodes} setAllCodes={setAllCodes} codesRequired={codesRequired} setCodesRequired={setCodesRequired} claimType={claimType} />
        )}
        {step === 3 && (
          <SpecialtyStep specialty={specialty} setSpecialty={setSpecialty} />
        )}
        {step === 4 && (
          <PayerStep payer={payer} setPayer={setPayer} state={state} setState={setState} />
        )}
        {step === 5 && (
          <ProcessStep run={run} processing={processing} processSteps={processSteps} />
        )}
      </div>

      {step < 5 && (
        <div className="flex justify-between">
          <button
            disabled={step === 0}
            onClick={() => setStep((s) => Math.max(0, s - 1))}
            data-testid="wizard-back"
            className="rounded-md border border-border bg-white px-4 py-2 text-sm text-chc-ink hover:bg-slate-50 disabled:opacity-40"
          >
            ← Back
          </button>
          <button
            disabled={!canNext}
            onClick={() => setStep((s) => Math.min(STEPS.length - 1, s + 1))}
            data-testid="wizard-next"
            className="rounded-md bg-chc-navy px-5 py-2 text-sm font-medium text-white hover:bg-[#002f67] disabled:opacity-50"
          >
            {step === 4 ? "Review & Process" : "Continue"}
          </button>
        </div>
      )}
    </div>
  );
}

function StepIndicator({ steps, current }) {
  return (
    <ol className="grid grid-cols-3 md:grid-cols-6 gap-2" data-testid="wizard-stepper">
      {steps.map((s, i) => {
        const done = i < current, active = i === current;
        return (
          <li key={s.key} className="flex items-center gap-3">
            <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-semibold ${
              done ? "bg-chc-cyan text-white" : active ? "bg-chc-navy text-white" : "bg-slate-100 text-slate-400"
            }`}>
              {done ? <CheckCircle weight="fill" size={16} /> : i + 1}
            </div>
            <div className="min-w-0">
              <p className="text-[10px] uppercase tracking-widest text-chc-slate">Step {i + 1}</p>
              <p className={`text-sm truncate ${active ? "font-semibold text-chc-ink" : "text-chc-slate"}`}>{s.label}</p>
            </div>
          </li>
        );
      })}
    </ol>
  );
}

function UploadStep({ dropRef, inputRef, files, setFiles, onDrop, onDragOver, onDragLeave, onFiles }) {
  return (
    <div>
      <p className="text-[11px] uppercase tracking-widest text-chc-slate">Step 1</p>
      <h2 className="mt-1 text-xl font-semibold text-chc-ink">Upload medical records</h2>
      <p className="mt-1 text-sm text-chc-slate">One patient encounter per session. PDF, PNG, JPG, TIFF, DOCX, TXT — max 15 MB each.</p>

      <div
        ref={dropRef}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        data-testid="upload-dropzone"
        className="mt-5 rounded-md border-2 border-dashed border-border bg-chc-mist/40 p-10 text-center transition-all"
      >
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-md bg-white border border-border">
          <UploadSimple size={22} className="text-chc-navy" />
        </div>
        <p className="mt-3 text-sm text-chc-ink font-medium">Drag & drop files here</p>
        <p className="text-xs text-chc-slate">or</p>
        <button
          onClick={() => inputRef.current?.click()}
          data-testid="upload-browse"
          className="mt-2 rounded-md border border-border bg-white px-3 py-1.5 text-xs font-medium text-chc-navy hover:bg-chc-mist"
        >Browse files</button>
        <input ref={inputRef} type="file" multiple onChange={(e) => onFiles(e.target.files)} className="hidden"
          accept=".pdf,.png,.jpg,.jpeg,.tif,.tiff,.docx,.txt,.webp" data-testid="upload-input" />
      </div>

      {files.length > 0 && (
        <ul className="mt-4 space-y-2" data-testid="upload-filelist">
          {files.map((f, i) => (
            <li key={i} className="flex items-center justify-between rounded-md border border-border bg-white p-3">
              <div className="flex items-center gap-3 min-w-0">
                <FileText className="text-chc-blue shrink-0" size={18} />
                <div className="min-w-0">
                  <p className="truncate text-sm text-chc-ink">{f.name}</p>
                  <p className="text-[11px] text-chc-slate">{(f.size / 1024).toFixed(1)} KB</p>
                </div>
              </div>
              <button onClick={() => setFiles((p) => p.filter((_, j) => j !== i))} data-testid={`upload-remove-${i}`} className="text-chc-slate hover:text-rose-600">
                <X size={16} />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function ClaimTypeStep({ value, setValue }) {
  return (
    <div>
      <p className="text-[11px] uppercase tracking-widest text-chc-slate">Step 2</p>
      <h2 className="mt-1 text-xl font-semibold text-chc-ink">Select claim form type</h2>
      <div className="mt-5 grid grid-cols-1 md:grid-cols-2 gap-4">
        {[
          { key: "UB-04", title: "UB-04", desc: "Institutional / Hospital billing (inpatient, outpatient facility)" },
          { key: "CMS-1500", title: "CMS-1500", desc: "Professional / Physician billing" },
        ].map((o) => (
          <button
            key={o.key}
            onClick={() => setValue(o.key)}
            data-testid={`claim-${o.key}`}
            className={`text-left rounded-md border p-5 transition-all ${
              value === o.key ? "border-chc-navy bg-chc-mist ring-2 ring-chc-blue" : "border-border bg-white hover:bg-chc-mist"
            }`}
          >
            <p className="font-mono text-xs text-chc-slate">{o.key}</p>
            <p className="mt-1 text-lg font-semibold text-chc-ink">{o.title}</p>
            <p className="mt-1 text-xs text-chc-slate">{o.desc}</p>
          </button>
        ))}
      </div>
    </div>
  );
}

function CodesStep({ allCodes, setAllCodes, codesRequired, setCodesRequired, claimType }) {
  const toggle = (k) => setCodesRequired((p) => p.includes(k) ? p.filter((x) => x !== k) : [...p, k]);
  return (
    <div>
      <p className="text-[11px] uppercase tracking-widest text-chc-slate">Step 3</p>
      <h2 className="mt-1 text-xl font-semibold text-chc-ink">Select codes required</h2>
      <div className="mt-5 space-y-3">
        <label className={`flex items-center gap-3 rounded-md border p-4 cursor-pointer ${allCodes ? "border-chc-navy bg-chc-mist" : "border-border bg-white"}`}>
          <input type="radio" name="allcodes" checked={allCodes} onChange={() => setAllCodes(true)} data-testid="codes-all" />
          <div>
            <p className="font-medium text-chc-ink">All codes (recommended)</p>
            <p className="text-xs text-chc-slate">Return every applicable code type for the selected claim form.</p>
          </div>
        </label>
        <label className={`flex items-center gap-3 rounded-md border p-4 cursor-pointer ${!allCodes ? "border-chc-navy bg-chc-mist" : "border-border bg-white"}`}>
          <input type="radio" name="allcodes" checked={!allCodes} onChange={() => setAllCodes(false)} data-testid="codes-specific" />
          <div>
            <p className="font-medium text-chc-ink">Specific codes only</p>
            <p className="text-xs text-chc-slate">Pick the code sets below.</p>
          </div>
        </label>
        {!allCodes && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-2">
            {CODE_OPTIONS.filter((o) => !(o.key === "ICD-10-PCS" && claimType !== "UB-04")).map((o) => {
              const on = codesRequired.includes(o.key);
              return (
                <label key={o.key} data-testid={`codes-${o.key}`} className={`flex items-center gap-2 rounded-md border p-3 text-sm cursor-pointer ${on ? "border-chc-navy bg-chc-mist" : "border-border bg-white"}`}>
                  <input type="checkbox" checked={on} onChange={() => toggle(o.key)} />
                  <span className="text-chc-ink">{o.label}</span>
                </label>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

function SpecialtyStep({ specialty, setSpecialty }) {
  const toggle = (s) => setSpecialty((p) => p.includes(s) ? p.filter((x) => x !== s) : [...p, s]);
  return (
    <div>
      <p className="text-[11px] uppercase tracking-widest text-chc-slate">Step 4</p>
      <h2 className="mt-1 text-xl font-semibold text-chc-ink">Select medical specialty</h2>
      <p className="mt-1 text-sm text-chc-slate">Multi-select allowed.</p>
      <div className="mt-5 grid grid-cols-2 md:grid-cols-3 gap-2">
        {SPECIALTIES.map((s) => {
          const on = specialty.includes(s);
          return (
            <button
              key={s}
              onClick={() => toggle(s)}
              data-testid={`specialty-${s.replace(/\W+/g, "-").toLowerCase()}`}
              className={`rounded-md border p-3 text-left text-sm transition ${on ? "border-chc-navy bg-chc-mist text-chc-ink" : "border-border bg-white text-chc-slate hover:bg-chc-mist"}`}
            >
              <span className="flex items-center gap-2">
                <Stethoscope size={14} className={on ? "text-chc-navy" : "text-chc-slate"} /> {s}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function PayerStep({ payer, setPayer, state, setState }) {
  return (
    <div>
      <p className="text-[11px] uppercase tracking-widest text-chc-slate">Step 5</p>
      <h2 className="mt-1 text-xl font-semibold text-chc-ink">Select payer type</h2>
      <div className="mt-5 grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { key: "MEDICARE", title: "Medicare", icon: Building },
          { key: "MEDICAID", title: "Medicaid", icon: Building },
          { key: "COMMERCIAL", title: "Commercial Insurance", icon: CreditCard },
        ].map((o) => (
          <button key={o.key} onClick={() => setPayer(o.key)}
            data-testid={`payer-${o.key}`}
            className={`text-left rounded-md border p-5 transition ${payer === o.key ? "border-chc-navy bg-chc-mist ring-2 ring-chc-blue" : "border-border bg-white hover:bg-chc-mist"}`}>
            <o.icon size={18} className="text-chc-blue" />
            <p className="mt-2 font-semibold text-chc-ink">{o.title}</p>
          </button>
        ))}
      </div>
      {payer === "MEDICAID" && (
        <div className="mt-5 max-w-xs">
          <label className="block text-[11px] font-semibold uppercase tracking-widest text-chc-slate mb-1">State</label>
          <select value={state} onChange={(e) => setState(e.target.value)} data-testid="payer-state"
            className="h-11 w-full rounded-md border border-border bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#0073CF]">
            <option value="">Select a state</option>
            {US_STATES.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
      )}
    </div>
  );
}

function ProcessStep({ run, processing, processSteps }) {
  return (
    <div>
      <p className="text-[11px] uppercase tracking-widest text-chc-slate">Step 6</p>
      <h2 className="mt-1 text-xl font-semibold text-chc-ink">Automated processing</h2>
      <p className="mt-1 text-sm text-chc-slate">OCR → PHI purge → payer-specific coding → MUE/NCCI validation. Nothing leaves this server.</p>

      {!processing && processSteps.length === 0 && (
        <button onClick={run} data-testid="process-start"
          className="mt-6 inline-flex items-center gap-2 rounded-md bg-chc-navy px-5 py-2.5 text-sm font-medium text-white hover:bg-[#002f67] transition">
          <Sparkle size={16} weight="fill" /> Start processing
        </button>
      )}

      {(processing || processSteps.length > 0) && (
        <div className="mt-6 rounded-md border border-border bg-chc-mist/40 p-5 relative overflow-hidden" data-testid="process-log">
          {processing && <div className="scanline" />}
          <ul className="space-y-2 text-sm relative z-10">
            {processSteps.map((s, i) => (
              <li key={i} className="flex items-center gap-2">
                {s.done ? (
                  <CheckCircle weight="fill" className="text-emerald-600" size={18} />
                ) : (
                  <span className="h-4 w-4 rounded-full border-2 border-chc-cyan border-t-transparent animate-spin" />
                )}
                <span className={s.done ? "text-chc-ink" : "text-chc-slate"}>{s.label}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
