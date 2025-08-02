from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone

from pydantic import HttpUrl, SecretStr, TypeAdapter

from openhands.core.config.openhands_config import OpenHandsConfig
from openhands.core.logger import openhands_logger as logger
from openhands.storage import get_file_store
from openhands.storage.data_models.webhook_config import (
    WebhookConfig,
    WebhookEventType,
    WebhookLog,
    WebhookLogStatus,
)
from openhands.storage.files import FileStore
from openhands.utils.async_utils import call_sync_from_async

# Base directory for webhook data
WEBHOOK_BASE_DIR = 'webhooks'
WEBHOOK_CONFIG_DIR = f'{WEBHOOK_BASE_DIR}/configs'
WEBHOOK_LOGS_DIR = f'{WEBHOOK_BASE_DIR}/logs'

# Type adapters for serialization/deserialization
webhook_config_type_adapter = TypeAdapter(WebhookConfig)
webhook_log_type_adapter = TypeAdapter(WebhookLog)


class WebhookStore(ABC):
    """Abstract base class for webhook storage.

    This class defines the interface for storing and retrieving webhook configurations
    and logs. Implementations should handle user-specific data isolation.
    """

    @abstractmethod
    async def save_webhook_config(self, config: WebhookConfig) -> None:
        """Store webhook configuration."""
        pass

    @abstractmethod
    async def get_webhook_config(self, webhook_id: str) -> WebhookConfig:
        """Load webhook configuration."""
        pass

    @abstractmethod
    async def delete_webhook_config(self, webhook_id: str) -> None:
        """Delete webhook configuration."""
        pass

    @abstractmethod
    async def list_webhook_configs(self, user_id: str) -> list[WebhookConfig]:
        """List all webhook configurations for a user."""
        pass

    @abstractmethod
    async def save_webhook_log(self, log: WebhookLog) -> None:
        """Store webhook log."""
        pass

    @abstractmethod
    async def get_webhook_log(self, log_id: str) -> WebhookLog:
        """Load webhook log."""
        pass

    @abstractmethod
    async def list_webhook_logs(
        self, user_id: str, webhook_id: str | None = None, limit: int = 50
    ) -> list[WebhookLog]:
        """List webhook logs for a user, optionally filtered by webhook ID."""
        pass

    @classmethod
    @abstractmethod
    async def get_instance(cls, config: OpenHandsConfig, user_id: str) -> WebhookStore:
        """Get a store for the specified user."""
        pass


