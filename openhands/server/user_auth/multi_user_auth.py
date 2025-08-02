from __future__ import annotations

import hashlib
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import SecretStr

from openhands.core.logger import openhands_logger as logger
from openhands.integrations.provider import PROVIDER_TOKEN_TYPE
from openhands.server import shared
from openhands.server.settings import Settings
from openhands.server.user_auth.user_auth import AuthType, UserAuth
from openhands.storage.data_models.user import User
from openhands.storage.data_models.user_secrets import UserSecrets
from openhands.storage.secrets.secrets_store import SecretsStore
from openhands.storage.settings.settings_store import SettingsStore

# JWT settings
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', secrets.token_hex(32))
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_MINUTES = 60 * 24  # 24 hours

# Security bearer scheme for token authentication
security = HTTPBearer()


def get_password_hash(password: str) -> str:
    """Generate a secure hash for a password."""
    salt = os.environ.get('PASSWORD_SALT', 'openhands-salt')
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return get_password_hash(plain_password) == hashed_password


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRATION_MINUTES)

    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError as e:
        logger.error(f'JWT token validation error: {str(e)}')
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate credentials',
            headers={'WWW-Authenticate': 'Bearer'},
        )


async def get_current_user_from_token(token: str) -> User:
    """Get the current user from a JWT token."""
    payload = decode_token(token)
    user_id = payload.get('sub')

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid authentication credentials',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    # Get user from database
    from openhands.storage.user import FileUserStore

    user_store = await FileUserStore.get_instance(shared.config)

    try:
        user = await user_store.get_user(user_id)
        return user
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='User not found',
            headers={'WWW-Authenticate': 'Bearer'},
        )


@dataclass
class MultiUserAuth(UserAuth):
    """Multi-user authentication implementation."""

    request: Request
    _user: User | None = None
    _settings: Settings | None = None
    _settings_store: SettingsStore | None = None
    _secrets_store: SecretsStore | None = None
    _user_secrets: UserSecrets | None = None

    async def get_user_id(self) -> str | None:
        """Get the unique identifier for the current user."""
        user = await self._get_user()
        return user.user_id if user else None

    async def get_user_email(self) -> str | None:
        """Get the email for the current user."""
        user = await self._get_user()
        return user.email if user else None

    async def get_access_token(self) -> SecretStr | None:
        """Get the access token for the current user."""
        auth_header = self.request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        token = auth_header.replace('Bearer ', '')
        return SecretStr(token)

    async def get_provider_tokens(self) -> PROVIDER_TOKEN_TYPE | None:
        """Get the provider tokens for the current user."""
        user_secrets = await self.get_user_secrets()
        if user_secrets is None:
            return None
        return user_secrets.provider_tokens

    async def get_user_settings_store(self) -> SettingsStore:
        """Get the settings store for the current user."""
        settings_store = self._settings_store
        if settings_store:
            return settings_store

        user_id = await self.get_user_id()
        settings_store = await shared.SettingsStoreImpl.get_instance(
            shared.config, user_id
        )
        if settings_store is None:
            raise ValueError('Failed to get settings store instance')

        self._settings_store = settings_store
        return settings_store

    async def get_user_settings(self) -> Settings | None:
        """Get the user settings for the current user."""
        settings = self._settings
        if settings:
            return settings

        settings_store = await self.get_user_settings_store()
        settings = await settings_store.load()

        # Merge config.toml settings with stored settings
        if settings:
            settings = settings.merge_with_config_settings()

            # Ensure user_id is set
            user_id = await self.get_user_id()
            if user_id and not settings.user_id:
                settings.user_id = user_id
                await settings_store.store(settings)

        self._settings = settings
        return settings

    async def get_secrets_store(self) -> SecretsStore:
        """Get secrets store."""
        secrets_store = self._secrets_store
        if secrets_store:
            return secrets_store

        user_id = await self.get_user_id()
        secret_store = await shared.SecretsStoreImpl.get_instance(
            shared.config, user_id
        )
        if secret_store is None:
            raise ValueError('Failed to get secrets store instance')

        self._secrets_store = secret_store
        return secret_store

    async def get_user_secrets(self) -> UserSecrets | None:
        """Get the user's secrets."""
        user_secrets = self._user_secrets
        if user_secrets:
            return user_secrets

        secrets_store = await self.get_secrets_store()
        user_secrets = await secrets_store.load()

        # Ensure user_id is set
        if user_secrets and not user_secrets.user_id:
            user_id = await self.get_user_id()
            if user_id:
                # Create a new UserSecrets with user_id
                updated_secrets = UserSecrets(
                    provider_tokens=user_secrets.provider_tokens,
                    custom_secrets=user_secrets.custom_secrets,
                    user_id=user_id,
                )
                await secrets_store.store(updated_secrets)
                user_secrets = updated_secrets

        self._user_secrets = user_secrets
        return user_secrets

    def get_auth_type(self) -> AuthType | None:
        """Get the authentication type."""
        return AuthType.BEARER

    async def _get_user(self) -> User | None:
        """Get the current user from the request."""
        if self._user:
            return self._user

        # Try to get token from Authorization header
        auth_header = self.request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.replace('Bearer ', '')
            try:
                user = await get_current_user_from_token(token)
                self._user = user
                return user
            except HTTPException:
                return None

        return None

    @classmethod
    async def get_instance(cls, request: Request) -> UserAuth:
        """Get an instance of UserAuth from the request given."""
        return cls(request=request)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """Dependency to get the current authenticated user."""
    token = credentials.credentials
    return await get_current_user_from_token(token)
