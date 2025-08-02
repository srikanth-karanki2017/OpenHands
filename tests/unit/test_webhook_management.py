"""Tests for webhook management system."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from pydantic import HttpUrl, SecretStr

from openhands.storage.data_models.webhook_config import (
    WebhookConfig,
    WebhookEventType,
    WebhookLog,
    WebhookLogStatus,
)
from openhands.storage.webhook.webhook_store import (
    WebhookStore,
    create_webhook_config,
    create_webhook_log,
)


class TestWebhookConfigCreation:
    """Test webhook configuration creation utilities."""

    def test_create_webhook_config(self):
        """Test webhook configuration creation."""
        user_id = 'test_user_123'
        name = 'Test Webhook'
        url = 'https://example.com/webhook'
        events = [WebhookEventType.PULL_REQUEST_OPENED]
        repository = 'owner/repo'
        secret = 'webhook_secret'

        config = create_webhook_config(
            user_id=user_id,
            name=name,
            url=url,
            events=events,
            repository=repository,
            secret=secret,
        )

        assert config.user_id == user_id
        assert config.name == name
        assert config.url == HttpUrl(url)
        assert config.events == events
        assert config.repository == repository
        assert config.secret.get_secret_value() == secret
        assert config.webhook_id is not None

    def test_create_webhook_config_minimal(self):
        """Test webhook configuration creation with minimal parameters."""
        user_id = 'test_user_123'
        name = 'Test Webhook'
        url = 'https://example.com/webhook'
        events = [WebhookEventType.PULL_REQUEST_OPENED]

        config = create_webhook_config(
            user_id=user_id,
            name=name,
            url=url,
            events=events,
        )

        assert config.user_id == user_id
        assert config.name == name
        assert config.url == HttpUrl(url)
        assert config.events == events
        assert config.repository is None
        assert config.secret is None
        assert config.webhook_id is not None


class TestWebhookLogCreation:
    """Test webhook log creation utilities."""

    def test_create_webhook_log(self):
        """Test webhook log creation."""
        webhook_id = str(uuid4())
        user_id = 'test_user_123'
        event_type = WebhookEventType.PULL_REQUEST_OPENED
        repository = 'owner/repo'
        pr_number = 42
        status = WebhookLogStatus.SUCCESS
        request_payload = {'action': 'opened', 'number': 42}

        log = create_webhook_log(
            webhook_id=webhook_id,
            user_id=user_id,
            event_type=event_type,
            repository=repository,
            pr_number=pr_number,
            status=status,
            request_payload=request_payload,
        )

        assert log.webhook_id == webhook_id
        assert log.user_id == user_id
        assert log.event_type == event_type
        assert log.repository == repository
        assert log.pr_number == pr_number
        assert log.status == status
        assert log.request_payload == request_payload
        assert log.log_id is not None
        assert log.response_status is None
        assert log.response_body is None
        assert log.error_message is None

    def test_create_webhook_log_minimal(self):
        """Test webhook log creation with minimal parameters."""
        webhook_id = str(uuid4())
        user_id = 'test_user_123'
        event_type = WebhookEventType.PULL_REQUEST_OPENED

        log = create_webhook_log(
            webhook_id=webhook_id,
            user_id=user_id,
            event_type=event_type,
        )

        assert log.webhook_id == webhook_id
        assert log.user_id == user_id
        assert log.event_type == event_type
        assert log.repository is None
        assert log.pr_number is None
        assert log.status == WebhookLogStatus.PENDING
        assert log.request_payload == {}
        assert log.log_id is not None


class TestWebhookStore:
    """Test WebhookStore class."""

    @pytest.fixture
    def mock_file_store(self):
        """Mock file store."""
        return MagicMock()

    @pytest.fixture
    def webhook_store(self, mock_file_store):
        """Create WebhookStore instance."""
        return WebhookStore(mock_file_store, 'test_user_123')

    @pytest.fixture
    def sample_webhook_config(self):
        """Sample webhook configuration."""
        return WebhookConfig(
            webhook_id=str(uuid4()),
            user_id='test_user_123',
            name='Test Webhook',
            url=HttpUrl('https://example.com/webhook'),
            events=[WebhookEventType.PULL_REQUEST_OPENED],
            repository='owner/repo',
            secret=SecretStr('webhook_secret'),
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    @pytest.fixture
    def sample_webhook_log(self, sample_webhook_config):
        """Sample webhook log."""
        return WebhookLog(
            log_id=str(uuid4()),
            webhook_id=sample_webhook_config.webhook_id,
            user_id='test_user_123',
            event_type=WebhookEventType.PULL_REQUEST_OPENED,
            repository='owner/repo',
            pr_number=42,
            status=WebhookLogStatus.SUCCESS,
            request_payload={'action': 'opened', 'number': 42},
            response_status=200,
            response_body='OK',
            error_message=None,
            created_at=datetime.now(timezone.utc),
        )

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_save_webhook_config(self, webhook_store, sample_webhook_config):
        """Test saving webhook configuration."""
        with patch('openhands.utils.async_utils.call_sync_from_async') as mock_call:
            await webhook_store.save_webhook_config(sample_webhook_config)

            # Verify file store write was called
            mock_call.assert_called()
            args = mock_call.call_args[0]
            assert args[0] == webhook_store.file_store.write

    @pytest.mark.asyncio
    async def test_get_webhook_config(self, webhook_store, sample_webhook_config):
        """Test getting webhook configuration."""
        webhook_data = sample_webhook_config.model_dump_json()

        with patch('openhands.utils.async_utils.call_sync_from_async') as mock_call:
            mock_call.return_value = webhook_data

            result = await webhook_store.get_webhook_config(
                sample_webhook_config.webhook_id
            )

            assert result is not None
            assert result.webhook_id == sample_webhook_config.webhook_id
            assert result.name == sample_webhook_config.name

    @pytest.mark.asyncio
    async def test_get_webhook_config_not_found(self, webhook_store):
        """Test getting non-existent webhook configuration."""
        with patch('openhands.utils.async_utils.call_sync_from_async') as mock_call:
            mock_call.side_effect = FileNotFoundError()

            result = await webhook_store.get_webhook_config('nonexistent_id')
            assert result is None

    @pytest.mark.asyncio
    async def test_list_webhook_configs(self, webhook_store, sample_webhook_config):
        """Test listing webhook configurations."""
        webhook_data = sample_webhook_config.model_dump_json()

        with patch('openhands.utils.async_utils.call_sync_from_async') as mock_call:
            # Mock file store list to return one webhook file
            webhook_store.file_store.list.return_value = [
                f'webhooks/{sample_webhook_config.webhook_id}.json'
            ]
            mock_call.return_value = webhook_data

            configs = await webhook_store.list_webhook_configs()

            assert len(configs) == 1
            assert configs[0].webhook_id == sample_webhook_config.webhook_id

    @pytest.mark.asyncio
    async def test_delete_webhook_config(self, webhook_store, sample_webhook_config):
        """Test deleting webhook configuration."""
        with patch('openhands.utils.async_utils.call_sync_from_async') as mock_call:
            await webhook_store.delete_webhook_config(sample_webhook_config.webhook_id)

            # Verify file store delete was called
            mock_call.assert_called()
            args = mock_call.call_args[0]
            assert args[0] == webhook_store.file_store.delete

    @pytest.mark.asyncio
    async def test_save_webhook_log(self, webhook_store, sample_webhook_log):
        """Test saving webhook log."""
        with patch('openhands.utils.async_utils.call_sync_from_async') as mock_call:
            await webhook_store.save_webhook_log(sample_webhook_log)

            # Verify file store write was called
            mock_call.assert_called()
            args = mock_call.call_args[0]
            assert args[0] == webhook_store.file_store.write

    @pytest.mark.asyncio
    async def test_get_webhook_log(self, webhook_store, sample_webhook_log):
        """Test getting webhook log."""
        log_data = sample_webhook_log.model_dump_json()

        with patch('openhands.utils.async_utils.call_sync_from_async') as mock_call:
            mock_call.return_value = log_data

            result = await webhook_store.get_webhook_log(sample_webhook_log.log_id)

            assert result is not None
            assert result.log_id == sample_webhook_log.log_id
            assert result.webhook_id == sample_webhook_log.webhook_id

    @pytest.mark.asyncio
    async def test_get_webhook_log_not_found(self, webhook_store):
        """Test getting non-existent webhook log."""
        with patch('openhands.utils.async_utils.call_sync_from_async') as mock_call:
            mock_call.side_effect = FileNotFoundError()

            result = await webhook_store.get_webhook_log('nonexistent_id')
            assert result is None

    @pytest.mark.asyncio
    async def test_list_webhook_logs(self, webhook_store, sample_webhook_log):
        """Test listing webhook logs."""
        log_data = sample_webhook_log.model_dump_json()

        with patch('openhands.utils.async_utils.call_sync_from_async') as mock_call:
            # Mock file store list to return one log file
            webhook_store.file_store.list.return_value = [
                f'webhook_logs/{sample_webhook_log.log_id}.json'
            ]
            mock_call.return_value = log_data

            logs = await webhook_store.list_webhook_logs()

            assert len(logs) == 1
            assert logs[0].log_id == sample_webhook_log.log_id

    @pytest.mark.asyncio
    async def test_list_webhook_logs_with_limit(
        self, webhook_store, sample_webhook_log
    ):
        """Test listing webhook logs with limit."""
        log_data = sample_webhook_log.model_dump_json()

        with patch('openhands.utils.async_utils.call_sync_from_async') as mock_call:
            # Mock file store list to return multiple log files
            webhook_store.file_store.list.return_value = [
                f'webhook_logs/{uuid4()}.json',
                f'webhook_logs/{uuid4()}.json',
                f'webhook_logs/{sample_webhook_log.log_id}.json',
            ]
            mock_call.return_value = log_data

            logs = await webhook_store.list_webhook_logs(limit=2)

            assert len(logs) == 2

    @pytest.mark.asyncio
    async def test_get_instance(self):
        """Test WebhookStore.get_instance class method."""
        mock_config = MagicMock()
        mock_config.file_store = 'local'
        mock_config.file_store_path = '/tmp/test'
        mock_config.file_store_web_hook_url = None
        mock_config.file_store_web_hook_headers = None

        with patch(
            'openhands.storage.webhook.webhook_store.get_file_store'
        ) as mock_get_store:
            mock_file_store = MagicMock()
            mock_get_store.return_value = mock_file_store

            store = await WebhookStore.get_instance(mock_config, 'test_user_123')

            assert isinstance(store, WebhookStore)
            assert store.user_id == 'test_user_123'
            assert store.file_store == mock_file_store

            mock_get_store.assert_called_once_with(
                'local',
                '/tmp/test',
                None,
                None,
            )
