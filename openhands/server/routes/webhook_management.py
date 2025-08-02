from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from openhands.core.logger import openhands_logger as logger
from openhands.server.dependencies import get_dependencies
from openhands.server.shared import config
from openhands.server.user_auth.multi_user_auth import get_current_user
from openhands.storage.data_models.user import User
from openhands.storage.data_models.webhook_config import (
    WebhookConfigCreate,
    WebhookConfigResponse,
    WebhookConfigUpdate,
    WebhookLogResponse,
)
from openhands.storage.webhook import (
    FileWebhookStore,
    create_webhook_config,
)

app = APIRouter(prefix='/api/webhooks')


@app.post(
    '/configs',
    response_model=WebhookConfigResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_webhook(
    webhook_data: WebhookConfigCreate,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Create a new webhook configuration for the authenticated user.
    """
    try:
        # Get webhook store
        webhook_store = await FileWebhookStore.get_instance(
            config, current_user.user_id
        )

        # Create webhook config
        webhook = create_webhook_config(
            user_id=current_user.user_id,
            name=webhook_data.name,
            url=str(webhook_data.url),
            events=webhook_data.events,
            repository=webhook_data.repository,
            secret=webhook_data.secret.get_secret_value()
            if webhook_data.secret
            else None,
        )

        # Save webhook config
        await webhook_store.save_webhook_config(webhook)

        # Return webhook config (without secret)
        return WebhookConfigResponse(
            webhook_id=webhook.webhook_id,
            name=webhook.name,
            url=webhook.url,
            events=webhook.events,
            repository=webhook.repository,
            status=webhook.status,
            created_at=webhook.created_at,
            updated_at=webhook.updated_at,
        )
    except Exception as e:
        logger.error(f'Error creating webhook: {str(e)}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Error creating webhook: {str(e)}',
        )


@app.get('/configs', response_model=list[WebhookConfigResponse])
async def list_webhooks(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    List all webhook configurations for the authenticated user.
    """
    try:
        # Get webhook store
        webhook_store = await FileWebhookStore.get_instance(
            config, current_user.user_id
        )

        # List webhook configs
        webhooks = await webhook_store.list_webhook_configs(current_user.user_id)

        # Return webhook configs (without secrets)
        return [
            WebhookConfigResponse(
                webhook_id=webhook.webhook_id,
                name=webhook.name,
                url=webhook.url,
                events=webhook.events,
                repository=webhook.repository,
                status=webhook.status,
                created_at=webhook.created_at,
                updated_at=webhook.updated_at,
            )
            for webhook in webhooks
        ]
    except Exception as e:
        logger.error(f'Error listing webhooks: {str(e)}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Error listing webhooks: {str(e)}',
        )


@app.get(
    '/configs/{webhook_id}',
    response_model=WebhookConfigResponse,
)
async def get_webhook(
    current_user: Annotated[User, Depends(get_current_user)],
    webhook_id: str = Path(..., description='The ID of the webhook to retrieve'),
):
    """
    Get a specific webhook configuration by ID.
    """
    try:
        # Get webhook store
        webhook_store = await FileWebhookStore.get_instance(
            config, current_user.user_id
        )

        # Get webhook config
        webhook = await webhook_store.get_webhook_config(webhook_id)

        # Verify user owns this webhook
        if webhook.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='You do not have permission to access this webhook',
            )

        # Return webhook config (without secret)
        return WebhookConfigResponse(
            webhook_id=webhook.webhook_id,
            name=webhook.name,
            url=webhook.url,
            events=webhook.events,
            repository=webhook.repository,
            status=webhook.status,
            created_at=webhook.created_at,
            updated_at=webhook.updated_at,
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Webhook with ID {webhook_id} not found',
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error retrieving webhook: {str(e)}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Error retrieving webhook: {str(e)}',
        )


@app.patch(
    '/configs/{webhook_id}',
    response_model=WebhookConfigResponse,
)
async def update_webhook(
    webhook_data: WebhookConfigUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    webhook_id: str = Path(..., description='The ID of the webhook to update'),
):
    """
    Update a specific webhook configuration by ID.
    """
    try:
        # Get webhook store
        webhook_store = await FileWebhookStore.get_instance(
            config, current_user.user_id
        )

        # Get existing webhook config
        webhook = await webhook_store.get_webhook_config(webhook_id)

        # Verify user owns this webhook
        if webhook.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='You do not have permission to update this webhook',
            )

        # Update webhook fields
        if webhook_data.name is not None:
            webhook.name = webhook_data.name

        if webhook_data.url is not None:
            webhook.url = webhook_data.url

        if webhook_data.events is not None:
            webhook.events = webhook_data.events

        if webhook_data.repository is not None:
            webhook.repository = webhook_data.repository

        if webhook_data.secret is not None:
            webhook.secret = webhook_data.secret

        if webhook_data.status is not None:
            webhook.status = webhook_data.status

        # Save updated webhook config
        await webhook_store.save_webhook_config(webhook)

        # Return updated webhook config (without secret)
        return WebhookConfigResponse(
            webhook_id=webhook.webhook_id,
            name=webhook.name,
            url=webhook.url,
            events=webhook.events,
            repository=webhook.repository,
            status=webhook.status,
            created_at=webhook.created_at,
            updated_at=webhook.updated_at,
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Webhook with ID {webhook_id} not found',
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error updating webhook: {str(e)}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Error updating webhook: {str(e)}',
        )


