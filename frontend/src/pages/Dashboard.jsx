/**
 * CHC Pro AI — Dashboard.jsx
 * Shows company logo in top navbar with real user data from GET /api/v1/auth/me.
 */
import { useEffect, useState } from 'react';
import { useNavigate }         from 'react-router-dom';
import { useAuth }             from '../hooks/useAuth';
import { getMe, apiError }     from '../services/authService';

const font = "'IBM Plex Sans', sans-serif";
const navy = '#003F87';
const teal = '#0073CF';

const S = {
  page: { minHeight:'100vh', background:'#F8FAFC', fontFamily:font },
  topbar: {
    background:navy, padding:'0 28px', height:60,
    display:'flex', alignItems:'center', justifyContent:'space-between',
    boxShadow:'0 1px 4px rgba(0,0,0,0.18)',
  },
  topbarLeft: { display:'flex', alignItems:'center', gap:12 },
  topbarLogo: { width:38, height:38, objectFit:'contain', borderRadius:6 },
  topbarBrand: {
    display:'flex', flexDirection:'column',
  },
  topbarName: { color:'#fff', fontSize:15, fontWeight:700, lineHeight:1.2 },
  topbarSub:  { color:'rgba(255,255,255,0.65)', fontSize:10, lineHeight:1.2 },
  topbarRight: { display:'flex', alignItems:'center', gap:14 },
  topbarEmail: { color:'rgba(255,255,255,0.75)', fontSize:13 },
  logoutBtn: {
    background:'rgba(255,255,255,0.13)',
    border:'1px solid rgba(255,255,255,0.22)',
    borderRadius:6, color:'#fff', fontSize:13,
    padding:'5px 14px', cursor:'pointer', fontFamily:font,
  },
  body: { maxWidth:920, margin:'0 auto', padding:'36px 24px' },
  greeting: { fontSize:24, fontWeight:600, color:navy, marginBottom:4 },
  greetingSub: { fontSize:14, color:'#64748B', marginBottom:32 },
  grid: {
    display:'grid',
    gridTemplateColumns:'repeat(auto-fit, minmax(190px, 1fr))',
    gap:16, marginBottom:32,
  },
  statCard: {
    background:'#fff', border:'1px solid #E2E8F0',
    borderRadius:10, padding:'20px 20px 18px',
  },
  statLabel: {
    fontSize:11, fontWeight:500, color:'#94A3B8',
    textTransform:'uppercase', letterSpacing:'0.05em', marginBottom:6,
  },
  statValue: { fontSize:18, fontWeight:600, color:navy },
  badge: ok => ({
    display:'inline-flex', alignItems:'center', gap:5,
    padding:'3px 10px', borderRadius:20, fontSize:12, fontWeight:500,
    background: ok ? '#D1FAE5' : '#FEE2E2',
    color:      ok ? '#065F46' : '#991B1B',
  }),
  profileCard: {
    background:'#fff', border:'1px solid #E2E8F0',
    borderRadius:10, padding:'24px 28px', marginBottom:24,
  },
  profileTitle: {
    fontSize:15, fontWeight:600, color:navy,
    marginBottom:20, paddingBottom:12,
    borderBottom:'1px solid #F1F5F9',
  },
  profileRow: {
    display:'grid', gridTemplateColumns:'160px 1fr',
    alignItems:'center', padding:'8px 0',
    borderBottom:'1px solid #F8FAFC',
  },
  profileKey: {
    fontSize:12, fontWeight:500, color:'#94A3B8',
    textTransform:'uppercase', letterSpacing:'0.04em',
  },
  profileVal: { fontSize:14, color:'#0F172A' },
  actionCard: {
    background:navy, borderRadius:10,
    padding:'24px 28px',
    display:'flex', alignItems:'center',
    justifyContent:'space-between', flexWrap:'wrap', gap:16,
  },
  actionBtn: {
    background:'#fff', color:navy, border:'none',
    borderRadius:8, padding:'10px 24px',
    fontSize:14, fontWeight:600, cursor:'pointer', fontFamily:font,
  },
  err: {
    background:'#FEE2E2', border:'1px solid #FECACA',
    borderRadius:8, padding:'10px 14px',
    color:'#991B1B', fontSize:13, marginBottom:20,
  },
  spinner: {
    display:'flex', alignItems:'center', justifyContent:'center',
    height:'60vh', flexDirection:'column', gap:14,
    color:'#64748B', fontSize:14,
  },
};

function Spinner() {
  return (
    <div style={S.spinner}>
      <div style={{
        width:36, height:36, borderRadius:'50%',
        border:'3px solid #E2E8F0', borderTopColor:navy,
        animation:'spin 0.7s linear infinite',
      }} />
      <span>Loading your profile…</span>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

export default function Dashboard() {
  const navigate         = useNavigate();
  const { logout }       = useAuth();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState('');

  useEffect(() => {
    getMe()
      .then(setProfile)
      .catch(e => setError(apiError(e)))
      .finally(() => setLoading(false));
  }, []);

  async function handleLogout() {
    await logout();
    navigate('/login');
  }

  function fmt(v)   { return (v === null || v === undefined || v === '') ? '—' : String(v); }
  function spec(s)  { return s ? s.replace(/_/g,' ').replace(/\b\w/g, l => l.toUpperCase()) : '—'; }
  function fmtDate(iso) {
    try { return new Date(iso).toLocaleDateString('en-US',{ year:'numeric', month:'long', day:'numeric' }); }
    catch { return iso || '—'; }
  }

  return (
    <div style={S.page}>

      {/* ── Top navigation bar ── */}
      <div style={S.topbar}>
        <div style={S.topbarLeft}>
          {/* Logo */}
          <img
            src="/logo.webp"
            alt="CHC Pro AI"
            style={S.topbarLogo}
            onError={e => { e.target.style.display='none'; }}
          />
          <div style={S.topbarBrand}>
            <span style={S.topbarName}>CHC Pro AI</span>
            <span style={S.topbarSub}>Healthcare Revenue &amp; Coding Solutions</span>
          </div>
        </div>

        <div style={S.topbarRight}>
          {profile && (
            <span style={S.topbarEmail} data-testid="topbar-email">
              {profile.email}
            </span>
          )}
          <button style={S.logoutBtn} onClick={handleLogout} data-testid="logout-btn">
            Sign out
          </button>
        </div>
      </div>

      <div style={S.body}>
        {error && <div style={S.err} data-testid="dashboard-error">{error}</div>}
        {loading && <Spinner />}

        {!loading && profile && (
          <>
            <div style={S.greeting} data-testid="dashboard-greeting">
              Welcome back, {profile.first_name} {profile.last_name}
            </div>
            <div style={S.greetingSub}>
              {spec(profile.specialty)} · {profile.state}
            </div>

            {/* Stat cards */}
            <div style={S.grid}>
              {[
                { label:'NPI',            value: fmt(profile.npi) },
                { label:'Specialty',      value: spec(profile.specialty) },
                { label:'Practice state', value: fmt(profile.state) },
              ].map(({ label, value }) => (
                <div key={label} style={S.statCard}>
                  <div style={S.statLabel}>{label}</div>
                  <div style={S.statValue}>{value}</div>
                </div>
              ))}

              {[
                { label:'PECOS enrollment', ok: profile.pecos_enrolled,
                  text: profile.pecos_enrolled ? '✓ Enrolled' : '✗ Not enrolled' },
                { label:'Two-factor auth',  ok: profile.mfa_enabled,
                  text: profile.mfa_enabled  ? '✓ Enabled'  : '✗ Not enabled' },
                { label:'Email verified',   ok: profile.is_verified,
                  text: profile.is_verified  ? '✓ Verified' : '✗ Not verified' },
              ].map(({ label, ok, text }) => (
                <div key={label} style={S.statCard}>
                  <div style={S.statLabel}>{label}</div>
                  <div style={{ marginTop:4 }}>
                    <span style={S.badge(ok)}>{text}</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Profile detail */}
            <div style={S.profileCard} data-testid="profile-card">
              <div style={S.profileTitle}>Account details</div>
              {[
                ['Full name',     `${profile.first_name} ${profile.last_name}`],
                ['Email',          profile.email],
                ['Organization',   profile.organization],
                ['NPI',            profile.npi],
                ['Claim form',     profile.claim_form_preference || 'Not set'],
                ['Member since',   fmtDate(profile.created_at)],
              ].map(([k,v]) => (
                <div key={k} style={S.profileRow}>
                  <span style={S.profileKey}>{k}</span>
                  <span style={S.profileVal}>{fmt(v)}</span>
                </div>
              ))}
            </div>

            {/* CTA */}
            <div style={S.actionCard} data-testid="cta-card">
              <div style={{ color:'#fff' }}>
                <div style={{ fontSize:17, fontWeight:600, marginBottom:4 }}>
                  Ready to code a medical record?
                </div>
                <div style={{ fontSize:13, opacity:0.8 }}>
                  Upload a medical record to start the AI coding workflow.
                </div>
              </div>
              <button style={S.actionBtn} onClick={()=>navigate('/upload')}
                data-testid="start-coding-btn">
                Start coding →
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
