# Multi-User Support in OpenHands

This document describes the multi-user support feature in OpenHands, which allows multiple users to use the same OpenHands instance with their own isolated data and configurations.

## Overview

OpenHands now supports multiple users with:
- User authentication (username/password)
- User-specific data isolation
- User-specific GitHub tokens
- User-specific webhook configurations

## Enabling Multi-User Mode

Multi-user mode can be enabled by setting the `ENABLE_MULTI_USER` environment variable to `true` when starting the OpenHands container:

```bash
docker run -p 3000:3000 -e ENABLE_MULTI_USER=true openhands/openhands-ai:latest
```

When multi-user mode is enabled, the container will automatically run a migration script to create a default admin user and migrate existing data.

### Default Admin Credentials

The default admin credentials are:
- Username: `admin`
- Password: `openhands`

You can customize these by setting the following environment variables:
- `ADMIN_USERNAME`: Custom admin username
- `ADMIN_EMAIL`: Custom admin email
- `ADMIN_PASSWORD`: Custom admin password

Example:
```bash
docker run -p 3000:3000 \
  -e ENABLE_MULTI_USER=true \
  -e ADMIN_USERNAME=myadmin \
  -e ADMIN_EMAIL=admin@mycompany.com \
  -e ADMIN_PASSWORD=mysecretpassword \
  openhands/openhands-ai:latest
```

## User Management

### Registration

New users can register by visiting the `/register` page and providing:
- Username
- Email
- Password

### Login

Users can log in by visiting the `/login` page and providing:
- Username
- Password

### User Profile

After logging in, users can access their profile by clicking on their username in the sidebar or visiting the `/profile` page. The profile page shows:
- Username
- Email
- Account creation date
- Last login date
- Links to settings pages

## Data Isolation

In multi-user mode, each user has their own isolated data:

- **Conversations**: Each user can only see and access their own conversations
- **Settings**: Each user has their own settings configuration
- **GitHub Tokens**: Each user can configure their own GitHub tokens
- **Webhooks**: Each user can configure their own webhook endpoints

## Webhook Management

Each user can manage their own webhook configurations through the webhook management UI:

1. **Webhook List**: View, add, edit, and delete webhook configurations
2. **Webhook Logs**: View webhook delivery logs and details

### Adding a Webhook

To add a new webhook:
1. Navigate to Settings > Webhooks
2. Click "Add Webhook"
3. Fill in the webhook details:
   - Name: A descriptive name for the webhook
   - URL: The endpoint that will receive webhook events
   - Events: The events to trigger the webhook (PR, push, etc.)
   - Repository: Optional repository filter
   - Secret: Optional secret for webhook validation
   - Status: Active or Inactive

### Webhook Security

Webhooks can be secured with a secret token. When configured, OpenHands will sign webhook payloads with this secret, allowing the receiving endpoint to verify the authenticity of the webhook.

## API Authentication

All API endpoints in multi-user mode require authentication using JWT tokens. The token is obtained during login and should be included in the `Authorization` header of all API requests:

```
Authorization: Bearer <token>
```

## Migration from Single-User Mode

When upgrading from single-user to multi-user mode, the migration script will:
1. Create a default admin user
2. Migrate existing conversations to the admin user
3. Migrate existing settings to the admin user
4. Migrate existing secrets (GitHub tokens, etc.) to the admin user

The migration script can also be run manually:

```bash
python scripts/migrate_to_multi_user.py --admin-username admin --admin-email admin@example.com --admin-password openhands
```

## Security Considerations

- All user passwords are securely hashed using PBKDF2-SHA256
- JWT tokens are used for authentication with a 24-hour expiration
- All API endpoints validate user permissions to prevent unauthorized access
- Webhook secrets are stored securely and never exposed in API responses