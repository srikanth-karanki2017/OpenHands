import hmac
import json
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from openhands.core.logger import openhands_logger as logger
from openhands.integrations.github.webhook_service import GitHubWebhookService
from openhands.server.dependencies import get_dependencies
from openhands.server.shared import config, server_config
from openhands.storage.data_models.webhook_config import WebhookEventType, WebhookLogStatus
from openhands.storage.webhook import FileWebhookStore, create_webhook_log

app = APIRouter(prefix='/api/webhooks', dependencies=get_dependencies())


class GitHubWebhookPayload(BaseModel):
    """Model for GitHub webhook payload."""

    action: str = Field(..., description='The action that was performed')
    pull_request: Optional[dict[str, Any]] = Field(
        None, description='Pull request data'
    )
    repository: dict[str, Any] = Field(..., description='Repository data')
    sender: dict[str, Any] = Field(..., description='User who triggered the event')


@app.post('/github')
async def github_webhook(
    request: Request,
    x_github_event: str = Header(..., description='GitHub event type'),
    x_hub_signature_256: Optional[str] = Header(
        None, description='GitHub webhook signature'
    ),
    user_id: Optional[str] = Query(None, description='User ID for webhook validation'),
    webhook_id: Optional[str] = Query(None, description='Webhook ID for logging'),
):
    """
    Handle GitHub webhook events.

    This endpoint receives webhook events from GitHub, validates them,
    and triggers the appropriate OpenHands automation process.

    Currently supported events:
    - pull_request (opened, synchronize, reopened)
    """
    # Get the raw request body
    body = await request.body()
    
    # Parse the payload first to extract repository info for logging
    try:
        payload_dict = json.loads(body)
        repo_full_name = str(payload_dict.get('repository', {}).get('full_name', ''))
        pr_number = None
        
        if x_github_event == 'pull_request' and 'pull_request' in payload_dict:
            pr_number = int(payload_dict['pull_request'].get('number', 0))
    except Exception:
        repo_full_name = None
        pr_number = None

    # Create webhook log entry if user_id and webhook_id are provided
    webhook_log = None
    webhook_store = None
    
    if user_id and webhook_id:
        try:
            webhook_store = await FileWebhookStore.get_instance(config, user_id)
            
            # Create log entry
            webhook_log = create_webhook_log(
                webhook_id=webhook_id,
                user_id=user_id,
                event_type=WebhookEventType.PULL_REQUEST if x_github_event == 'pull_request' else WebhookEventType.ALL,
                repository=repo_full_name,
                pr_number=pr_number,
                status=WebhookLogStatus.PENDING,
                request_payload=payload_dict,
            )
            
            # Save log entry
            await webhook_store.save_webhook_log(webhook_log)
        except Exception as e:
            logger.error(f"Error creating webhook log: {str(e)}")
            # Continue processing even if log creation fails

    # Verify webhook signature if configured
    webhook_secret = None
    
    # First try user-specific webhook secret if user_id and webhook_id are provided
    if user_id and webhook_id and webhook_store:
        try:
            webhook_config = await webhook_store.get_webhook_config(webhook_id)
            if webhook_config and webhook_config.secret:
                webhook_secret = webhook_config.secret.get_secret_value()
        except Exception as e:
            logger.error(f"Error retrieving webhook config: {str(e)}")
    
    # Fall back to global webhook secret if no user-specific secret
    if not webhook_secret:
        webhook_secret = server_config.github_webhook_secret
    
    # Verify signature if secret and signature are provided
    if webhook_secret and x_hub_signature_256:
        signature = hmac.new(
            webhook_secret.encode(), msg=body, digestmod='sha256'
        ).hexdigest()
        expected_signature = f'sha256={signature}'

        if not hmac.compare_digest(expected_signature, x_hub_signature_256):
            logger.warning(
                'Invalid GitHub webhook signature', extra={'event': x_github_event}
            )
            
            # Update log entry if it exists
            if webhook_log and webhook_store:
                webhook_log.status = WebhookLogStatus.FAILURE
                webhook_log.error_message = "Invalid webhook signature"
                await webhook_store.save_webhook_log(webhook_log)
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid signature'
            )

    # Parse the payload
    try:
        # Only process pull_request events for now
        if x_github_event == 'pull_request':
            payload = GitHubWebhookPayload(**payload_dict)

            # Only process certain PR actions
            if payload.action in ['opened', 'synchronize', 'reopened']:
                # Extract relevant information
                repo_full_name = str(payload.repository.get('full_name', ''))
                pr_number = (
                    int(payload.pull_request.get('number', 0))
                    if payload.pull_request
                    else 0
                )
                pr_title = (
                    str(payload.pull_request.get('title', ''))
                    if payload.pull_request
                    else ''
                )
                pr_body = (
                    payload.pull_request.get('body') if payload.pull_request else None
                )

                # Get head and base branch with proper type checking
                head_dict = (
                    payload.pull_request.get('head', {}) if payload.pull_request else {}
                )
                base_dict = (
                    payload.pull_request.get('base', {}) if payload.pull_request else {}
                )
                pr_head_branch = str(head_dict.get('ref', ''))
                pr_base_branch = str(base_dict.get('ref', ''))

                logger.info(
                    f'Processing GitHub PR webhook: {repo_full_name}#{pr_number}',
                    extra={
                        'event': x_github_event,
                        'action': payload.action,
                        'repo': repo_full_name,
                        'pr_number': pr_number,
                        'user_id': user_id,
                        'webhook_id': webhook_id,
                    },
                )

                # Process the PR event using the webhook service
                webhook_service = GitHubWebhookService()
                result = await webhook_service.process_pr_event(
                    repo_full_name=repo_full_name,
                    pr_number=pr_number,
                    pr_title=pr_title,
                    pr_body=pr_body,
                    pr_head_branch=pr_head_branch,
                    pr_base_branch=pr_base_branch,
                    action=payload.action,
                    sender=payload.sender,
                    user_id=user_id,  # Pass user_id to webhook service
                )

                # Add event info to the result
                result['event'] = x_github_event
                result['action'] = payload.action
                
                # Update log entry if it exists
                if webhook_log and webhook_store:
                    webhook_log.status = WebhookLogStatus.SUCCESS
                    webhook_log.response_status = 200
                    await webhook_store.save_webhook_log(webhook_log)

                return result

        # Update log entry for ignored events
        if webhook_log and webhook_store:
            webhook_log.status = WebhookLogStatus.SUCCESS
            webhook_log.response_status = 200
            webhook_log.error_message = f"Event {x_github_event} with action {payload_dict.get('action')} not processed"
            await webhook_store.save_webhook_log(webhook_log)

        return {
            'status': 'ignored',
            'message': f'Event {x_github_event} with action {payload_dict.get("action")} not processed',
            'event': x_github_event,
        }

    except Exception as e:
        logger.error(
            f'Error processing GitHub webhook: {str(e)}',
            extra={'event': x_github_event},
            exc_info=True,
        )
        
        # Update log entry if it exists
        if webhook_log and webhook_store:
            webhook_log.status = WebhookLogStatus.FAILURE
            webhook_log.error_message = str(e)
            await webhook_store.save_webhook_log(webhook_log)
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Error processing webhook: {str(e)}',
        )
