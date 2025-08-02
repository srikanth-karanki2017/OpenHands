"""Integration tests for authentication API endpoints."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from openhands.server.app import app
from openhands.storage.data_models.user import User


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_user():
    """Sample user for testing."""
    return User(
        user_id='test_user_123',
        username='testuser',
        email='test@example.com',
        password_hash=SecretStr('$2b$12$hashed_password'),
        github_id=None,
        gitlab_id=None,
        bitbucket_id=None,
        created_at=datetime.now(timezone.utc),
        last_login=None,
        is_active=True,
        email_verified=False,
    )


class TestAuthEndpoints:
    """Test authentication API endpoints."""

    @patch('openhands.storage.user.user_store.UserStore.get_instance')
    def test_register_success(self, mock_get_instance, client):
        """Test successful user registration."""
        mock_user_store = AsyncMock()
        mock_get_instance.return_value = mock_user_store
        mock_user_store.get_user_by_username.return_value = None
        mock_user_store.get_user_by_email.return_value = None

        response = client.post(
            '/api/auth/register',
            json={
                'username': 'newuser',
                'email': 'new@example.com',
                'password': 'password123',
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data['message'] == 'User registered successfully'
        assert 'user_id' in data

    @patch('openhands.storage.user.user_store.UserStore.get_instance')
    def test_register_username_exists(self, mock_get_instance, client, sample_user):
        """Test registration with existing username."""
        mock_user_store = AsyncMock()
        mock_get_instance.return_value = mock_user_store
        mock_user_store.get_user_by_username.return_value = sample_user

        response = client.post(
            '/api/auth/register',
            json={
                'username': 'testuser',
                'email': 'new@example.com',
                'password': 'password123',
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert 'Username already exists' in data['detail']

    @patch('openhands.storage.user.user_store.UserStore.get_instance')
    def test_register_email_exists(self, mock_get_instance, client, sample_user):
        """Test registration with existing email."""
        mock_user_store = AsyncMock()
        mock_get_instance.return_value = mock_user_store
        mock_user_store.get_user_by_username.return_value = None
        mock_user_store.get_user_by_email.return_value = sample_user

        response = client.post(
            '/api/auth/register',
            json={
                'username': 'newuser',
                'email': 'test@example.com',
                'password': 'password123',
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert 'Email already exists' in data['detail']

    def test_register_invalid_data(self, client):
        """Test registration with invalid data."""
        response = client.post(
            '/api/auth/register',
            json={
                'username': '',  # Empty username
                'email': 'invalid-email',  # Invalid email
                'password': '123',  # Too short password
            },
        )

        assert response.status_code == 422

    @patch('openhands.storage.user.user_store.UserStore.get_instance')
    @patch('openhands.server.user_auth.multi_user_auth.verify_password')
    def test_login_success(self, mock_verify, mock_get_instance, client, sample_user):
        """Test successful login."""
        mock_user_store = AsyncMock()
        mock_get_instance.return_value = mock_user_store
        mock_user_store.get_user_by_username.return_value = sample_user
        mock_verify.return_value = True

        response = client.post(
            '/api/auth/token', data={'username': 'testuser', 'password': 'password123'}
        )

        assert response.status_code == 200
        data = response.json()
        assert 'access_token' in data
        assert data['token_type'] == 'bearer'

    @patch('openhands.storage.user.user_store.UserStore.get_instance')
    def test_login_user_not_found(self, mock_get_instance, client):
        """Test login with non-existent user."""
        mock_user_store = AsyncMock()
        mock_get_instance.return_value = mock_user_store
        mock_user_store.get_user_by_username.return_value = None

        response = client.post(
            '/api/auth/token',
            data={'username': 'nonexistent', 'password': 'password123'},
        )

        assert response.status_code == 401
        data = response.json()
        assert 'Invalid credentials' in data['detail']

    @patch('openhands.storage.user.user_store.UserStore.get_instance')
    @patch('openhands.server.user_auth.multi_user_auth.verify_password')
    def test_login_wrong_password(
        self, mock_verify, mock_get_instance, client, sample_user
    ):
        """Test login with wrong password."""
        mock_user_store = AsyncMock()
        mock_get_instance.return_value = mock_user_store
        mock_user_store.get_user_by_username.return_value = sample_user
        mock_verify.return_value = False

        response = client.post(
            '/api/auth/token',
            data={'username': 'testuser', 'password': 'wrongpassword'},
        )

        assert response.status_code == 401
        data = response.json()
        assert 'Invalid credentials' in data['detail']

    @patch('openhands.storage.user.user_store.UserStore.get_instance')
    @patch('openhands.server.user_auth.multi_user_auth.verify_password')
    def test_login_inactive_user(
        self, mock_verify, mock_get_instance, client, sample_user
    ):
        """Test login with inactive user."""
        sample_user.is_active = False

        mock_user_store = AsyncMock()
        mock_get_instance.return_value = mock_user_store
        mock_user_store.get_user_by_username.return_value = sample_user
        mock_verify.return_value = True

        response = client.post(
            '/api/auth/token', data={'username': 'testuser', 'password': 'password123'}
        )

        assert response.status_code == 401
        data = response.json()
        assert 'User account is inactive' in data['detail']

    @patch('openhands.server.user_auth.multi_user_auth.get_current_user_from_token')
    def test_get_current_user_success(self, mock_get_user, client, sample_user):
        """Test getting current user info."""
        mock_get_user.return_value = sample_user

        response = client.get(
            '/api/auth/me', headers={'Authorization': 'Bearer test_token'}
        )

        assert response.status_code == 200
        data = response.json()
        assert data['user_id'] == sample_user.user_id
        assert data['username'] == sample_user.username
        assert data['email'] == sample_user.email

    def test_get_current_user_no_token(self, client):
        """Test getting current user without token."""
        response = client.get('/api/auth/me')

        assert response.status_code == 401

    @patch('openhands.server.user_auth.multi_user_auth.get_current_user_from_token')
    def test_get_current_user_invalid_token(self, mock_get_user, client):
        """Test getting current user with invalid token."""
        from fastapi import HTTPException

        mock_get_user.side_effect = HTTPException(
            status_code=401, detail='Invalid token'
        )

        response = client.get(
            '/api/auth/me', headers={'Authorization': 'Bearer invalid_token'}
        )

        assert response.status_code == 401
