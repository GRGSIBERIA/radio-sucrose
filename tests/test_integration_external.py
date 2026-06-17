from __future__ import annotations

import os
from pathlib import Path

import pytest

RUN_INTEGRATION = os.getenv("RADIO_RUN_INTEGRATION_TESTS") == "1"

pytestmark = pytest.mark.integration


def _require_integration() -> None:
    if not RUN_INTEGRATION:
        pytest.skip("set RADIO_RUN_INTEGRATION_TESTS=1 to run external integration tests")


def test_vllm_generates_news_script_from_actual_prompt(tmp_path: Path) -> None:
    _require_integration()
    pytest.importorskip("openai")

    from radio_sucrose.config import AppConfig
    from radio_sucrose.clients.vllm import VLLMScriptClient
    from radio_sucrose.prompt import PromptBuilder

    refs = tmp_path / "refs"
    refs.mkdir()
    (refs / "sucrose.txt").write_text("スクロースは落ち着いたラジオパーソナリティーです。", encoding="utf-8")
    (refs / "dori.txt").write_text("ドリーは好奇心旺盛なゲストです。", encoding="utf-8")

    config = AppConfig.from_env()
    client = VLLMScriptClient(config, PromptBuilder(str(refs)))
    segment = client.generate_segment(
        {
            "task_type": "news_segment",
            "news": {
                "category": "国内",
                "title": "テスト用の国内ニュースタイトル",
                "source": "integration-test",
                "published_at": "2026-06-17T00:00:00+09:00",
                "url": "https://example.invalid/news",
                "body_excerpt": "これはvLLM疎通確認用のニュース本文です。スクロースとドリーが要約と雑談を行う台本を生成してください。",
            },
            "constraints": {
                "target_duration_sec": 180,
                "max_duration_sec": 210,
                "target_total_japanese_chars": 1000,
                "must_include_small_talk": True,
            },
        }
    )

    assert segment.segment_type == "news"
    assert segment.chunks
    assert {chunk.speaker for chunk in segment.chunks}.issubset({"A", "B"})
    assert all(chunk.tts_text for chunk in segment.chunks)
    assert all(chunk.display_text for chunk in segment.chunks)


def test_yahoo_domestic_rss_fetches_one_live_article() -> None:
    _require_integration()
    pytest.importorskip("bs4")
    pytest.importorskip("requests")

    from radio_sucrose.news.yahoo import YAHOO_RSS_FEEDS, YahooNewsFetcher

    fetcher = YahooNewsFetcher()
    domestic_feed = YAHOO_RSS_FEEDS["domestic"]
    items = fetcher.fetch_rss_items(domestic_feed["url"])

    assert items, "Yahoo!ニュース国内RSSからitemを取得できませんでした"

    article = fetcher.fetch_article(items[0], domestic_feed["label"])

    assert article.category == "国内"
    assert article.url == items[0].link
    assert article.title
    assert article.body or article.full_article_url