class FileWebhookStore(WebhookStore):
    """File-based implementation of WebhookStore.

    This class stores webhook configurations and logs as JSON files in the filesystem.
    """

    def __init__(self, file_store: FileStore, user_id: str):
        self.file_store = file_store
        self.user_id = user_id

    def _get_webhook_config_path(self, webhook_id: str) -> str:
        """Get the file path for a webhook configuration."""
        return f'{WEBHOOK_CONFIG_DIR}/{self.user_id}/{webhook_id}.json'

    def _get_webhook_log_path(self, log_id: str) -> str:
        """Get the file path for a webhook log."""
        return f'{WEBHOOK_LOGS_DIR}/{self.user_id}/{log_id}.json'

    def _get_webhook_configs_dir(self) -> str:
        """Get the directory path for a user's webhook configurations."""
        return f'{WEBHOOK_CONFIG_DIR}/{self.user_id}'

    def _get_webhook_logs_dir(self) -> str:
        """Get the directory path for a user's webhook logs."""
        return f'{WEBHOOK_LOGS_DIR}/{self.user_id}'

    async def save_webhook_config(self, config: WebhookConfig) -> None:
        """Store webhook configuration."""
        # Ensure user_id matches
        if config.user_id != self.user_id:
            raise ValueError('Webhook config user_id does not match store user_id')

        # Update the updated_at timestamp
        config.updated_at = datetime.now(timezone.utc)

        # Serialize and save
        json_str = webhook_config_type_adapter.dump_json(config)
        path = self._get_webhook_config_path(config.webhook_id)
        await call_sync_from_async(self.file_store.write, path, json_str)

    async def get_webhook_config(self, webhook_id: str) -> WebhookConfig:
        """Load webhook configuration."""
        path = self._get_webhook_config_path(webhook_id)
        try:
            json_str = await call_sync_from_async(self.file_store.read, path)
            config = webhook_config_type_adapter.validate_json(json_str)

            # Verify user_id matches
            if config.user_id != self.user_id:
                raise ValueError('Webhook config user_id does not match store user_id')

            return config
        except Exception as e:
            logger.error(f'Error loading webhook config: {str(e)}')
            raise FileNotFoundError(f'Webhook config not found: {webhook_id}')

    async def delete_webhook_config(self, webhook_id: str) -> None:
        """Delete webhook configuration."""
        # First verify the webhook belongs to this user
        try:
            await self.get_webhook_config(webhook_id)
        except FileNotFoundError:
            # If it doesn't exist, nothing to delete
            return

        # Delete the file
        path = self._get_webhook_config_path(webhook_id)
        await call_sync_from_async(self.file_store.delete, path)

    async def list_webhook_configs(self, user_id: str) -> list[WebhookConfig]:
        """List all webhook configurations for a user."""
        # Verify user_id matches
        if user_id != self.user_id:
            raise ValueError('Requested user_id does not match store user_id')

        # Get all files in the user's webhook config directory
        dir_path = self._get_webhook_configs_dir()
        try:
            files = await call_sync_from_async(self.file_store.list, dir_path)
        except FileNotFoundError:
            # If directory doesn't exist, return empty list
            return []

        # Load each config
        configs = []
        for file_path in files:
            if not file_path.endswith('.json'):
                continue

            try:
                json_str = await call_sync_from_async(self.file_store.read, file_path)
                config = webhook_config_type_adapter.validate_json(json_str)

                # Verify user_id matches
                if config.user_id == self.user_id:
                    configs.append(config)
            except Exception as e:
                logger.error(f'Error loading webhook config from {file_path}: {str(e)}')
                continue

        return configs

    async def save_webhook_log(self, log: WebhookLog) -> None:
        """Store webhook log."""
        # Ensure user_id matches
        if log.user_id != self.user_id:
            raise ValueError('Webhook log user_id does not match store user_id')

        # Serialize and save
        json_str = webhook_log_type_adapter.dump_json(log)
        path = self._get_webhook_log_path(log.log_id)
        await call_sync_from_async(self.file_store.write, path, json_str)

    async def get_webhook_log(self, log_id: str) -> WebhookLog:
        """Load webhook log."""
        path = self._get_webhook_log_path(log_id)
        try:
            json_str = await call_sync_from_async(self.file_store.read, path)
            log = webhook_log_type_adapter.validate_json(json_str)

            # Verify user_id matches
            if log.user_id != self.user_id:
                raise ValueError('Webhook log user_id does not match store user_id')

            return log
        except Exception as e:
            logger.error(f'Error loading webhook log: {str(e)}')
            raise FileNotFoundError(f'Webhook log not found: {log_id}')

    async def list_webhook_logs(
        self, user_id: str, webhook_id: str | None = None, limit: int = 50
    ) -> list[WebhookLog]:
        """List webhook logs for a user, optionally filtered by webhook ID."""
        # Verify user_id matches
        if user_id != self.user_id:
            raise ValueError('Requested user_id does not match store user_id')

        # Get all files in the user's webhook logs directory
        dir_path = self._get_webhook_logs_dir()
        try:
            files = await call_sync_from_async(self.file_store.list, dir_path)
        except FileNotFoundError:
            # If directory doesn't exist, return empty list
            return []

        # Load each log
        logs = []
        for file_path in files:
            if not file_path.endswith('.json'):
                continue

            try:
                json_str = await call_sync_from_async(self.file_store.read, file_path)
                log = webhook_log_type_adapter.validate_json(json_str)

                # Verify user_id matches and filter by webhook_id if provided
                if log.user_id == self.user_id and (
                    webhook_id is None or log.webhook_id == webhook_id
                ):
                    logs.append(log)

                    # Stop if we've reached the limit
                    if len(logs) >= limit:
                        break
            except Exception as e:
                logger.error(f'Error loading webhook log from {file_path}: {str(e)}')
                continue

        # Sort by created_at (newest first)
        logs.sort(key=lambda x: x.created_at, reverse=True)

        return logs[:limit]

    @classmethod
    async def get_instance(cls, config: OpenHandsConfig, user_id: str) -> WebhookStore:
        """Get a store for the specified user."""
        file_store = get_file_store(
            config.file_store,
            config.file_store_path,
            config.file_store_web_hook_url,
            config.file_store_web_hook_headers,
        )
        return cls(file_store, user_id)


def create_webhook_config(
    user_id: str,
    name: str,
    url: str,
    events: list[WebhookEventType],
    repository: str | None = None,
    secret: str | None = None,
) -> WebhookConfig:
    """Create a new webhook configuration."""
    webhook_id = str(uuid.uuid4())
    return WebhookConfig(
        webhook_id=webhook_id,
        user_id=user_id,
        name=name,
        url=HttpUrl(url),
        events=events,
        repository=repository,
        secret=SecretStr(secret) if secret else None,
    )


def create_webhook_log(
    webhook_id: str,
    user_id: str,
    event_type: WebhookEventType,
    repository: str | None = None,
    pr_number: int | None = None,
    status: WebhookLogStatus = WebhookLogStatus.PENDING,
    request_payload: dict | None = None,
) -> WebhookLog:
    """Create a new webhook log entry."""
    log_id = str(uuid.uuid4())
    if request_payload is None:
        request_payload = {}

    return WebhookLog(
        log_id=log_id,
        webhook_id=webhook_id,
        user_id=user_id,
        event_type=event_type,
        repository=repository,
        pr_number=pr_number,
        status=status,
        request_payload=request_payload,
        response_status=None,
        response_body=None,
        error_message=None,
    )
