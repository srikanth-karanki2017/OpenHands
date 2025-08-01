from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from openhands.core.logger import openhands_logger as logger
from openhands.server.dependencies import get_dependencies
from openhands.server.shared import config
from openhands.server.user_auth.multi_user_auth import (
    JWT_EXPIRATION_MINUTES,
    create_access_token,
)
from openhands.storage.data_models.user import (
    Token,
    User,
    UserCreate,
    UserLogin,
    UserResponse,
)
from openhands.storage.user import FileUserStore, create_user

app = APIRouter(prefix="/api/auth", dependencies=get_dependencies())


@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    """
    Register a new user with username and password.
    """
    try:
        # Get user store
        user_store = await FileUserStore.get_instance(config)
        
        # Create user
        user = await create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password.get_secret_value(),
            user_store=user_store,
        )
        
        # Return user info (without password)
        return UserResponse(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            created_at=user.created_at,
            last_login=user.last_login,
            email_verified=user.email_verified,
        )
    except ValueError as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during registration",
        )


@app.post("/login", response_model=Token)
async def login_user(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """
    Authenticate a user and return an access token.
    """
    try:
        # Get user store
        user_store = await FileUserStore.get_instance(config)
        
        # Authenticate user
        user = await user_store.authenticate_user(
            username=form_data.username,
            password=form_data.password,
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        expires_delta = timedelta(minutes=JWT_EXPIRATION_MINUTES)
        access_token = create_access_token(
            data={"sub": user.user_id, "username": user.username, "email": user.email},
            expires_delta=expires_delta,
        )
        
        # Calculate expiration time
        expires_at = datetime.now(timezone.utc) + expires_delta
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_at=expires_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during login",
        )


@app.post("/token", response_model=Token)
async def login_for_access_token(user_data: UserLogin):
    """
    Authenticate a user and return an access token.
    """
    try:
        # Get user store
        user_store = await FileUserStore.get_instance(config)
        
        # Authenticate user
        user = await user_store.authenticate_user(
            username=user_data.username,
            password=user_data.password.get_secret_value(),
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        expires_delta = timedelta(minutes=JWT_EXPIRATION_MINUTES)
        access_token = create_access_token(
            data={"sub": user.user_id, "username": user.username, "email": user.email},
            expires_delta=expires_delta,
        )
        
        # Calculate expiration time
        expires_at = datetime.now(timezone.utc) + expires_delta
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_at=expires_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during token generation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during token generation",
        )


@app.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(FileUserStore.get_instance)]
):
    """
    Get information about the currently authenticated user.
    """
    return UserResponse(
        user_id=current_user.user_id,
        username=current_user.username,
        email=current_user.email,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
        email_verified=current_user.email_verified,
    )