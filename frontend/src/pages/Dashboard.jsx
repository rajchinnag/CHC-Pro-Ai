/**
 * CHC Pro AI — Dashboard.jsx
 * Displays real authenticated user profile from GET /api/v1/auth/me.
 * Design: IBM Plex Sans, #003F87 navy, #0073CF teal per design_guidelines.json
 */
import { useEffect, useState } from 'react';
import { useNavigate }         from 'react-router-dom';
import { useAuth }             from '../hooks/useAuth';
import { getMe, apiError }     from '../services/authService';

const font = "'IBM Plex Sans', sans-serif";
const navy = '#003F87';
const teal = '#0073CF';

// ── Shared styles ──────────────────────────────────────────────────────────
const S = {
  page: {
    minHeight: '100vh',
    background: '#F8FAFC',
    fontFamily: font,
  },
  topbar: {
    background: navy,
    padding: '0 32px',
    height: 56,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  topbarBrand: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 600,
    letterSpacing: '-0.01em',
  },
  topbarRight: {
    display: 'flex',
    alignItems: 'center',
    gap: 16,
  },
  topbarEmail: {
    color: 'rgba(255,255,255,0.75)',
    fontSize: 13,
  },
  logoutBtn: {
    background: 'rgba(255,255,255,0.12)',
    border: '1px solid rgba(255,255,255,0.2)',
    borderRadius: 6,
    color: '#fff',
    fontSize: 13,
    padding: '5px 14px',
    cursor: 'pointer',
    fontFamily: font,
  },
  body: {
    maxWidth: 900,
    margin: '0 auto',
    padding: '36px 24px',
  },
  greeting: {
    fontSize: 24,
    fontWeight: 600,
    color: navy,
    marginBottom: 4,
  },
  greetingSub: {
    fontSize: 14,
    color: '#64748B',
    marginBottom: 32,
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: 16,
    marginBottom: 32,
  },
  statCard: {
    background: '#fff',
    border: '1px solid #E2E8F0',
    borderRadius: 10,
    padding: '20px 20px 18px',
  },
  statLabel: {
    fontSize: 12,
    fontWeight: 500,
    color: '#94A3B8',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    marginBottom: 6,
  },
  statValue: {
    fontSize: 18,
    fontWeight: 600,
    color: navy,
  },
  badge: (ok) => ({
    display: 'inline-flex',
    alignItems: 'center',
    gap: 5,
    padding: '3px 10px',
    borderRadius: 20,
    fontSize: 12,
    fontWeight: 500,
    background: ok ? '#D1FAE5' : '#FEE2E2',
    color:      ok ? '#065F46' : '#991B1B',
  }),
  profileCard: {
    background: '#fff',
    border: '1px solid #E2E8F0',
    borderRadius: 10,
    padding: '24px 28px',
    marginBottom: 24,
  },
  profileTitle: {
    fontSize: 15,
    fontWeight: 600,
    color: navy,
    marginBottom: 20,
    paddingBottom: 12,
    borderBottom: '1px solid #F1F5F9',
  },
  profileRow: {
    display: 'grid',
    gridTemplateColumns: '160px 1fr',
    alignItems: 'center',
    padding: '8px 0',
    borderBottom: '1px solid #F8FAFC',
  },
  profileKey: {
    fontSize: 12,
    fontWeight: 500,
    color: '#94A3B8',
    textTransform: 'uppercase',
    letterSpacing: '0.04em',
  },
  profileVal: {
    fontSize: 14,
    color: '#0F172A',
  },
  actionCard: {
    background: navy,
    borderRadius: 10,
    padding: '24px 28px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    flexWrap: 'wrap',
    gap: 16,
  },
  actionText: {
    color: '#fff',
  },
  actionBtn: {
    background: '#fff',
    color: navy,
    border: 'none',
    borderRadius: 8,
    padding: '10px 24px',
    fontSize: 14,
    fontWeight: 600,
    cursor: 'pointer',
    fontFamily: font,
    whiteSpace: 'nowrap',
  },
  err: {
    background: '#FEE2E2',
    border: '1px solid #FECACA',
    borderRadius: 8,
    padding: '10px 14px',
    color: '#991B1B',
    fontSize: 13,
    marginBottom: 20,
  },
  spinner: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    height: '60vh',
    flexDirection: 'column',
    gap: 14,
    color: '#64748B',
    fontSize: 14,
  },
};

