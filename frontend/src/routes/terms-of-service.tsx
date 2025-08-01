import React from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { Button } from "#/components/ui/button";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "#/components/ui/card";
import { Checkbox } from "#/components/ui/checkbox";
import { Label } from "#/components/ui/label";
import { useAcceptTos } from "#/hooks/mutation/use-accept-tos";

/**
 * Terms of Service page component
 */
export default function TermsOfService() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [accepted, setAccepted] = React.useState(false);
  const acceptTos = useAcceptTos();

  const handleAccept = async () => {
    if (!accepted) return;
    
    try {
      await acceptTos.mutateAsync();
      navigate("/");
    } catch (error) {
      console.error("Error accepting terms:", error);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-background p-4">
      <Card className="w-full max-w-3xl">
        <CardHeader>
          <CardTitle className="text-2xl text-center">
            {t(I18nKey.TOS$TERMS_OF_SERVICE)}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="prose max-w-none">
            <h2>{t(I18nKey.TOS$INTRODUCTION)}</h2>
            <p>{t(I18nKey.TOS$INTRODUCTION_TEXT)}</p>
            
            <h2>{t(I18nKey.TOS$ACCEPTANCE)}</h2>
            <p>{t(I18nKey.TOS$ACCEPTANCE_TEXT)}</p>
            
            <h2>{t(I18nKey.TOS$PRIVACY)}</h2>
            <p>{t(I18nKey.TOS$PRIVACY_TEXT)}</p>
            
            <h2>{t(I18nKey.TOS$USAGE)}</h2>
            <p>{t(I18nKey.TOS$USAGE_TEXT)}</p>
            
            <h2>{t(I18nKey.TOS$LIMITATIONS)}</h2>
            <p>{t(I18nKey.TOS$LIMITATIONS_TEXT)}</p>
          </div>
          
          <div className="flex items-start space-x-2 pt-4">
            <Checkbox 
              id="terms" 
              checked={accepted}
              onCheckedChange={(checked) => setAccepted(checked === true)}
            />
            <Label 
              htmlFor="terms" 
              className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
            >
              {t(I18nKey.TOS$ACCEPT_TERMS)}
            </Label>
          </div>
          
          <div className="flex justify-end pt-4">
            <Button 
              onClick={handleAccept} 
              disabled={!accepted || acceptTos.isPending}
            >
              {acceptTos.isPending ? (
                <span className="loading loading-spinner loading-xs mr-2"></span>
              ) : null}
              {t(I18nKey.TOS$CONTINUE)}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}