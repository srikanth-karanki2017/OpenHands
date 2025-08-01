import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "#/hooks/use-auth";

interface ProtectedRouteProps {
  children: React.ReactNode;
}

/**
 * ProtectedRoute component that redirects to login if user is not authenticated
 */
export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  // Show loading state while checking authentication
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="loading loading-spinner loading-lg"></div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Render children if authenticated
  return <>{children}</>;
}