from __future__ import annotations

import socket

from radio_sucrose.config import AppConfig


class OBSMessageBox:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._client = None
        self._disabled = False

    def connect(self) -> bool:
        if self.config.dry_run:
            return False
        if self._disabled:
            return False

        if not self._preflight_socket():
            return False

        try:
            from obsws_python import ReqClient

            self._client = ReqClient(
                host=self.config.obs_host,
                port=self.config.obs_port,
                password=self.config.obs_password,
            )
        except Exception as exc:
            self._client = None
            if self.config.obs_required:
                raise

            self._disable(f"OBS message_box disabled: {exc}")

            return False
        return True

    def set_text(self, text: str) -> None:
        if self.config.dry_run:
            print(f"[OBS:{self.config.obs_message_source}] {text}")
            return

        if self._disabled:
            return
        if self._client is None and not self.connect():
            return
        assert self._client is not None
        try:
            self._client.set_input_settings(
                name=self.config.obs_message_source,
                settings={"text": text},
                overlay=True,
            )
        except Exception as exc:
            if self.config.obs_required:
                raise

            self._client = None
            self._disable(f"OBS message_box disabled after update failure: {exc}")

    def _preflight_socket(self) -> bool:
        try:
            with socket.create_connection(
                (self.config.obs_host, self.config.obs_port),
                timeout=self.config.obs_connect_timeout,
            ):
                return True
        except OSError as exc:
            if self.config.obs_required:
                raise
            self._disable(f"OBS websocket unavailable at {self.config.obs_host}:{self.config.obs_port}: {exc}")
            return False

    def _disable(self, message: str) -> None:
        self._disabled = True
        print(f"[WARN] {message}")

