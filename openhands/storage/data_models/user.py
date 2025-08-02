from __future__ import annotations

import re
from datetime import datetime, timezone

from pydantic import BaseModel, Field, SecretStr, field_serializer, field_validator


class User(BaseModel):
    """
    User model for authentication and authorization.

    This model represents a user in the OpenHands system and is used for
    authentication, authorization, and user-specific data isolation.
    """

    user_id: str = Field(..., description='Unique identifier for the user')
    username: str = Field(..., description='Username for display and login')
    email: str | None = Field(None, description="User's email address")
    password_hash: SecretStr | None = Field(
        None, description='Hashed password for basic auth'
    )
    github_id: str | None = Field(None, description='GitHub user ID for OAuth')
    gitlab_id: str | None = Field(None, description='GitLab user ID for OAuth')
    bitbucket_id: str | None = Field(None, description='Bitbucket user ID for OAuth')
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: datetime | None = Field(None)
    is_active: bool = Field(True, description='Whether the user account is active')
    email_verified: bool = Field(
        False, description="Whether the user's email has been verified"
    )

    @field_serializer('password_hash')
    def serialize_password_hash(self, value: SecretStr | None) -> str | None:
        """Serialize password hash to include the actual value."""
        if value is None:
            return None
        return value.get_secret_value()


class UserCreate(BaseModel):
    """
    Model for creating a new user with username/password authentication.
    """

    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: SecretStr = Field(..., min_length=8)

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v


class UserLogin(BaseModel):
    """
    Model for user login with username/password authentication.
    """

    username: str
    password: SecretStr


class UserResponse(BaseModel):
    """
    Model for user information returned to the client.
    """

    user_id: str
    username: str
    email: str | None = None
    created_at: datetime
    last_login: datetime | None = None
    email_verified: bool = False


class Token(BaseModel):
    """
    Model for authentication tokens.
    """

    access_token: str
    token_type: str = 'bearer'
    expires_at: datetime
