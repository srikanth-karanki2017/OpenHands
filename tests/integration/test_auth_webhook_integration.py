"""Integration tests for authentication and webhook management."""

import pytest
from fastapi.testclient import TestClient

from openhands.server.app import app


class TestAuthWebhookIntegration:
    """Integration tests for the complete auth and webhook flow."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    def test_complete_auth_webhook_flow(self, client):
        """Test the complete flow: register -> login -> create webhook -> list webhooks."""
        
        # Step 1: Register a new user
        register_response = client.post('/api/auth/register', json={
            'username': 'integrationuser',
            'email': 'integration@example.com',
            'password': 'securepassword123'
        })
        
        assert register_response.status_code == 201
        register_data = register_response.json()
        assert register_data['username'] == 'integrationuser'
        assert register_data['email'] == 'integration@example.com'
        assert 'user_id' in register_data
        assert 'password_hash' not in register_data  # Should not be exposed
        
        # Step 2: Login with the registered user
        login_response = client.post('/api/auth/token', json={
            'username': 'integrationuser',
            'password': 'securepassword123'
        })
        
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert 'access_token' in login_data
        assert login_data['token_type'] == 'bearer'
        assert 'expires_at' in login_data
        
        token = login_data['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Step 3: Get current user info
        me_response = client.get('/api/auth/me', headers=headers)
        assert me_response.status_code == 200
        me_data = me_response.json()
        assert me_data['username'] == 'integrationuser'
        assert me_data['email'] == 'integration@example.com'
        assert me_data['user_id'] == register_data['user_id']
        
        # Step 4: Create a webhook
        webhook_response = client.post('/api/webhooks/configs', json={
            'name': 'Integration Test Webhook',
            'url': 'https://example.com/webhook-endpoint',
            'events': ['push', 'pull_request', 'issue'],
            'repository': 'testuser/testrepo',
            'secret': 'webhook_secret_integration_test'
        }, headers=headers)
        
        assert webhook_response.status_code == 201
        webhook_data = webhook_response.json()
        assert webhook_data['name'] == 'Integration Test Webhook'
        assert webhook_data['url'] == 'https://example.com/webhook-endpoint'
        assert webhook_data['events'] == ['push', 'pull_request', 'issue']
        assert webhook_data['repository'] == 'testuser/testrepo'
        assert webhook_data['status'] == 'active'
        assert 'webhook_id' in webhook_data
        assert 'created_at' in webhook_data
        assert 'updated_at' in webhook_data
        
        webhook_id = webhook_data['webhook_id']
        
        # Step 5: List webhooks
        list_response = client.get('/api/webhooks/configs', headers=headers)
        assert list_response.status_code == 200
        webhooks = list_response.json()
        assert len(webhooks) == 1
        assert webhooks[0]['webhook_id'] == webhook_id
        assert webhooks[0]['name'] == 'Integration Test Webhook'
        
        # Step 6: Update webhook
        update_response = client.patch(f'/api/webhooks/configs/{webhook_id}', json={
            'name': 'Updated Integration Test Webhook',
            'url': 'https://example.com/updated-webhook-endpoint',
            'events': ['push', 'pull_request'],
            'repository': 'testuser/testrepo',
            'secret': 'updated_webhook_secret'
        }, headers=headers)
        
        assert update_response.status_code == 200
        updated_webhook = update_response.json()
        assert updated_webhook['name'] == 'Updated Integration Test Webhook'
        assert updated_webhook['url'] == 'https://example.com/updated-webhook-endpoint'
        assert updated_webhook['events'] == ['push', 'pull_request']
        
        # Step 7: Get specific webhook
        get_response = client.get(f'/api/webhooks/configs/{webhook_id}', headers=headers)
        assert get_response.status_code == 200
        get_webhook = get_response.json()
        assert get_webhook['webhook_id'] == webhook_id
        assert get_webhook['name'] == 'Updated Integration Test Webhook'
        
        # Step 8: Delete webhook
        delete_response = client.delete(f'/api/webhooks/configs/{webhook_id}', headers=headers)
        assert delete_response.status_code == 204
        
        # Step 9: Verify webhook is deleted
        list_after_delete = client.get('/api/webhooks/configs', headers=headers)
        assert list_after_delete.status_code == 200
        assert len(list_after_delete.json()) == 0

    def test_authentication_failures(self, client):
        """Test authentication failure scenarios."""
        
        # Test login with non-existent user
        login_response = client.post('/api/auth/token', json={
            'username': 'nonexistent',
            'password': 'password123'
        })
        assert login_response.status_code == 401
        assert 'Invalid username or password' in login_response.json()['detail']
        
        # Test accessing protected endpoint without token
        webhook_response = client.get('/api/webhooks/configs')
        assert webhook_response.status_code == 403
        
        # Test accessing protected endpoint with invalid token
        invalid_headers = {'Authorization': 'Bearer invalid_token'}
        webhook_response = client.get('/api/webhooks/configs', headers=invalid_headers)
        assert webhook_response.status_code == 401

    def test_user_registration_validation(self, client):
        """Test user registration validation."""
        
        # Test registration with invalid email
        response = client.post('/api/auth/register', json={
            'username': 'testuser',
            'email': 'invalid-email',
            'password': 'password123'
        })
        assert response.status_code == 422
        
        # Test registration with short password
        response = client.post('/api/auth/register', json={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': '123'
        })
        assert response.status_code == 422
        
        # Test registration with missing fields
        response = client.post('/api/auth/register', json={
            'username': 'testuser'
        })
        assert response.status_code == 422

    def test_webhook_validation(self, client):
        """Test webhook creation validation."""
        
        # First register and login
        client.post('/api/auth/register', json={
            'username': 'webhookuser',
            'email': 'webhook@example.com',
            'password': 'password123'
        })
        
        login_response = client.post('/api/auth/token', json={
            'username': 'webhookuser',
            'password': 'password123'
        })
        token = login_response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Test webhook creation with invalid URL
        response = client.post('/api/webhooks/configs', json={
            'name': 'Test Webhook',
            'url': 'not-a-valid-url',
            'events': ['push'],
            'repository': 'test/repo',
            'secret': 'secret'
        }, headers=headers)
        assert response.status_code == 422
        
        # Test webhook creation with empty events (empty list is allowed)
        response = client.post('/api/webhooks/configs', json={
            'name': 'Test Webhook',
            'url': 'https://example.com/webhook',
            'events': [],
            'repository': 'test/repo',
            'secret': 'secret'
        }, headers=headers)
        assert response.status_code == 201
        webhook_data = response.json()
        assert webhook_data['events'] == []

    def test_user_isolation(self, client):
        """Test that users can only see their own webhooks."""
        
        # Register first user
        client.post('/api/auth/register', json={
            'username': 'user1',
            'email': 'user1@example.com',
            'password': 'password123'
        })
        
        login1_response = client.post('/api/auth/token', json={
            'username': 'user1',
            'password': 'password123'
        })
        token1 = login1_response.json()['access_token']
        headers1 = {'Authorization': f'Bearer {token1}'}
        
        # Register second user
        client.post('/api/auth/register', json={
            'username': 'user2',
            'email': 'user2@example.com',
            'password': 'password123'
        })
        
        login2_response = client.post('/api/auth/token', json={
            'username': 'user2',
            'password': 'password123'
        })
        token2 = login2_response.json()['access_token']
        headers2 = {'Authorization': f'Bearer {token2}'}
        
        # User 1 creates a webhook
        webhook1_response = client.post('/api/webhooks/configs', json={
            'name': 'User 1 Webhook',
            'url': 'https://example.com/user1-webhook',
            'events': ['push'],
            'repository': 'user1/repo',
            'secret': 'user1_secret'
        }, headers=headers1)
        assert webhook1_response.status_code == 201
        
        # User 2 creates a webhook
        webhook2_response = client.post('/api/webhooks/configs', json={
            'name': 'User 2 Webhook',
            'url': 'https://example.com/user2-webhook',
            'events': ['push'],
            'repository': 'user2/repo',
            'secret': 'user2_secret'
        }, headers=headers2)
        assert webhook2_response.status_code == 201
        
        # User 1 should only see their webhook
        user1_webhooks = client.get('/api/webhooks/configs', headers=headers1)
        assert user1_webhooks.status_code == 200
        webhooks1 = user1_webhooks.json()
        assert len(webhooks1) == 1
        assert webhooks1[0]['name'] == 'User 1 Webhook'
        
        # User 2 should only see their webhook
        user2_webhooks = client.get('/api/webhooks/configs', headers=headers2)
        assert user2_webhooks.status_code == 200
        webhooks2 = user2_webhooks.json()
        assert len(webhooks2) == 1
        assert webhooks2[0]['name'] == 'User 2 Webhook'
        
        # User 1 should not be able to access User 2's webhook
        user2_webhook_id = webhooks2[0]['webhook_id']
        access_response = client.get(f'/api/webhooks/configs/{user2_webhook_id}', headers=headers1)
        assert access_response.status_code == 404