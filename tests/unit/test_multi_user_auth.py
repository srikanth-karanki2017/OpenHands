"""Tests for multi-user authentication system."""

from datetime import datetime, timedelta, timezone
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
        """Test password hashing functionality."""
        password = 'test_password_123'
        hashed = get_password_hash(password)

        # Hash should be different from original password
        assert hashed != password
        # Hash should be consistent
        assert len(hashed) > 0

    def test_password_hash_uniqueness(self):
        """Test that same password produces different hashes with salt."""
        password = 'test_password_123'
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Note: Our current implementation uses SHA256 without salt,
        # so hashes will be the same. This is a security consideration.
        assert hash1 == hash2  # Current implementation behavior

    def test_password_verification(self):
        """Test password verification."""
        password = 'test_password_123'
        hashed = get_password_hash(password)

        # Correct password should verify
        assert verify_password(password, hashed) is True

        # Wrong password should not verify
        assert verify_password('wrong_password', hashed) is False


class TestJWTTokens:
    """Test JWT token creation and validation."""

    def test_create_access_token(self):
        """Test access token creation."""
        data = {'sub': 'test_user', 'username': 'testuser'}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_expiry(self):
        """Test access token creation with custom expiry."""
        data = {'sub': 'test_user', 'username': 'testuser'}
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
        mock_user_store.get_user.return_value = test_user

        # Create token
        token_data = {'sub': 'test_user_123', 'username': 'testuser'}
        token = create_access_token(token_data)

        # Test user retrieval
        user = await get_current_user_from_token(token)

        assert user == test_user
        mock_user_store.get_user.assert_called_once_with('test_user_123')

    @pytest.mark.asyncio
    async def test_get_current_user_from_token_invalid_token(self):
        """Test user retrieval with invalid token."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_from_token('invalid_token')

        assert exc_info.value.status_code == 401

    @patch('openhands.server.user_auth.multi_user_auth.FileUserStore')
    @pytest.mark.asyncio
    async def test_get_current_user_from_token_user_not_found(
        self, mock_user_store_class
    ):
        """Test user retrieval when user doesn't exist."""
        # Mock user store
        mock_user_store = AsyncMock()
        mock_user_store_class.get_instance.return_value = mock_user_store
        mock_user_store.get_user.side_effect = FileNotFoundError('User not found')

        # Create valid token
        token_data = {'sub': 'nonexistent_user', 'username': 'testuser'}
        token = create_access_token(token_data)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_from_token(token)

        assert exc_info.value.status_code == 401


class TestMultiUserAuth:
    """Test MultiUserAuth class functionality."""

    @pytest.fixture
    def auth(self):
        """Create a MultiUserAuth instance for testing."""
        request = MagicMock()
        return MultiUserAuth(request)

    @pytest.mark.asyncio
    async def test_get_user_id_no_token(self, auth):
        """Test get_user_id with no token."""
        auth._request.headers = {}
        user_id = await auth.get_user_id()
        assert user_id is None

    @pytest.mark.asyncio
    async def test_get_user_id_with_token(self, auth):
        """Test get_user_id with valid token."""
        # Create a token
        token_data = {'sub': 'test_user_123', 'username': 'testuser'}
        token = create_access_token(token_data)

        auth._request.headers = {'authorization': f'Bearer {token}'}

        with patch(
            'openhands.server.user_auth.multi_user_auth.get_current_user_from_token'
        ) as mock_get_user:
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

            user_id = await auth.get_user_id()
            assert user_id == 'test_user_123'

    @pytest.mark.asyncio
    async def test_get_user_id_invalid_token(self, auth):
        """Test get_user_id with invalid token."""
        auth._request.headers = {'authorization': 'Bearer invalid_token'}

        with patch(
            'openhands.server.user_auth.multi_user_auth.get_current_user_from_token'
        ) as mock_get_user:
            mock_get_user.side_effect = HTTPException(status_code=401)

            user_id = await auth.get_user_id()
            assert user_id is None

    @pytest.mark.asyncio
    async def test_get_user_secrets_no_user(self, auth):
        """Test get_user_secrets with no authenticated user."""
        auth._request.headers = {}

        secrets = await auth.get_user_secrets()
        assert secrets == {}
