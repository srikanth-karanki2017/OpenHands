/**
 * Types for webhook management
 */

export enum WebhookEventType {
  ALL = "all",
  PULL_REQUEST = "pull_request",
  PUSH = "push",
  ISSUE = "issue",
  COMMENT = "comment",
}

export enum WebhookStatus {
  ACTIVE = "active",
  INACTIVE = "inactive",
}

export enum WebhookLogStatus {
  SUCCESS = "success",
  FAILURE = "failure",
  PENDING = "pending",
}

export interface WebhookConfig {
  webhook_id: string;
  name: string;
  url: URL;
  events: WebhookEventType[];
  repository?: string;
  status: WebhookStatus;
  created_at: string;
  updated_at: string;
}

export interface WebhookLog {
  log_id: string;
  webhook_id: string;
  event_type: WebhookEventType;
  repository?: string;
  pr_number?: number;
  status: WebhookLogStatus;
  response_status?: number;
  error_message?: string;
  created_at: string;
}

export interface WebhookCreateRequest {
  name: string;
  url: string;
  events: string[];
  repository?: string;
  secret?: string;
  status?: WebhookStatus;
}

export interface WebhookUpdateRequest {
  webhook_id: string;
  name?: string;
  url?: string;
  events?: string[];
  repository?: string;
  secret?: string;
  status?: WebhookStatus;
}