from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, SecretStr


class User(BaseModel):
    """
    User model for authentication and authorization.
    
    This model represents a user in the OpenHands system and is used for
    authentication, authorization, and user-specific data isolation.
    """
    
    user_id: str = Field(..., description="Unique identifier for the user")
    username: str = Field(..., description="Username for display and login")
    email: Optional[EmailStr] = Field(None, description="User's email address")
    password_hash: Optional[SecretStr] = Field(None, description="Hashed password for basic auth")
    github_id: Optional[str] = Field(None, description="GitHub user ID for OAuth")
    gitlab_id: Optional[str] = Field(None, description="GitLab user ID for OAuth")
    bitbucket_id: Optional[str] = Field(None, description="Bitbucket user ID for OAuth")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = Field(None)
    is_active: bool = Field(True, description="Whether the user account is active")
    email_verified: bool = Field(False, description="Whether the user's email has been verified")


class UserCreate(BaseModel):
    """
    Model for creating a new user with username/password authentication.
    """
    
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: SecretStr = Field(..., min_length=8)


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
    email: Optional[EmailStr] = None
    created_at: datetime
    last_login: Optional[datetime] = None
    email_verified: bool = False


class Token(BaseModel):
    """
    Model for authentication tokens.
    """
    
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime