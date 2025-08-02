from __future__ import annotations

import json
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone

from pydantic import SecretStr, TypeAdapter

from openhands.core.config.openhands_config import OpenHandsConfig
from openhands.core.logger import openhands_logger as logger
from openhands.server.user_auth.multi_user_auth import get_password_hash, verify_password
from openhands.storage import get_file_store
from openhands.storage.data_models.user import User
from openhands.storage.files import FileStore
from openhands.utils.async_utils import call_sync_from_async

# Base directory for user data
USER_BASE_DIR = 'users'

# Type adapter for serialization/deserialization
user_type_adapter = TypeAdapter(User)


class UserStore(ABC):
    """Abstract base class for user storage.

    This class defines the interface for storing and retrieving user information.
    """

    @abstractmethod
    async def save_user(self, user: User) -> None:
        """Store user information."""
        pass

    @abstractmethod
    async def get_user(self, user_id: str) -> User:
        """Load user information by user_id."""
        pass

    @abstractmethod
    async def get_user_by_username(self, username: str) -> User:
        """Load user information by username."""
        pass

    @abstractmethod
    async def get_user_by_email(self, email: str) -> User:
        """Load user information by email."""
        pass

    @abstractmethod
    async def delete_user(self, user_id: str) -> None:
        """Delete user information."""
        pass

    @abstractmethod
    async def list_users(self, limit: int = 100, offset: int = 0) -> list[User]:
        """List all users."""
        pass

    @abstractmethod
    async def authenticate_user(self, username: str, password: str) -> User | None:
        """Authenticate a user with username and password."""
        pass

    @classmethod
    @abstractmethod
    async def get_instance(cls, config: OpenHandsConfig) -> UserStore:
        """Get a user store instance."""
        pass


