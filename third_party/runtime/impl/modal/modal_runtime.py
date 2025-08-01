import os
import tempfile
from pathlib import Path
from typing import Callable

import httpx
import modal
import tenacity

from openhands.core.config import OpenHandsConfig
from openhands.events import EventStream
from openhands.integrations.provider import PROVIDER_TOKEN_TYPE
from openhands.runtime.impl.action_execution.action_execution_client import (
    ActionExecutionClient,
)
from openhands.runtime.plugins import PluginRequirement
from openhands.runtime.runtime_status import RuntimeStatus
from openhands.runtime.utils.command import get_action_execution_server_startup_command
from openhands.runtime.utils.runtime_build import (
    BuildFromImageType,
    prep_build_folder,
)
from openhands.utils.async_utils import call_sync_from_async
from openhands.utils.tenacity_stop import stop_if_should_exit

# FIXME: this will not work in HA mode. We need a better way to track IDs
MODAL_RUNTIME_IDS: dict[str, str] = {}


class ModalRuntime(ActionExecutionClient):
    """This runtime will subscribe the event stream.

    When receive an event, it will send the event to runtime-client which run inside the Modal sandbox environment.

    Args:
        config (OpenHandsConfig): The application configuration.
        event_stream (EventStream): The event stream to subscribe to.
        sid (str, optional): The session ID. Defaults to 'default'.
        plugins (list[PluginRequirement] | None, optional): List of plugin requirements. Defaults to None.
        env_vars (dict[str, str] | None, optional): Environment variables to set. Defaults to None.
    """

    container_name_prefix = 'openhands-sandbox-'
    sandbox: modal.Sandbox | None
    sid: str

    def __init__(
        self,
        config: OpenHandsConfig,
        event_stream: EventStream,
        sid: str = 'default',
        plugins: list[PluginRequirement] | None = None,
        env_vars: dict[str, str] | None = None,
        status_callback: Callable | None = None,
        attach_to_existing: bool = False,
        headless_mode: bool = True,
        user_id: str | None = None,
        git_provider_tokens: PROVIDER_TOKEN_TYPE | None = None,
    ):
        # Read Modal API credentials from environment variables
        modal_token_id = os.getenv('MODAL_TOKEN_ID')
        modal_token_secret = os.getenv('MODAL_TOKEN_SECRET')

        if not modal_token_id:
            raise ValueError('MODAL_TOKEN_ID environment variable is required for Modal runtime')
        if not modal_token_secret:
            raise ValueError('MODAL_TOKEN_SECRET environment variable is required for Modal runtime')

        self.config = config
        self.sandbox = None
        self.sid = sid

        self.modal_client = modal.Client.from_credentials(
            modal_token_id,
            modal_token_secret,
        )
        self.app = modal.App.lookup(
            'openhands', create_if_missing=True, client=self.modal_client
        )

        # workspace_base cannot be used because we can't bind mount into a sandbox.
        if self.config.workspace_base is not None:
            self.log(
                'warning',
                'Setting workspace_base is not supported in the modal runtime.',
            )

        # This value is arbitrary as it's private to the container
        self.container_port = 3000
        self._vscode_port = 4445
        self._vscode_url: str | None = None

        self.status_callback = status_callback
        self.base_container_image_id = self.config.sandbox.base_container_image
        self.runtime_container_image_id = self.config.sandbox.runtime_container_image

        if self.config.sandbox.runtime_extra_deps:
            self.log(
                'debug',
                f'Installing extra user-provided dependencies in the runtime image: {self.config.sandbox.runtime_extra_deps}',
            )

        super().__init__(
            config,
            event_stream,
            sid,
            plugins,
            env_vars,
            status_callback,
            attach_to_existing,
            headless_mode,
            user_id,
            git_provider_tokens,
        )

    async def connect(self):
        self.set_runtime_status(RuntimeStatus.STARTING_RUNTIME)

        self.log('debug', f'ModalRuntime `{self.sid}`')

        self.image = self._get_image_definition(
            self.base_container_image_id,
            self.runtime_container_image_id,
            self.config.sandbox.runtime_extra_deps,
        )

        if self.attach_to_existing:
            if self.sid in MODAL_RUNTIME_IDS:
                sandbox_id = MODAL_RUNTIME_IDS[self.sid]
                self.log('debug', f'Attaching to existing Modal sandbox: {sandbox_id}')
                self.sandbox = modal.Sandbox.from_id(
                    sandbox_id, client=self.modal_client
                )
        else:
            self.set_runtime_status(RuntimeStatus.STARTING_RUNTIME)
            await call_sync_from_async(
                self._init_sandbox,
                sandbox_workspace_dir=self.config.workspace_mount_path_in_sandbox,
                plugins=self.plugins,
            )

            self.set_runtime_status(RuntimeStatus.RUNTIME_STARTED)

        if self.sandbox is None:
            raise Exception('Sandbox not initialized')
        tunnel = self.sandbox.tunnels()[self.container_port]
        self.api_url = tunnel.url
        self.log('debug', f'Container started. Server url: {self.api_url}')

        if not self.attach_to_existing:
            self.log('debug', 'Waiting for client to become ready...')
            self.set_runtime_status(RuntimeStatus.STARTING_RUNTIME)

        self._wait_until_alive()
        self.setup_initial_env()

        if not self.attach_to_existing:
            self.set_runtime_status(RuntimeStatus.READY)
        self._runtime_initialized = True

    @property
    def action_execution_server_url(self):
        return self.api_url

    @tenacity.retry(
        stop=tenacity.stop_after_delay(120) | stop_if_should_exit(),
        retry=tenacity.retry_if_exception_type((ConnectionError, httpx.NetworkError)),
        reraise=True,
        wait=tenacity.wait_fixed(2),
    )
    def _wait_until_alive(self):
        self.check_if_alive()

    def _get_image_definition(
        self,
        base_container_image_id: str | None,
        runtime_container_image_id: str | None,
        runtime_extra_deps: str | None,
    ) -> modal.Image:
        if runtime_container_image_id:
            base_runtime_image = modal.Image.from_registry(runtime_container_image_id)
        elif base_container_image_id:
            build_folder = tempfile.mkdtemp()
            prep_build_folder(
                build_folder=Path(build_folder),
                base_image=base_container_image_id,
                build_from=BuildFromImageType.SCRATCH,
                extra_deps=runtime_extra_deps,
                enable_browser=True,
            )

            base_runtime_image = modal.Image.from_dockerfile(
                path=os.path.join(build_folder, 'Dockerfile'),
                context_mount=modal.Mount.from_local_dir(
                    local_path=build_folder,
                    remote_path='.',  # to current WORKDIR
                ),
            )
        else:
            raise ValueError(
                'Neither runtime container image nor base container image is set'
            )

        return base_runtime_image.run_commands(
            """
# Disable bracketed paste
# https://github.com/pexpect/pexpect/issues/669
echo "set enable-bracketed-paste off" >> /etc/inputrc && \\
echo 'export INPUTRC=/etc/inputrc' >> /etc/bash.bashrc
""".strip()
        )

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(5),
        wait=tenacity.wait_exponential(multiplier=1, min=4, max=60),
    )
    def _init_sandbox(
        self,
        sandbox_workspace_dir: str,
        plugins: list[PluginRequirement] | None = None,
    ):
        try:
            self.log('debug', 'Preparing to start container...')
            # Combine environment variables
            environment: dict[str, str | None] = {
                'port': str(self.container_port),
                'PYTHONUNBUFFERED': '1',
                'VSCODE_PORT': str(self._vscode_port),
            }
            if self.config.debug:
                environment['DEBUG'] = 'true'

            env_secret = modal.Secret.from_dict(environment)

            self.log('debug', f'Sandbox workspace: {sandbox_workspace_dir}')
            sandbox_start_cmd = get_action_execution_server_startup_command(
                server_port=self.container_port,
                plugins=self.plugins,
                app_config=self.config,
            )
            self.log('debug', f'Starting container with command: {sandbox_start_cmd}')
            self.sandbox = modal.Sandbox.create(
                *sandbox_start_cmd,
                secrets=[env_secret],
                workdir='/openhands/code',
                encrypted_ports=[self.container_port, self._vscode_port],
                image=self.image,
                app=self.app,
                client=self.modal_client,
                timeout=60 * 60,
            )
            MODAL_RUNTIME_IDS[self.sid] = self.sandbox.object_id
            self.log('debug', 'Container started')

        except Exception as e:
            self.log(
                'error', f'Error: Instance {self.sid} FAILED to start container!\n'
            )
            self.log('error', str(e))
            self.close()
            raise e

    def close(self):
        """Closes the ModalRuntime and associated objects."""
        super().close()

        if not self.attach_to_existing and self.sandbox:
            self.sandbox.terminate()

    @property
    def vscode_url(self) -> str | None:
        if self._vscode_url is not None:  # cached value
            self.log('debug', f'VSCode URL: {self._vscode_url}')
            return self._vscode_url
        token = super().get_vscode_token()
        if not token:
            self.log('error', 'VSCode token not found')
            return None
        if not self.sandbox:
            self.log('error', 'Sandbox not initialized')
            return None

        tunnel = self.sandbox.tunnels()[self._vscode_port]
        tunnel_url = tunnel.url
        self._vscode_url = (
            tunnel_url
            + f'/?tkn={token}&folder={self.config.workspace_mount_path_in_sandbox}'
        )

        self.log(
            'debug',
            f'VSCode URL: {self._vscode_url}',
        )

        return self._vscode_url
