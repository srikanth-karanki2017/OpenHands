import React from "react";
import {
  useRouteError,
  isRouteErrorResponse,
  Outlet,
  useNavigate,
  useLocation,
} from "react-router";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import i18n from "#/i18n";
import { useGitHubAuthUrl } from "#/hooks/use-github-auth-url";
import { useIsAuthed } from "#/hooks/query/use-is-authed";
import { useConfig } from "#/hooks/query/use-config";
import { Sidebar } from "#/components/features/sidebar/sidebar";
import { AuthProvider } from "#/hooks/use-auth";
import { useAuth } from "#/hooks/use-auth";
import { ProtectedRoute } from "#/components/features/auth/protected-route";
import { useSettings } from "#/hooks/query/use-settings";
import { useMigrateUserConsent } from "#/hooks/use-migrate-user-consent";
import { useBalance } from "#/hooks/query/use-balance";
import { displaySuccessToast } from "#/utils/custom-toast-handlers";
import { useIsOnTosPage } from "#/hooks/use-is-on-tos-page";
import { LOCAL_STORAGE_KEYS } from "#/utils/local-storage";
import { EmailVerificationGuard } from "#/components/features/guards/email-verification-guard";
import { MaintenanceBanner } from "#/components/features/maintenance/maintenance-banner";

export function ErrorBoundary() {
  const error = useRouteError();
  const { t } = useTranslation();

  if (isRouteErrorResponse(error)) {
    return (
      <div>
        <h1>{error.status}</h1>
        <p>{error.statusText}</p>
        <pre>
          {error.data instanceof Object
            ? JSON.stringify(error.data)
            : error.data}
        </pre>
      </div>
    );
  }
  if (error instanceof Error) {
    return (
      <div>
        <h1>{t(I18nKey.ERROR$GENERIC)}</h1>
        <pre>{error.message}</pre>
      </div>
    );
  }

  return (
    <div>
      <h1>{t(I18nKey.ERROR$UNKNOWN)}</h1>
    </div>
  );
}

/**
 * AuthWrapper component that wraps the app with the AuthProvider
 */
export function AuthWrapper() {
  return (
    <AuthProvider>
      <MultiUserApp />
    </AuthProvider>
  );
}

/**
 * MultiUserApp component that handles authentication and routing
 */
function MultiUserApp() {
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const isOnTosPage = useIsOnTosPage();
  const { data: settings } = useSettings();
  const { error } = useBalance();
  const { migrateUserConsent } = useMigrateUserConsent();
  const { t } = useTranslation();
  const { isAuthenticated, isLoading } = useAuth();

  const config = useConfig();

  // Public routes that don't require authentication
  const isPublicRoute = pathname === "/login" || pathname === "/register" || isOnTosPage;

  React.useEffect(() => {
    // Don't change language when on TOS page
    if (!isOnTosPage && settings?.LANGUAGE) {
      i18n.changeLanguage(settings.LANGUAGE);
    }
  }, [settings?.LANGUAGE, isOnTosPage]);

  React.useEffect(() => {
    // Don't do any redirects when on TOS page or public routes
    // Don't allow users to use the app if it 402s
    if (!isOnTosPage && !isPublicRoute && error?.status === 402 && pathname !== "/") {
      navigate("/");
    }
  }, [error?.status, pathname, isOnTosPage, isPublicRoute]);

  // Show loading state while checking authentication
  if (isLoading && !isPublicRoute) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="loading loading-spinner loading-lg"></div>
      </div>
    );
  }

  return (
    <div
      data-testid="root-layout"
      className="bg-base p-3 h-screen lg:min-w-[1024px] flex flex-col md:flex-row gap-3"
    >
      {/* Only show sidebar if authenticated or on public routes */}
      {(isAuthenticated || isPublicRoute) && <Sidebar />}

      <div
        id="root-outlet"
        className="h-[calc(100%-50px)] md:h-full w-full relative overflow-auto"
      >
        {config.data?.MAINTENANCE && (
          <MaintenanceBanner startTime={config.data.MAINTENANCE.startTime} />
        )}

        {/* Conditionally wrap with ProtectedRoute based on route */}
        {isPublicRoute ? (
          <Outlet />
        ) : (
          <ProtectedRoute>
            <EmailVerificationGuard>
              <Outlet />
            </EmailVerificationGuard>
          </ProtectedRoute>
        )}
      </div>
    </div>
  );
}

export default AuthWrapper;
