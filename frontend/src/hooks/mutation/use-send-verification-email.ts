import { useMutation } from "@tanstack/react-query";
import { authApi } from "#/api/auth-api";
import { displaySuccessToast } from "#/utils/custom-toast-handlers";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

/**
 * Hook for sending a verification email
 */
export function useSendVerificationEmail() {
  const { t } = useTranslation();
  
  return useMutation({
    mutationFn: () => authApi.sendVerificationEmail(),
    onSuccess: () => {
      displaySuccessToast(t(I18nKey.AUTH$VERIFICATION_EMAIL_SENT));
    },
  });
}