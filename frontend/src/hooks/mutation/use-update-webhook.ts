import { useMutation, useQueryClient } from "@tanstack/react-query";
import { webhookApi } from "#/api/webhook-api";
import { WebhookUpdateRequest } from "#/types/webhook";

/**
 * Hook to update an existing webhook configuration
 */
export function useUpdateWebhook() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (webhook: WebhookUpdateRequest) => webhookApi.updateWebhook(webhook),
    onSuccess: (data) => {
      // Invalidate the specific webhook query
      queryClient.invalidateQueries({ queryKey: ["webhooks", data.webhook_id] });
      // Invalidate the webhooks list query
      queryClient.invalidateQueries({ queryKey: ["webhooks"] });
    },
  });
}