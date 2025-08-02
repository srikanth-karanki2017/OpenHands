import { apiClient } from "./api-client";
import { WebhookConfig, WebhookCreateRequest, WebhookLog, WebhookUpdateRequest } from "#/types/webhook";

/**
 * API client for webhook management
 */
export const webhookApi = {
  /**
   * Get all webhook configurations for the current user
   */
  getWebhooks: async (): Promise<WebhookConfig[]> => {
    const response = await apiClient.get<WebhookConfig[]>("/api/webhooks/configs");
    return response.data;
  },

  /**
   * Get a specific webhook configuration by ID
   */
  getWebhook: async (webhookId: string): Promise<WebhookConfig> => {
    const response = await apiClient.get<WebhookConfig>(`/api/webhooks/configs/${webhookId}`);
    return response.data;
  },

  /**
   * Create a new webhook configuration
   */
  createWebhook: async (webhook: WebhookCreateRequest): Promise<WebhookConfig> => {
    const response = await apiClient.post<WebhookConfig>("/api/webhooks/configs", webhook);
    return response.data;
  },

  /**
   * Update an existing webhook configuration
   */
  updateWebhook: async (webhook: WebhookUpdateRequest): Promise<WebhookConfig> => {
    const response = await apiClient.patch<WebhookConfig>(
      `/api/webhooks/configs/${webhook.webhook_id}`,
      webhook
    );
    return response.data;
  },

  /**
   * Delete a webhook configuration
   */
  deleteWebhook: async (webhookId: string): Promise<void> => {
    await apiClient.delete(`/api/webhooks/configs/${webhookId}`);
  },

  /**
   * Get webhook logs, optionally filtered by webhook ID
   */
  getWebhookLogs: async (params?: { webhookId?: string; limit?: number }): Promise<WebhookLog[]> => {
    const queryParams = new URLSearchParams();

    if (params?.webhookId) {
      queryParams.append("webhook_id", params.webhookId);
    }

    if (params?.limit) {
      queryParams.append("limit", params.limit.toString());
    }

    const url = `/api/webhooks/logs${queryParams.toString() ? `?${queryParams.toString()}` : ""}`;
    const response = await apiClient.get<WebhookLog[]>(url);
    return response.data;
  },

  /**
   * Get a specific webhook log by ID
   */
  getWebhookLog: async (logId: string): Promise<WebhookLog> => {
    const response = await apiClient.get<WebhookLog>(`/api/webhooks/logs/${logId}`);
    return response.data;
  },
};