// ── Spinner ────────────────────────────────────────────────────────────────
function Spinner() {
  return (
    <div style={S.spinner}>
      <div style={{
        width: 36, height: 36, borderRadius: '50%',
        border: '3px solid #E2E8F0', borderTopColor: navy,
        animation: 'spin 0.7s linear infinite',
      }} />
      <span>Loading your profile…</span>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

// ── Main ───────────────────────────────────────────────────────────────────
export default function Dashboard() {
  const navigate       = useNavigate();
  const { logout }     = useAuth();
  const [profile, setProfile]   = useState(null);
  const [loading, setLoading]   = useState(true);
  const [error,   setError]     = useState('');

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

  function fmt(val) {
    if (val === null || val === undefined || val === '') return '—';
    return String(val);
  }

  function fmtSpecialty(s) {
    if (!s) return '—';
    return s.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  }

  function fmtDate(iso) {
    if (!iso) return '—';
    try { return new Date(iso).toLocaleDateString('en-US', { year:'numeric', month:'long', day:'numeric' }); }
    catch { return iso; }
  }

  return (
    <div style={S.page}>

      {/* Top bar */}
      <div style={S.topbar}>
        <span style={S.topbarBrand}>Carolin Code Pro AI</span>
        <div style={S.topbarRight}>
          {profile && (
            <span style={S.topbarEmail} data-testid="topbar-email">
              {profile.email}
            </span>
          )}
          <button
            style={S.logoutBtn}
            onClick={handleLogout}
            data-testid="logout-btn"
          >
            Sign out
          </button>
        </div>
      </div>

      <div style={S.body}>

        {error && <div style={S.err} data-testid="dashboard-error">{error}</div>}

        {loading && <Spinner />}

        {!loading && profile && (
          <>
            {/* Greeting */}
            <div
              style={S.greeting}
              data-testid="dashboard-greeting"
            >
              Welcome back, {profile.first_name} {profile.last_name}
            </div>
            <div style={S.greetingSub}>
              {fmtSpecialty(profile.specialty)} · {profile.state}
            </div>

            {/* Stat cards */}
            <div style={S.grid}>
              <div style={S.statCard} data-testid="stat-npi">
                <div style={S.statLabel}>NPI</div>
                <div style={S.statValue}>{fmt(profile.npi)}</div>
              </div>

              <div style={S.statCard} data-testid="stat-specialty">
                <div style={S.statLabel}>Specialty</div>
                <div style={S.statValue}>{fmtSpecialty(profile.specialty)}</div>
              </div>

              <div style={S.statCard} data-testid="stat-state">
                <div style={S.statLabel}>Practice state</div>
                <div style={S.statValue}>{fmt(profile.state)}</div>
              </div>

              <div style={S.statCard} data-testid="stat-pecos">
                <div style={S.statLabel}>PECOS enrollment</div>
                <div style={{ marginTop: 4 }}>
                  <span style={S.badge(profile.pecos_enrolled)}>
                    {profile.pecos_enrolled ? '✓ Enrolled' : '✗ Not enrolled'}
                  </span>
                </div>
              </div>

              <div style={S.statCard} data-testid="stat-mfa">
                <div style={S.statLabel}>Two-factor auth</div>
                <div style={{ marginTop: 4 }}>
                  <span style={S.badge(profile.mfa_enabled)}>
                    {profile.mfa_enabled ? '✓ Enabled' : '✗ Not enabled'}
                  </span>
                </div>
              </div>

              <div style={S.statCard} data-testid="stat-verified">
                <div style={S.statLabel}>Email verified</div>
                <div style={{ marginTop: 4 }}>
                  <span style={S.badge(profile.is_verified)}>
                    {profile.is_verified ? '✓ Verified' : '✗ Not verified'}
                  </span>
                </div>
              </div>
            </div>

            {/* Profile detail */}
            <div style={S.profileCard} data-testid="profile-card">
              <div style={S.profileTitle}>Account details</div>

              {[
                ['Full name',      `${profile.first_name} ${profile.last_name}`],
                ['Email',          profile.email],
                ['Organization',   profile.organization],
                ['NPI',            profile.npi],
                ['Provider type',  profile.claim_form_preference || 'individual'],
                ['Claim form',     profile.claim_form_preference || 'Not set'],
                ['Member since',   fmtDate(profile.created_at)],
              ].map(([k, v]) => (
                <div key={k} style={S.profileRow}>
                  <span style={S.profileKey}>{k}</span>
                  <span style={S.profileVal}>{fmt(v)}</span>
                </div>
              ))}
            </div>

            {/* Start coding CTA — active once Layer 2+ is built */}
            <div style={S.actionCard} data-testid="cta-card">
              <div style={S.actionText}>
                <div style={{ fontSize: 17, fontWeight: 600, marginBottom: 4 }}>
                  Ready to code a medical record?
                </div>
                <div style={{ fontSize: 13, opacity: 0.8 }}>
                  Upload a medical record to start the AI coding workflow.
                </div>
              </div>
              <button
                style={S.actionBtn}
                onClick={() => navigate('/upload')}
                data-testid="start-coding-btn"
              >
                Start coding →
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
