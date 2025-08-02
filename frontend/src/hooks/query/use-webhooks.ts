import { useQuery } from "@tanstack/react-query";
import { webhookApi } from "#/api/webhook-api";

/**
 * Hook to fetch all webhook configurations for the current user
 */
export function useWebhooks() {
  return useQuery({
    queryKey: ["webhooks"],
    queryFn: () => webhookApi.getWebhooks(),
  });
}

/**
 * Hook to fetch a specific webhook configuration by ID
 */
export function useWebhook(webhookId: string) {
  return useQuery({
    queryKey: ["webhooks", webhookId],
    queryFn: () => webhookApi.getWebhook(webhookId),
    enabled: !!webhookId,
  });
}
