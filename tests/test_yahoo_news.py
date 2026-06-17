from pathlib import Path

import pytest

bs4 = pytest.importorskip("bs4")
from bs4 import BeautifulSoup

from radio_sucrose.news.yahoo import (
    extract_article_body,
    extract_title,
    find_full_article_url,
    parse_rss_items,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_rss_items_extracts_links() -> None:
    items = parse_rss_items((FIXTURES / "yahoo_rss.xml").read_text(encoding="utf-8"))

    assert len(items) == 2
    assert items[0].title == "テストニュース1"
    assert items[0].link == "https://news.yahoo.co.jp/pickup/1"
    assert items[0].pub_date == "Tue, 16 Jun 2026 12:00:00 +0900"


def test_find_full_article_url_by_visible_text() -> None:
    html = (FIXTURES / "yahoo_pickup.html").read_text(encoding="utf-8")

    assert find_full_article_url(html, "https://news.yahoo.co.jp/pickup/1") == "https://news.yahoo.co.jp/articles/full-1"


def test_extract_title_and_body_from_yahoo_article() -> None:
    soup = BeautifulSoup((FIXTURES / "yahoo_article.html").read_text(encoding="utf-8"), "html.parser")

    assert extract_title(soup) == "本文ページタイトル"
    body = extract_article_body(soup, min_chars=1)
    assert "これは第一段落です" in body
    assert "これは第二段落です" in body
    assert "これは第三段落です" in body
    assert "\n" in body
