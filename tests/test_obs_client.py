from __future__ import annotations

import pytest

from radio_sucrose.clients.obs import OBSMessageBox
from radio_sucrose.config import AppConfig


def test_obs_message_box_disables_itself_when_connection_fails(capsys) -> None:
    obs = OBSMessageBox(AppConfig(obs_required=False, obs_port=1, obs_connect_timeout=0.01))

    obs.set_text("hello")
    obs.set_text("world")

    captured = capsys.readouterr().out
    assert "OBS websocket unavailable" in captured
    assert obs._disabled is True


def test_obs_message_box_can_be_required() -> None:
    obs = OBSMessageBox(AppConfig(obs_required=True, obs_port=1, obs_connect_timeout=0.01))

    with pytest.raises(Exception):
        obs.set_text("hello")
