from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl, SecretStr


class WebhookEventType(str, Enum):
    """
    Types of events that can trigger a webhook.
    """

    PULL_REQUEST = 'pull_request'
    PUSH = 'push'
    ISSUE = 'issue'
    COMMENT = 'comment'
    ALL = 'all'


class WebhookStatus(str, Enum):
    """
    Status of a webhook.
    """

    ACTIVE = 'active'
    INACTIVE = 'inactive'


class WebhookConfig(BaseModel):
    """
    Configuration for a webhook.

    This model represents a webhook configuration that can be triggered by
    various events in the OpenHands system.
    """

    webhook_id: str = Field(..., description='Unique identifier for the webhook')
    user_id: str = Field(..., description='User ID that owns this webhook')
    name: str = Field(..., description='Display name for the webhook')
    url: HttpUrl = Field(..., description='URL to send webhook requests to')
    events: list[WebhookEventType] = Field(
        default_factory=lambda: [WebhookEventType.ALL],
        description='Events that trigger this webhook',
    )
    repository: str | None = Field(
        None, description='Repository to filter events for (format: owner/repo)'
    )
    secret: SecretStr | None = Field(
        None, description='Secret used to sign webhook payloads'
    )
    status: WebhookStatus = Field(
        default=WebhookStatus.ACTIVE, description='Status of the webhook'
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description='When the webhook was created',
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description='When the webhook was last updated',
    )


class WebhookLogStatus(str, Enum):
    """
    Status of a webhook delivery.
    """

    SUCCESS = 'success'
    FAILURE = 'failure'
    PENDING = 'pending'


class WebhookLog(BaseModel):
    """
    Log of a webhook delivery.

    This model represents a log entry for a webhook delivery, including
    the request and response details.
    """

    log_id: str = Field(..., description='Unique identifier for the log entry')
    webhook_id: str = Field(..., description='ID of the webhook that was triggered')
    user_id: str = Field(..., description='User ID that owns this webhook')
    event_type: WebhookEventType = Field(
        ..., description='Type of event that triggered the webhook'
    )
    repository: str | None = Field(
        None, description='Repository that triggered the event (format: owner/repo)'
    )
    pr_number: int | None = Field(
        None, description='Pull request number (if applicable)'
    )
    status: WebhookLogStatus = Field(..., description='Status of the webhook delivery')
    request_payload: dict = Field(
        ..., description='Payload sent in the webhook request'
    )
    response_status: int | None = Field(
        None, description='HTTP status code of the response'
    )
    response_body: str | None = Field(
        None, description='Response body from the webhook delivery'
    )
    error_message: str | None = Field(
        None, description='Error message if the delivery failed'
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description='When the webhook was triggered',
    )


class WebhookConfigCreate(BaseModel):
    """
    Model for creating a new webhook configuration.
    """

    name: str = Field(..., min_length=1, max_length=100)
    url: HttpUrl
    events: list[WebhookEventType] = Field(
        default_factory=lambda: [WebhookEventType.ALL]
    )
    repository: str | None = None
    secret: SecretStr | None = None


class WebhookConfigUpdate(BaseModel):
    """
    Model for updating an existing webhook configuration.
    """

    name: str | None = Field(None, min_length=1, max_length=100)
    url: HttpUrl | None = None
    events: list[WebhookEventType] | None = None
    repository: str | None = None
    secret: SecretStr | None = None
    status: WebhookStatus | None = None


class WebhookConfigResponse(BaseModel):
    """
    Model for webhook configuration information returned to the client.
    """

    webhook_id: str
    name: str
    url: HttpUrl
    events: list[WebhookEventType]
    repository: str | None = None
    status: WebhookStatus
    created_at: datetime
    updated_at: datetime


class WebhookLogResponse(BaseModel):
    """
    Model for webhook log information returned to the client.
    """

    log_id: str
    webhook_id: str
    event_type: WebhookEventType
    repository: str | None = None
    pr_number: int | None = None
    status: WebhookLogStatus
    response_status: int | None = None
    error_message: str | None = None
    created_at: datetime
