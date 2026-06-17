from __future__ import annotations

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
            self._disabled = True
            print(f"[WARN] OBS message_box disabled: {exc}")
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
            self._disabled = True
            self._client = None
            print(f"[WARN] OBS message_box disabled after update failure: {exc}")
