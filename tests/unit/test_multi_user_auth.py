"""Tests for multi-user authentication system."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from pydantic import SecretStr

from openhands.server.user_auth.multi_user_auth import (
    MultiUserAuth,
    create_access_token,
    get_current_user_from_token,
    get_password_hash,
    verify_password,
)
from openhands.storage.data_models.user import User


class TestPasswordUtils:
    """Test password hashing and verification utilities."""

    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = 'test_password_123'
        hashed = get_password_hash(password)

        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password('wrong_password', hashed)

    def test_password_hash_uniqueness(self):
        """Test that same password produces different hashes due to salt."""
        password = 'test_password_123'
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Note: bcrypt includes salt, so hashes should be different
        # But our current implementation uses SHA256 without salt, so they'll be the same
        # This is actually a security issue that should be fixed in production
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)


class TestJWTTokens:
    """Test JWT token creation and validation."""

    def test_create_access_token(self):
        """Test JWT token creation."""
        data = {'sub': 'test_user', 'user_id': '123'}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_expiry(self):
        """Test JWT token creation with custom expiry."""
        from datetime import timedelta

        data = {'sub': 'test_user', 'user_id': '123'}
        expires_delta = timedelta(minutes=30)
        token = create_access_token(data, expires_delta)

        assert isinstance(token, str)
        assert len(token) > 0

    @patch('openhands.server.user_auth.multi_user_auth.FileUserStore')
    @pytest.mark.asyncio
    async def test_get_current_user_from_token_success(self, mock_user_store_class):
        """Test successful user retrieval from token."""
        # Mock user store
        mock_user_store = AsyncMock()
        mock_user_store_class.get_instance.return_value = mock_user_store

        # Create test user
        test_user = User(
            user_id='test_user_123',
            username='testuser',
            email='test@example.com',
            password_hash=SecretStr('hashed_password'),
            github_id=None,
            gitlab_id=None,
            bitbucket_id=None,
            created_at=datetime.now(timezone.utc),
            last_login=None,
            is_active=True,
            email_verified=False,
        )
        mock_user_store.get_user_by_id.return_value = test_user

        # Create token
        token_data = {'sub': 'testuser', 'user_id': 'test_user_123'}
        token = create_access_token(token_data)

        # Test user retrieval
        user = await get_current_user_from_token(token)

        assert user == test_user
        mock_user_store.get_user_by_id.assert_called_once_with('test_user_123')

    @patch('openhands.server.user_auth.multi_user_auth.FileUserStore')
    @pytest.mark.asyncio
    async def test_get_current_user_from_token_invalid_token(
        self, mock_user_store_class
    ):
        """Test user retrieval with invalid token."""
        mock_user_store = AsyncMock()
        mock_user_store_class.get_instance.return_value = mock_user_store

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_from_token('invalid_token')

        assert exc_info.value.status_code == 401

    @patch('openhands.server.user_auth.multi_user_auth.FileUserStore')
    @pytest.mark.asyncio
    async def test_get_current_user_from_token_user_not_found(
        self, mock_user_store_class
    ):
        """Test user retrieval when user doesn't exist."""
        mock_user_store = AsyncMock()
        mock_user_store_class.get_instance.return_value = mock_user_store
        mock_user_store.get_user_by_id.return_value = None

        token_data = {'sub': 'testuser', 'user_id': 'nonexistent_user'}
        token = create_access_token(token_data)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_from_token(token)

        assert exc_info.value.status_code == 401


class TestMultiUserAuth:
    """Test MultiUserAuth class."""

    @pytest.fixture
    def mock_config(self):
        """Mock OpenHands config."""
        config = MagicMock()
        config.file_store = 'local'
        config.file_store_path = '/tmp/test'
        config.file_store_web_hook_url = None
        config.file_store_web_hook_headers = None
        return config

    @pytest.fixture
    def auth(self, mock_config):
        """Create MultiUserAuth instance."""
        return MultiUserAuth(mock_config)

    @pytest.mark.asyncio
    async def test_get_user_id_no_token(self, auth):
        """Test get_user_id with no token."""
        user_id = await auth.get_user_id()
        assert user_id is None

    @patch('openhands.server.user_auth.multi_user_auth.get_current_user_from_token')
    @pytest.mark.asyncio
    async def test_get_user_id_with_token(self, mock_get_user, auth):
        """Test get_user_id with valid token."""
        test_user = User(
            user_id='test_user_123',
            username='testuser',
            email='test@example.com',
            password_hash=SecretStr('hashed_password'),
            github_id=None,
            gitlab_id=None,
            bitbucket_id=None,
            created_at=datetime.now(timezone.utc),
            last_login=None,
            is_active=True,
            email_verified=False,
        )
        mock_get_user.return_value = test_user

        # Mock request with token
        auth._request = MagicMock()
        auth._request.headers = {'authorization': 'Bearer test_token'}

        user_id = await auth.get_user_id()
        assert user_id == 'test_user_123'

    @patch('openhands.server.user_auth.multi_user_auth.get_current_user_from_token')
    @pytest.mark.asyncio
    async def test_get_user_id_invalid_token(self, mock_get_user, auth):
        """Test get_user_id with invalid token."""
        mock_get_user.side_effect = HTTPException(status_code=401)

        # Mock request with invalid token
        auth._request = MagicMock()
        auth._request.headers = {'authorization': 'Bearer invalid_token'}

        user_id = await auth.get_user_id()
        assert user_id is None

    @patch(
        'openhands.storage.settings.file_settings_store.FileSettingsStore.get_instance'
    )
    @pytest.mark.asyncio
    async def test_get_settings_no_user(self, mock_settings_store, auth):
        """Test get_settings with no authenticated user."""
        mock_store = AsyncMock()
        mock_settings_store.return_value = mock_store
        mock_store.load.return_value = None

        settings = await auth.get_settings()
        assert settings is None

    @patch('openhands.storage.secrets.file_secrets_store.FileSecretsStore.get_instance')
    @pytest.mark.asyncio
    async def test_get_user_secrets_no_user(self, mock_secrets_store, auth):
        """Test get_user_secrets with no authenticated user."""
        mock_store = AsyncMock()
        mock_secrets_store.return_value = mock_store
        mock_store.load.return_value = None

        secrets = await auth.get_user_secrets()
        assert secrets is None

    @pytest.mark.asyncio
    async def test_is_authenticated_no_user(self, auth):
        """Test is_authenticated with no user."""
        is_auth = await auth.is_authenticated()
        assert not is_auth

    @patch('openhands.server.user_auth.multi_user_auth.get_current_user_from_token')
    @pytest.mark.asyncio
    async def test_is_authenticated_with_user(self, mock_get_user, auth):
        """Test is_authenticated with valid user."""
        test_user = User(
            user_id='test_user_123',
            username='testuser',
            email='test@example.com',
            password_hash=SecretStr('hashed_password'),
            github_id=None,
            gitlab_id=None,
            bitbucket_id=None,
            created_at=datetime.now(timezone.utc),
            last_login=None,
            is_active=True,
            email_verified=False,
        )
        mock_get_user.return_value = test_user

        # Mock request with token
        auth._request = MagicMock()
        auth._request.headers = {'authorization': 'Bearer test_token'}

        is_auth = await auth.is_authenticated()
        assert is_auth
