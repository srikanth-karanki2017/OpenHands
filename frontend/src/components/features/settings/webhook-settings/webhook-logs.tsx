import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import {
  Card,
  CardContent,
  CardDescription,
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
import { Button } from "#/components/ui/button";
import { Input } from "#/components/ui/input";
import { Label } from "#/components/ui/label";
import { EyeIcon, ArrowPathIcon } from "@heroicons/react/24/outline";
import { useWebhookLogs } from "#/hooks/query/use-webhook-logs";
import { WebhookLog } from "#/types/webhook";
import { formatDate } from "#/utils/date";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "#/components/ui/dialog";
import { useWebhooks } from "#/hooks/query/use-webhooks";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "#/components/ui/select";

/**
 * WebhookLogs component displays a list of webhook delivery logs
 * and provides filtering and detailed view options.
 */
export function WebhookLogs() {
  const { t } = useTranslation();
  const [selectedWebhookId, setSelectedWebhookId] = useState<string | null>(null);
  const [selectedLog, setSelectedLog] = useState<WebhookLog | null>(null);
  const { data: webhooks } = useWebhooks();
  
  const { 
    data: logs, 
    isLoading, 
    refetch 
  } = useWebhookLogs({ 
    webhookId: selectedWebhookId || undefined 
  });

  const handleViewLog = (log: WebhookLog) => {
    setSelectedLog(log);
  };

  const handleFilterChange = (webhookId: string) => {
    setSelectedWebhookId(webhookId === "all" ? null : webhookId);
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case "success":
        return "success";
      case "failure":
        return "destructive";
      case "pending":
        return "warning";
      default:
        return "secondary";
    }
  };

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <div>
              <CardTitle>{t(I18nKey.WEBHOOK$WEBHOOK_LOGS)}</CardTitle>
              <CardDescription>
                {t(I18nKey.WEBHOOK$VIEW_WEBHOOK_DELIVERY_HISTORY)}
              </CardDescription>
            </div>
            <Button variant="outline" onClick={() => refetch()}>
              <ArrowPathIcon className="h-4 w-4 mr-2" />
              {t(I18nKey.COMMON$REFRESH)}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="mb-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <Label htmlFor="webhook-filter">
                  {t(I18nKey.WEBHOOK$FILTER_BY_WEBHOOK)}
                </Label>
                <Select
                  value={selectedWebhookId || "all"}
                  onValueChange={handleFilterChange}
                >
                  <SelectTrigger id="webhook-filter">
                    <SelectValue placeholder={t(I18nKey.WEBHOOK$ALL_WEBHOOKS)} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">
                      {t(I18nKey.WEBHOOK$ALL_WEBHOOKS)}
                    </SelectItem>
                    {webhooks?.map((webhook) => (
                      <SelectItem key={webhook.webhook_id} value={webhook.webhook_id}>
                        {webhook.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          {isLoading ? (
            <div className="py-8 text-center text-muted-foreground">
              {t(I18nKey.COMMON$LOADING)}...
            </div>
          ) : logs && logs.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t(I18nKey.WEBHOOK$EVENT_TYPE)}</TableHead>
                  <TableHead>{t(I18nKey.WEBHOOK$REPOSITORY)}</TableHead>
                  <TableHead>{t(I18nKey.WEBHOOK$PR_NUMBER)}</TableHead>
                  <TableHead>{t(I18nKey.WEBHOOK$STATUS)}</TableHead>
                  <TableHead>{t(I18nKey.WEBHOOK$RESPONSE_CODE)}</TableHead>
                  <TableHead>{t(I18nKey.WEBHOOK$TIMESTAMP)}</TableHead>
                  <TableHead>{t(I18nKey.COMMON$ACTIONS)}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {logs.map((log) => (
                  <TableRow key={log.log_id}>
                    <TableCell>
                      <Badge variant="outline">{log.event_type}</Badge>
                    </TableCell>
                    <TableCell>
                      {log.repository || t(I18nKey.WEBHOOK$NOT_SPECIFIED)}
                    </TableCell>
                    <TableCell>
                      {log.pr_number ? `#${log.pr_number}` : "-"}
                    </TableCell>
                    <TableCell>
                      <Badge variant={getStatusBadgeVariant(log.status)}>
                        {log.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {log.response_status || "-"}
                    </TableCell>
                    <TableCell>
                      {formatDate(new Date(log.created_at))}
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleViewLog(log)}
                      >
                        <EyeIcon className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="py-8 text-center text-muted-foreground">
              {t(I18nKey.WEBHOOK$NO_LOGS_FOUND)}
            </div>
          )}
        </CardContent>
      </Card>

      {selectedLog && (
        <Dialog open={!!selectedLog} onOpenChange={(open) => !open && setSelectedLog(null)}>
          <DialogContent className="sm:max-w-[600px]">
            <DialogHeader>
              <DialogTitle>{t(I18nKey.WEBHOOK$LOG_DETAILS)}</DialogTitle>
              <DialogDescription>
                {t(I18nKey.WEBHOOK$LOG_DETAILS_DESCRIPTION)}
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>{t(I18nKey.WEBHOOK$EVENT_TYPE)}</Label>
                  <div className="mt-1">
                    <Badge variant="outline">{selectedLog.event_type}</Badge>
                  </div>
                </div>
                <div>
                  <Label>{t(I18nKey.WEBHOOK$STATUS)}</Label>
                  <div className="mt-1">
                    <Badge variant={getStatusBadgeVariant(selectedLog.status)}>
                      {selectedLog.status}
                    </Badge>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>{t(I18nKey.WEBHOOK$REPOSITORY)}</Label>
                  <Input
                    readOnly
                    value={selectedLog.repository || t(I18nKey.WEBHOOK$NOT_SPECIFIED)}
                  />
                </div>
                <div>
                  <Label>{t(I18nKey.WEBHOOK$PR_NUMBER)}</Label>
                  <Input
                    readOnly
                    value={selectedLog.pr_number ? `#${selectedLog.pr_number}` : "-"}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>{t(I18nKey.WEBHOOK$RESPONSE_CODE)}</Label>
                  <Input
                    readOnly
                    value={selectedLog.response_status?.toString() || "-"}
                  />
                </div>
                <div>
                  <Label>{t(I18nKey.WEBHOOK$TIMESTAMP)}</Label>
                  <Input
                    readOnly
                    value={formatDate(new Date(selectedLog.created_at))}
                  />
                </div>
              </div>

              {selectedLog.error_message && (
                <div>
                  <Label>{t(I18nKey.WEBHOOK$ERROR_MESSAGE)}</Label>
                  <div className="mt-1 p-2 bg-destructive/10 text-destructive rounded border border-destructive/20">
                    {selectedLog.error_message}
                  </div>
                </div>
              )}
            </div>
          </DialogContent>
        </Dialog>
      )}
    </>
  );
}