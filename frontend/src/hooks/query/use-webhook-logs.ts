import { useQuery } from "@tanstack/react-query";
import { webhookApi } from "#/api/webhook-api";

interface UseWebhookLogsParams {
  webhookId?: string;
  limit?: number;
}

/**
 * Hook to fetch webhook logs, optionally filtered by webhook ID
 */
export function useWebhookLogs(params?: UseWebhookLogsParams) {
  return useQuery({
    queryKey: ["webhook-logs", params?.webhookId, params?.limit],
    queryFn: () => webhookApi.getWebhookLogs(params),
  });
}

/**
 * Hook to fetch a specific webhook log by ID
 */
export function useWebhookLog(logId: string) {
  return useQuery({
    queryKey: ["webhook-logs", "detail", logId],
    queryFn: () => webhookApi.getWebhookLog(logId),
    enabled: !!logId,
  });
}