@app.delete(
    '/configs/{webhook_id}',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_webhook(
    current_user: Annotated[User, Depends(get_current_user)],
    webhook_id: str = Path(..., description='The ID of the webhook to delete'),
):
    """
    Delete a specific webhook configuration by ID.
    """
    try:
        # Get webhook store
        webhook_store = await FileWebhookStore.get_instance(
            config, current_user.user_id
        )

        # Get existing webhook config to verify ownership
        try:
            webhook = await webhook_store.get_webhook_config(webhook_id)

            # Verify user owns this webhook
            if webhook.user_id != current_user.user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail='You do not have permission to delete this webhook',
                )
        except FileNotFoundError:
            # If webhook doesn't exist, return success (idempotent delete)
            return

        # Delete webhook config
        await webhook_store.delete_webhook_config(webhook_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error deleting webhook: {str(e)}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Error deleting webhook: {str(e)}',
        )


@app.get('/logs', response_model=list[WebhookLogResponse])
async def list_webhook_logs(
    current_user: Annotated[User, Depends(get_current_user)],
    webhook_id: Optional[str] = Query(None, description='Filter logs by webhook ID'),
    limit: int = Query(50, description='Maximum number of logs to return'),
):
    """
    List webhook logs for the authenticated user.
    """
    try:
        # Get webhook store
        webhook_store = await FileWebhookStore.get_instance(
            config, current_user.user_id
        )

        # List webhook logs
        logs = await webhook_store.list_webhook_logs(
            user_id=current_user.user_id,
            webhook_id=webhook_id,
            limit=limit,
        )

        # Return webhook logs
        return [
            WebhookLogResponse(
                log_id=log.log_id,
                webhook_id=log.webhook_id,
                event_type=log.event_type,
                repository=log.repository,
                pr_number=log.pr_number,
                status=log.status,
                response_status=log.response_status,
                error_message=log.error_message,
                created_at=log.created_at,
            )
            for log in logs
        ]
    except Exception as e:
        logger.error(f'Error listing webhook logs: {str(e)}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Error listing webhook logs: {str(e)}',
        )


@app.get(
    '/logs/{log_id}',
    response_model=WebhookLogResponse,
)
async def get_webhook_log(
    current_user: Annotated[User, Depends(get_current_user)],
    log_id: str = Path(..., description='The ID of the webhook log to retrieve'),
):
    """
    Get a specific webhook log by ID.
    """
    try:
        # Get webhook store
        webhook_store = await FileWebhookStore.get_instance(
            config, current_user.user_id
        )

        # Get webhook log
        log = await webhook_store.get_webhook_log(log_id)

        # Verify user owns this log
        if log.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='You do not have permission to access this webhook log',
            )

        # Return webhook log
        return WebhookLogResponse(
            log_id=log.log_id,
            webhook_id=log.webhook_id,
            event_type=log.event_type,
            repository=log.repository,
            pr_number=log.pr_number,
            status=log.status,
            response_status=log.response_status,
            error_message=log.error_message,
            created_at=log.created_at,
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Webhook log with ID {log_id} not found',
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error retrieving webhook log: {str(e)}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Error retrieving webhook log: {str(e)}',
        )
