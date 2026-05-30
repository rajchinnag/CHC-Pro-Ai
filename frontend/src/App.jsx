/**
 * CHC Pro AI — App.jsx
 * Root router.
 */
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './hooks/useAuth';
import ProtectedRoute from './components/ProtectedRoute';

// Pages
import Login     from './pages/Login';
import Register  from './pages/Register';
import Dashboard from './pages/Dashboard';
import Upload    from './pages/Upload';
import History   from './pages/History';
import Results   from './pages/Results';

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
          <Route
            path="/upload"
            element={
              <ProtectedRoute>
                <Upload />
              </ProtectedRoute>
            }
          />
          <Route
            path="/history"
            element={
              <ProtectedRoute>
                <History />
              </ProtectedRoute>
            }
          />
          <Route
            path="/results/:id"
            element={
              <ProtectedRoute>
                <Results />
              </ProtectedRoute>
            }
          />

          {/* ── Default redirects ── */}
          <Route path="/"  element={<Navigate to="/dashboard" replace />} />
          <Route path="*"  element={<Navigate to="/login" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}