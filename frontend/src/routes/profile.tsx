import React from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { useAuth } from "#/hooks/use-auth";
import { PageHeader } from "#/components/shared/page-header";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "#/components/ui/card";
import { Button } from "#/components/ui/button";
import { formatDate } from "#/utils/date";
import { useNavigate } from "react-router-dom";

/**
 * User profile page component
 */
export default function Profile() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title={t(I18nKey.AUTH$MY_PROFILE)}
        description={t(I18nKey.AUTH$VIEW_AND_MANAGE_YOUR_PROFILE)}
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>{t(I18nKey.AUTH$PROFILE_INFORMATION)}</CardTitle>
            <CardDescription>
              {t(I18nKey.AUTH$VIEW_YOUR_ACCOUNT_DETAILS)}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {user ? (
              <>
                <div className="space-y-1">
                  <p className="text-sm font-medium text-muted-foreground">
                    {t(I18nKey.AUTH$USERNAME)}
                  </p>
                  <p className="font-medium">{user.username}</p>
                </div>

                {user.email && (
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-muted-foreground">
                      {t(I18nKey.AUTH$EMAIL)}
                    </p>
                    <p className="font-medium">{user.email}</p>
                    {!user.email_verified && (
                      <p className="text-xs text-warning">
                        {t(I18nKey.AUTH$EMAIL_NOT_VERIFIED)}
                      </p>
                    )}
                  </div>
                )}

                <div className="space-y-1">
                  <p className="text-sm font-medium text-muted-foreground">
                    {t(I18nKey.AUTH$ACCOUNT_CREATED)}
                  </p>
                  <p className="font-medium">
                    {formatDate(new Date(user.created_at))}
                  </p>
                </div>

                {user.last_login && (
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-muted-foreground">
                      {t(I18nKey.AUTH$LAST_LOGIN)}
                    </p>
                    <p className="font-medium">
                      {formatDate(new Date(user.last_login))}
                    </p>
                  </div>
                )}

                <div className="pt-4">
                  <Button
                    variant="destructive"
                    onClick={handleLogout}
                  >
                    {t(I18nKey.AUTH$LOGOUT)}
                  </Button>
                </div>
              </>
            ) : (
              <div className="py-4 text-center text-muted-foreground">
                {t(I18nKey.COMMON$LOADING)}...
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t(I18nKey.AUTH$ACCOUNT_SETTINGS)}</CardTitle>
            <CardDescription>
              {t(I18nKey.AUTH$MANAGE_YOUR_ACCOUNT_SETTINGS)}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button
              variant="outline"
              className="w-full justify-start"
              onClick={() => navigate("/settings/git")}
            >
              {t(I18nKey.SETTINGS$GIT_SETTINGS)}
            </Button>
            <Button
              variant="outline"
              className="w-full justify-start"
              onClick={() => navigate("/settings/llm")}
            >
              {t(I18nKey.SETTINGS$LLM_SETTINGS)}
            </Button>
            <Button
              variant="outline"
              className="w-full justify-start"
              onClick={() => navigate("/settings/app")}
            >
              {t(I18nKey.SETTINGS$NAV_APPLICATION)}
            </Button>
            <Button
              variant="outline"
              className="w-full justify-start"
              onClick={() => navigate("/settings/secrets")}
            >
              {t(I18nKey.SETTINGS$NAV_SECRETS)}
            </Button>
            <Button
              variant="outline"
              className="w-full justify-start"
              onClick={() => navigate("/settings/webhooks")}
            >
              {t(I18nKey.SETTINGS$NAV_WEBHOOKS)}
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
