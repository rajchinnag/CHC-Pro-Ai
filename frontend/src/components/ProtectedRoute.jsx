import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";

export default function ProtectedRoute({ children, adminOnly = false }) {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3" data-testid="auth-loading">
          <div className="h-10 w-10 rounded-full border-2 border-chc-navy border-t-transparent animate-spin" />
          <p className="text-sm text-chc-slate">Verifying session…</p>
        </div>
      </div>
    );
  }
  if (!user) return <Navigate to="/login" replace />;
  if (adminOnly && !["admin", "provider"].includes(user.role)) {
    return <Navigate to="/app/dashboard" replace />;
  }
  return children;
}
