import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { Button } from "#/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "#/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "#/components/ui/table";
import { Badge } from "#/components/ui/badge";
import { PlusIcon, TrashIcon, PencilIcon } from "@heroicons/react/24/outline";
import { useWebhooks } from "#/hooks/query/use-webhooks";
import { WebhookForm } from "./webhook-form";
import { WebhookConfig } from "#/types/webhook";
import { useDeleteWebhook } from "#/hooks/mutation/use-delete-webhook";
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
import { formatDate } from "#/utils/date";

/**
 * WebhookList component displays a list of user's webhook configurations
 * and provides options to add, edit, and delete webhooks.
 */
export function WebhookList() {
  const { t } = useTranslation();
  const { data: webhooks, isLoading } = useWebhooks();
  const deleteWebhook = useDeleteWebhook();

  const [showForm, setShowForm] = useState(false);
  const [editingWebhook, setEditingWebhook] = useState<WebhookConfig | null>(null);
  const [webhookToDelete, setWebhookToDelete] = useState<WebhookConfig | null>(null);

  const handleAddWebhook = () => {
    setEditingWebhook(null);
    setShowForm(true);
  };

  const handleEditWebhook = (webhook: WebhookConfig) => {
    setEditingWebhook(webhook);
    setShowForm(true);
  };

  const handleCloseForm = () => {
    setShowForm(false);
    setEditingWebhook(null);
  };

  const handleDeleteWebhook = (webhook: WebhookConfig) => {
    setWebhookToDelete(webhook);
  };

  const confirmDelete = async () => {
    if (webhookToDelete) {
      await deleteWebhook.mutateAsync(webhookToDelete.webhook_id);
      setWebhookToDelete(null);
    }
  };

  return (
    <>
      <Card className="w-full">
        <CardHeader>
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <CardTitle>{t(I18nKey.WEBHOOK$MY_WEBHOOKS)}</CardTitle>
              <CardDescription>
                {t(I18nKey.WEBHOOK$MANAGE_YOUR_WEBHOOK_CONFIGURATIONS)}
              </CardDescription>
            </div>
            <Button onClick={handleAddWebhook} className="whitespace-nowrap">
              <PlusIcon className="h-4 w-4 mr-2" />
              {t(I18nKey.WEBHOOK$ADD_WEBHOOK)}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="py-8 text-center text-muted-foreground">
              {t(I18nKey.COMMON$LOADING)}...
            </div>
          ) : webhooks && webhooks.length > 0 ? (
            <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="whitespace-nowrap">{t(I18nKey.WEBHOOK$NAME)}</TableHead>
                  <TableHead className="whitespace-nowrap">{t(I18nKey.WEBHOOK$URL)}</TableHead>
                  <TableHead className="whitespace-nowrap">{t(I18nKey.WEBHOOK$REPOSITORY)}</TableHead>
                  <TableHead className="whitespace-nowrap">{t(I18nKey.WEBHOOK$EVENTS)}</TableHead>
                  <TableHead className="whitespace-nowrap">{t(I18nKey.WEBHOOK$STATUS)}</TableHead>
                  <TableHead className="whitespace-nowrap">{t(I18nKey.WEBHOOK$CREATED_AT)}</TableHead>
                  <TableHead className="whitespace-nowrap">{t(I18nKey.COMMON$ACTIONS)}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {webhooks.map((webhook) => (
                  <TableRow key={webhook.webhook_id}>
                    <TableCell className="font-medium">{webhook.name}</TableCell>
                    <TableCell className="max-w-[200px] truncate">
                      {webhook.url.toString()}
                    </TableCell>
                    <TableCell>
                      {webhook.repository || t(I18nKey.WEBHOOK$ALL_REPOSITORIES)}
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {webhook.events.map((event) => (
                          <Badge key={event} variant="outline">
                            {event}
                          </Badge>
                        ))}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={webhook.status === "active" ? "success" : "secondary"}
                      >
                        {webhook.status === "active"
                          ? t(I18nKey.WEBHOOK$ACTIVE)
                          : t(I18nKey.WEBHOOK$INACTIVE)}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {formatDate(new Date(webhook.created_at))}
                    </TableCell>
                    <TableCell>
                      <div className="flex space-x-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleEditWebhook(webhook)}
                        >
                          <PencilIcon className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDeleteWebhook(webhook)}
                        >
                          <TrashIcon className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            </div>
          ) : (
            <div className="py-8 text-center text-muted-foreground">
              {t(I18nKey.WEBHOOK$NO_WEBHOOKS_FOUND)}
            </div>
          )}
        </CardContent>
      </Card>

      {showForm && (
        <WebhookForm
          webhook={editingWebhook}
          onClose={handleCloseForm}
        />
      )}

      <AlertDialog open={!!webhookToDelete} onOpenChange={(open) => !open && setWebhookToDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t(I18nKey.WEBHOOK$DELETE_WEBHOOK)}</AlertDialogTitle>
            <AlertDialogDescription>
              {t(I18nKey.WEBHOOK$DELETE_WEBHOOK_CONFIRMATION, {
                name: webhookToDelete?.name,
              })}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>
              {t(I18nKey.COMMON$CANCEL)}
            </AlertDialogCancel>
            <AlertDialogAction onClick={confirmDelete} className="bg-destructive">
              {t(I18nKey.COMMON$DELETE)}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
