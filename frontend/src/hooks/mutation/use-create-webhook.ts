import { useMutation, useQueryClient } from "@tanstack/react-query";
import { webhookApi } from "#/api/webhook-api";
import { WebhookCreateRequest } from "#/types/webhook";

/**
 * Hook to create a new webhook configuration
 */
export function useCreateWebhook() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (webhook: WebhookCreateRequest) => webhookApi.createWebhook(webhook),
    onSuccess: () => {
      // Invalidate the webhooks query to refetch the list
      queryClient.invalidateQueries({ queryKey: ["webhooks"] });
    },
  });
}