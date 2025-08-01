import { useMutation, useQueryClient } from "@tanstack/react-query";
import { webhookApi } from "#/api/webhook-api";

/**
 * Hook to delete a webhook configuration
 */
export function useDeleteWebhook() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (webhookId: string) => webhookApi.deleteWebhook(webhookId),
    onSuccess: () => {
      // Invalidate the webhooks query to refetch the list
      queryClient.invalidateQueries({ queryKey: ["webhooks"] });
    },
  });
}