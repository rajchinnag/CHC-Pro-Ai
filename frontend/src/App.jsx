/**
 * CHC Pro AI — App.jsx
 * Root router. Replace your existing App.jsx with this file entirely.
 *
 * If your existing App.jsx has anything custom (extra routes, providers,
 * third-party wrappers) merge those into this file.
 *
 * Requires in package.json (run: npm install axios react-router-dom):
 *   "axios": "^1.6.0"
 *   "react-router-dom": "^6.22.0"
 */
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './hooks/useAuth';
import ProtectedRoute   from './components/ProtectedRoute';

// Pages
import Login     from './pages/Login';
import Register  from './pages/Register';
import Dashboard from './pages/Dashboard';

// IBM Plex Sans — matches design_guidelines.json
import './index.css';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* ── Public routes ── */}
          <Route path="/login"    element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* ── Protected routes ── */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />

          {/* ── Default redirects ── */}
          <Route path="/"  element={<Navigate to="/dashboard" replace />} />
          <Route path="*"  element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
