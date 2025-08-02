"""Tests for user store system."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from pydantic import SecretStr

from openhands.storage.data_models.user import User
from openhands.storage.user.user_store import UserStore, create_user


class TestUserStore:
    """Test UserStore class."""

    @pytest.fixture
    def mock_file_store(self):
        """Mock file store."""
        return MagicMock()

    @pytest.fixture
    def user_store(self, mock_file_store):
        """Create UserStore instance."""
        return UserStore(mock_file_store)

    @pytest.fixture
    def sample_user(self):
        """Sample user."""
        return User(
            user_id=str(uuid4()),
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

    @pytest.mark.asyncio
    async def test_save_user(self, user_store, sample_user):
        """Test saving user."""
        with patch('openhands.utils.async_utils.call_sync_from_async') as mock_call:
            await user_store.save_user(sample_user)

            # Verify file store write was called
            mock_call.assert_called()
            args = mock_call.call_args[0]
            assert args[0] == user_store.file_store.write

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, user_store, sample_user):
        """Test getting user by ID."""
        user_data = sample_user.model_dump_json(context={'expose_secrets': True})

        with patch('openhands.utils.async_utils.call_sync_from_async') as mock_call:
            mock_call.return_value = user_data

            result = await user_store.get_user_by_id(sample_user.user_id)

            assert result is not None
            assert result.user_id == sample_user.user_id
            assert result.username == sample_user.username
            assert result.email == sample_user.email

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, user_store):
        """Test getting non-existent user by ID."""
        with patch('openhands.utils.async_utils.call_sync_from_async') as mock_call:
            mock_call.side_effect = FileNotFoundError()

            result = await user_store.get_user_by_id('nonexistent_id')
            assert result is None

    @pytest.mark.asyncio
    async def test_get_user_by_username(self, user_store, sample_user):
        """Test getting user by username."""
        user_data = sample_user.model_dump_json(context={'expose_secrets': True})

        with patch('openhands.utils.async_utils.call_sync_from_async') as mock_call:
            # Mock file store list to return one user file
            user_store.file_store.list.return_value = [
                f'users/{sample_user.user_id}.json'
            ]
            mock_call.return_value = user_data

            result = await user_store.get_user_by_username(sample_user.username)

            assert result is not None
            assert result.user_id == sample_user.user_id
            assert result.username == sample_user.username

    @pytest.mark.asyncio
    async def test_get_user_by_username_not_found(self, user_store):
        """Test getting non-existent user by username."""
        with patch('openhands.utils.async_utils.call_sync_from_async'):
            # Mock file store list to return no files
            user_store.file_store.list.return_value = []

            result = await user_store.get_user_by_username('nonexistent_user')
            assert result is None

    @pytest.mark.asyncio
    async def test_get_user_by_email(self, user_store, sample_user):
        """Test getting user by email."""
        user_data = sample_user.model_dump_json(context={'expose_secrets': True})

        with patch('openhands.utils.async_utils.call_sync_from_async') as mock_call:
            # Mock file store list to return one user file
            user_store.file_store.list.return_value = [
                f'users/{sample_user.user_id}.json'
            ]
            mock_call.return_value = user_data

            result = await user_store.get_user_by_email(sample_user.email)

            assert result is not None
            assert result.user_id == sample_user.user_id
            assert result.email == sample_user.email

    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, user_store):
        """Test getting non-existent user by email."""
        with patch('openhands.utils.async_utils.call_sync_from_async'):
            # Mock file store list to return no files
            user_store.file_store.list.return_value = []

            result = await user_store.get_user_by_email('nonexistent@example.com')
            assert result is None

    @pytest.mark.asyncio
    async def test_update_user(self, user_store, sample_user):
        """Test updating user."""
        # Update user data
        sample_user.last_login = datetime.now(timezone.utc)
        sample_user.email_verified = True

        with patch('openhands.utils.async_utils.call_sync_from_async') as mock_call:
            await user_store.update_user(sample_user)

            # Verify file store write was called
            mock_call.assert_called()
            args = mock_call.call_args[0]
            assert args[0] == user_store.file_store.write

    @pytest.mark.asyncio
    async def test_delete_user(self, user_store, sample_user):
        """Test deleting user."""
        with patch('openhands.utils.async_utils.call_sync_from_async') as mock_call:
            await user_store.delete_user(sample_user.user_id)

            # Verify file store delete was called
            mock_call.assert_called()
            args = mock_call.call_args[0]
            assert args[0] == user_store.file_store.delete

    @pytest.mark.asyncio
    async def test_list_users(self, user_store, sample_user):
        """Test listing users."""
        user_data = sample_user.model_dump_json(context={'expose_secrets': True})

        with patch('openhands.utils.async_utils.call_sync_from_async') as mock_call:
            # Mock file store list to return one user file
            user_store.file_store.list.return_value = [
                f'users/{sample_user.user_id}.json'
            ]
            mock_call.return_value = user_data

            users = await user_store.list_users()

            assert len(users) == 1
            assert users[0].user_id == sample_user.user_id

    @pytest.mark.asyncio
    async def test_get_instance(self):
        """Test UserStore.get_instance class method."""
        mock_config = MagicMock()
        mock_config.file_store = 'local'
        mock_config.file_store_path = '/tmp/test'
        mock_config.file_store_web_hook_url = None
        mock_config.file_store_web_hook_headers = None

        with patch(
            'openhands.storage.user.user_store.get_file_store'
        ) as mock_get_store:
            mock_file_store = MagicMock()
            mock_get_store.return_value = mock_file_store

            store = await UserStore.get_instance(mock_config)

            assert isinstance(store, UserStore)
            assert store.file_store == mock_file_store

            mock_get_store.assert_called_once_with(
                'local',
                '/tmp/test',
                None,
                None,
            )


class TestCreateUser:
    """Test create_user utility function."""

    @patch('openhands.storage.user.user_store.UserStore.get_instance')
    @patch('openhands.storage.user.user_store.get_password_hash')
    @pytest.mark.asyncio
    async def test_create_user(self, mock_hash, mock_get_instance):
        """Test user creation."""
        # Mock dependencies
        mock_user_store = AsyncMock()
        mock_get_instance.return_value = mock_user_store
        mock_hash.return_value = 'hashed_password'

        mock_config = MagicMock()
        username = 'testuser'
        email = 'test@example.com'
        password = 'test_password'

        await create_user(mock_config, username, email, password)

        # Verify user store save was called
        mock_user_store.save_user.assert_called_once()

        # Verify the user data passed to save_user
        saved_user = mock_user_store.save_user.call_args[0][0]
        assert saved_user.username == username
        assert saved_user.email == email
        assert saved_user.password_hash.get_secret_value() == 'hashed_password'
        assert saved_user.is_active is True
        assert saved_user.email_verified is False
        assert saved_user.user_id is not None

    @patch('openhands.storage.user.user_store.UserStore.get_instance')
    @patch('openhands.storage.user.user_store.get_password_hash')
    @pytest.mark.asyncio
    async def test_create_user_with_github_id(self, mock_hash, mock_get_instance):
        """Test user creation with GitHub ID."""
        # Mock dependencies
        mock_user_store = AsyncMock()
        mock_get_instance.return_value = mock_user_store
        mock_hash.return_value = 'hashed_password'

        mock_config = MagicMock()
        username = 'testuser'
        email = 'test@example.com'
        password = 'test_password'
        github_id = 'github_123'

        await create_user(mock_config, username, email, password, github_id=github_id)

        # Verify user store save was called
        mock_user_store.save_user.assert_called_once()

        # Verify the user data passed to save_user
        saved_user = mock_user_store.save_user.call_args[0][0]
        assert saved_user.username == username
        assert saved_user.email == email
        assert saved_user.github_id == github_id
