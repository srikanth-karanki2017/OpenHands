#!/usr/bin/env python3
"""
Migration script to upgrade from single-user to multi-user mode.

This script:
1. Creates a default admin user
2. Migrates existing conversations, settings, and secrets to the admin user
3. Updates all necessary files with user_id references

Usage:
    python migrate_to_multi_user.py [--admin-username USERNAME] [--admin-email EMAIL] [--admin-password PASSWORD]
"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from openhands.core.config.utils import load_openhands_config
from openhands.core.logger import openhands_logger as logger
from openhands.server.user_auth.multi_user_auth import get_password_hash
from openhands.storage import get_file_store
from openhands.storage.conversation.file_conversation_store import FileConversationStore
from openhands.storage.data_models.conversation_metadata import ConversationMetadata
from openhands.storage.data_models.settings import Settings
from openhands.storage.data_models.user import User
from openhands.storage.data_models.user_secrets import UserSecrets
from openhands.storage.files import FileStore
from openhands.storage.locations import (
    CONVERSATION_BASE_DIR,
    get_conversation_metadata_filename,
)
from openhands.storage.secrets.file_secrets_store import FileSecretsStore
from openhands.storage.settings.file_settings_store import FileSettingsStore
from openhands.storage.user.user_store import FileUserStore
from openhands.utils.async_utils import run_async


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Migrate from single-user to multi-user mode"
    )
    parser.add_argument(
        "--admin-username",
        type=str,
        default="admin",
        help="Username for the admin user (default: admin)",
    )
    parser.add_argument(
        "--admin-email",
        type=str,
        default="admin@example.com",
        help="Email for the admin user (default: admin@example.com)",
    )
    parser.add_argument(
        "--admin-password",
        type=str,
        default="openhands",
        help="Password for the admin user (default: openhands)",
    )
    return parser.parse_args()


async def create_admin_user(
    file_store: FileStore, username: str, email: str, password: str
) -> User:
    """Create an admin user."""
    logger.info(f"Creating admin user: {username}")
    
    # Create user store
    user_store = FileUserStore(file_store)
    
    # Check if user already exists
    try:
        user = await user_store.get_user_by_username(username)
        logger.info(f"Admin user already exists: {user.user_id}")
        return user
    except FileNotFoundError:
        pass
    
    # Create new user
    user_id = str(uuid.uuid4())
    password_hash = get_password_hash(password)
    
    user = User(
        user_id=user_id,
        username=username,
        email=email,
        password_hash=password_hash,
        created_at=datetime.now(timezone.utc),
        is_active=True,
        email_verified=True,
    )
    
    # Save user
    await user_store.save_user(user)
    logger.info(f"Created admin user with ID: {user.user_id}")
    
    return user


async def migrate_conversations(file_store: FileStore, user_id: str) -> int:
    """Migrate existing conversations to the admin user."""
    logger.info("Migrating conversations...")
    
    # Create conversation store
    conversation_store = FileConversationStore(file_store)
    
    # Get all conversation files
    try:
        conversation_files = file_store.list(CONVERSATION_BASE_DIR)
    except FileNotFoundError:
        logger.info("No conversations found")
        return 0
    
    # Filter for metadata files
    metadata_files = [
        f for f in conversation_files
        if f.endswith("metadata.json") and "/." not in f
    ]
    
    count = 0
    for file_path in metadata_files:
        try:
            # Read metadata
            json_str = file_store.read(file_path)
            metadata_dict = json.loads(json_str)
            
            # Skip if already has user_id
            if metadata_dict.get("user_id"):
                continue
            
            # Add user_id
            metadata_dict["user_id"] = user_id
            
            # Save updated metadata
            updated_json = json.dumps(metadata_dict)
            file_store.write(file_path, updated_json)
            
            count += 1
        except Exception as e:
            logger.error(f"Error migrating conversation {file_path}: {str(e)}")
    
    logger.info(f"Migrated {count} conversations")
    return count


async def migrate_settings(file_store: FileStore, user_id: str) -> bool:
    """Migrate existing settings to the admin user."""
    logger.info("Migrating settings...")
    
    # Create settings store
    settings_store = FileSettingsStore(file_store)
    
    try:
        # Load existing settings
        settings = await settings_store.load()
        
        if not settings:
            logger.info("No settings found")
            return False
        
        # Add user_id if not present
        if not settings.user_id:
            settings.user_id = user_id
            
            # Save updated settings
            await settings_store.save(settings)
            logger.info("Migrated settings")
            return True
        else:
            logger.info("Settings already have user_id")
            return False
    except Exception as e:
        logger.error(f"Error migrating settings: {str(e)}")
        return False


async def migrate_secrets(file_store: FileStore, user_id: str) -> bool:
    """Migrate existing secrets to the admin user."""
    logger.info("Migrating secrets...")
    
    # Create secrets store
    secrets_store = FileSecretsStore(file_store)
    
    try:
        # Load existing secrets
        secrets = await secrets_store.load()
        
        if not secrets:
            logger.info("No secrets found")
            return False
        
        # Add user_id if not present
        if not secrets.user_id:
            # Create new UserSecrets with user_id
            updated_secrets = UserSecrets(
                provider_tokens=secrets.provider_tokens,
                custom_secrets=secrets.custom_secrets,
                user_id=user_id,
            )
            
            # Save updated secrets
            await secrets_store.save(updated_secrets)
            logger.info("Migrated secrets")
            return True
        else:
            logger.info("Secrets already have user_id")
            return False
    except Exception as e:
        logger.error(f"Error migrating secrets: {str(e)}")
        return False


async def main():
    """Main migration function."""
    args = parse_args()
    
    logger.info("Starting migration to multi-user mode")
    
    # Load config
    config = load_openhands_config()
    
    # Get file store
    file_store = get_file_store(config)
    
    # Create admin user
    admin_user = await create_admin_user(
        file_store,
        username=args.admin_username,
        email=args.admin_email,
        password=args.admin_password,
    )
    
    # Migrate data
    conversations_count = await migrate_conversations(file_store, admin_user.user_id)
    settings_migrated = await migrate_settings(file_store, admin_user.user_id)
    secrets_migrated = await migrate_secrets(file_store, admin_user.user_id)
    
    logger.info("Migration complete")
    logger.info(f"Admin user created: {admin_user.username} (ID: {admin_user.user_id})")
    logger.info(f"Conversations migrated: {conversations_count}")
    logger.info(f"Settings migrated: {settings_migrated}")
    logger.info(f"Secrets migrated: {secrets_migrated}")
    
    logger.info("\nYou can now login with:")
    logger.info(f"  Username: {admin_user.username}")
    logger.info(f"  Password: {args.admin_password}")


if __name__ == "__main__":
    run_async(main())