from __future__ import annotations

import pytest


def test_yahoo_http_client_uses_browser_like_user_agent() -> None:
    pytest.importorskip("bs4")
    pytest.importorskip("requests")
    from radio_sucrose.news.yahoo import HTTPClient

    client = HTTPClient.create()

    assert "Mozilla/5.0" in client.session.headers["User-Agent"]
    assert "Chrome" in client.session.headers["User-Agent"]
    assert client.session.headers["Accept-Language"].startswith("ja")