class FileUserStore(UserStore):
    """File-based implementation of UserStore.

    This class stores user information as JSON files in the filesystem.
    """

    def __init__(self, file_store: FileStore):
        self.file_store = file_store

    def _get_user_path(self, user_id: str) -> str:
        """Get the file path for a user."""
        return f'{USER_BASE_DIR}/{user_id}.json'

    def _get_username_index_path(self) -> str:
        """Get the file path for the username index."""
        return f'{USER_BASE_DIR}/username_index.json'

    def _get_email_index_path(self) -> str:
        """Get the file path for the email index."""
        return f'{USER_BASE_DIR}/email_index.json'

    async def _load_username_index(self) -> dict[str, str]:
        """Load the username to user_id index."""
        try:
            path = self._get_username_index_path()
            json_str = await call_sync_from_async(self.file_store.read, path)
            return json.loads(json_str)
        except Exception:
            return {}

    async def _save_username_index(self, index: dict[str, str]) -> None:
        """Save the username to user_id index."""
        path = self._get_username_index_path()
        json_str = json.dumps(index)
        await call_sync_from_async(self.file_store.write, path, json_str)

    async def _load_email_index(self) -> dict[str, str]:
        """Load the email to user_id index."""
        try:
            path = self._get_email_index_path()
            json_str = await call_sync_from_async(self.file_store.read, path)
            return json.loads(json_str)
        except Exception:
            return {}

    async def _save_email_index(self, index: dict[str, str]) -> None:
        """Save the email to user_id index."""
        path = self._get_email_index_path()
        json_str = json.dumps(index)
        await call_sync_from_async(self.file_store.write, path, json_str)

    async def save_user(self, user: User) -> None:
        """Store user information."""
        # Update indexes
        if user.username:
            username_index = await self._load_username_index()
            username_index[user.username.lower()] = user.user_id
            await self._save_username_index(username_index)

        if user.email:
            email_index = await self._load_email_index()
            email_index[user.email.lower()] = user.user_id
            await self._save_email_index(email_index)

        # Serialize and save
        json_str = user_type_adapter.dump_json(user)
        path = self._get_user_path(user.user_id)
        await call_sync_from_async(self.file_store.write, path, json_str)

    async def get_user(self, user_id: str) -> User:
        """Load user information by user_id."""
        path = self._get_user_path(user_id)
        try:
            json_str = await call_sync_from_async(self.file_store.read, path)
            return user_type_adapter.validate_json(json_str)
        except Exception as e:
            logger.error(f'Error loading user: {str(e)}')
            raise FileNotFoundError(f'User not found: {user_id}')

    async def get_user_by_username(self, username: str) -> User:
        """Load user information by username."""
        username_index = await self._load_username_index()
        user_id = username_index.get(username.lower())

        if not user_id:
            raise FileNotFoundError(f'User not found with username: {username}')

        return await self.get_user(user_id)

    async def get_user_by_email(self, email: str) -> User:
        """Load user information by email."""
        email_index = await self._load_email_index()
        user_id = email_index.get(email.lower())

        if not user_id:
            raise FileNotFoundError(f'User not found with email: {email}')

        return await self.get_user(user_id)

    async def delete_user(self, user_id: str) -> None:
        """Delete user information."""
        try:
            # Get the user first to update indexes
            user = await self.get_user(user_id)

            # Update username index
            if user.username:
                username_index = await self._load_username_index()
                if user.username.lower() in username_index:
                    del username_index[user.username.lower()]
                    await self._save_username_index(username_index)

            # Update email index
            if user.email:
                email_index = await self._load_email_index()
                if user.email.lower() in email_index:
                    del email_index[user.email.lower()]
                    await self._save_email_index(email_index)

            # Delete the user file
            path = self._get_user_path(user_id)
            await call_sync_from_async(self.file_store.delete, path)
        except FileNotFoundError:
            # If user doesn't exist, nothing to delete
            pass

    async def list_users(self, limit: int = 100, offset: int = 0) -> list[User]:
        """List all users."""
        try:
            # Get all files in the users directory
            files = await call_sync_from_async(self.file_store.list, USER_BASE_DIR)

            # Filter out index files and non-JSON files
            user_files = [
                f
                for f in files
                if f.endswith('.json') and not f.endswith('_index.json')
            ]

            # Apply pagination
            paginated_files = user_files[offset : offset + limit]

            # Load each user
            users = []
            for file_path in paginated_files:
                try:
                    json_str = await call_sync_from_async(
                        self.file_store.read, file_path
                    )
                    user = user_type_adapter.validate_json(json_str)
                    users.append(user)
                except Exception as e:
                    logger.error(f'Error loading user from {file_path}: {str(e)}')
                    continue

            return users
        except FileNotFoundError:
            # If directory doesn't exist, return empty list
            return []

    async def authenticate_user(self, username: str, password: str) -> User | None:
        """Authenticate a user with username and password."""
        try:
            user = await self.get_user_by_username(username)

            # Check if password_hash exists and matches
            if (
                user.password_hash
                and verify_password(password, user.password_hash.get_secret_value())
            ):
                # Update last_login
                user.last_login = datetime.now(timezone.utc)
                await self.save_user(user)
                return user

            return None
        except FileNotFoundError:
            return None

    @classmethod
    async def get_instance(cls, config: OpenHandsConfig) -> UserStore:
        """Get a user store instance."""
        file_store = get_file_store(
            config.file_store,
            config.file_store_path,
            config.file_store_web_hook_url,
            config.file_store_web_hook_headers,
        )
        return cls(file_store)


async def create_user(
    username: str,
    email: str,
    password: str,
    user_store: UserStore,
) -> User:
    """Create a new user."""
    # Check if username or email already exists
    try:
        await user_store.get_user_by_username(username)
        raise ValueError(f'Username already exists: {username}')
    except FileNotFoundError:
        pass

    try:
        await user_store.get_user_by_email(email)
        raise ValueError(f'Email already exists: {email}')
    except FileNotFoundError:
        pass

    # Create new user
    user_id = str(uuid.uuid4())
    password_hash = get_password_hash(password)

    user = User(
        user_id=user_id,
        username=username,
        email=email,
        password_hash=SecretStr(password_hash),
        github_id=None,
        gitlab_id=None,
        bitbucket_id=None,
        created_at=datetime.now(timezone.utc),
        last_login=None,
        is_active=True,
        email_verified=False,
    )

    # Save user
    await user_store.save_user(user)

    return user
