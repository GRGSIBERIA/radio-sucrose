from __future__ import annotations

from radio_sucrose.config import AppConfig


class OBSMessageBox:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._client = None

    def connect(self) -> None:
        if self.config.dry_run:
            return
        from obsws_python import ReqClient

        self._client = ReqClient(
            host=self.config.obs_host,
            port=self.config.obs_port,
            password=self.config.obs_password,
        )

    def set_text(self, text: str) -> None:
        if self.config.dry_run:
            print(f"[OBS:{self.config.obs_message_source}] {text}")
            return
        if self._client is None:
            self.connect()
        assert self._client is not None
        self._client.set_input_settings(
            name=self.config.obs_message_source,
            settings={"text": text},
            overlay=True,
        )
