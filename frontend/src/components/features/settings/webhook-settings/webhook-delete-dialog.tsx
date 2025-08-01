import React from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "#/components/ui/alert-dialog";
import { WebhookConfig } from "#/types/webhook";
import { useDeleteWebhook } from "#/hooks/mutation/use-delete-webhook";

interface WebhookDeleteDialogProps {
  webhook: WebhookConfig;
  onClose: () => void;
}

/**
 * WebhookDeleteDialog component for confirming webhook deletion
 */
export function WebhookDeleteDialog({ webhook, onClose }: WebhookDeleteDialogProps) {
  const { t } = useTranslation();
  const deleteWebhook = useDeleteWebhook();

  const handleDelete = async () => {
    try {
      await deleteWebhook.mutateAsync(webhook.webhook_id);
      onClose();
    } catch (error) {
      console.error("Error deleting webhook:", error);
    }
  };

  return (
    <AlertDialog open={true} onOpenChange={(open) => !open && onClose()}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{t(I18nKey.WEBHOOK$DELETE_WEBHOOK)}</AlertDialogTitle>
          <AlertDialogDescription>
            {t(I18nKey.WEBHOOK$DELETE_WEBHOOK_CONFIRMATION, { name: webhook.name })}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>{t(I18nKey.COMMON$CANCEL)}</AlertDialogCancel>
          <AlertDialogAction
            onClick={handleDelete}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            {deleteWebhook.isPending && (
              <span className="loading loading-spinner loading-xs mr-2"></span>
            )}
            {t(I18nKey.COMMON$DELETE)}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}