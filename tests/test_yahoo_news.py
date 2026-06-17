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


def test_extract_article_body_removes_yahoo_javascript_warning() -> None:
    soup = BeautifulSoup(
        """
        <div id="uamods"><div><div>
          <p>現在JavaScriptが無効になっています</p>
          <p>Yahoo!ニュースのすべての機能を利用するためには、JavaScriptの設定を有効にしてください。 JavaScriptの設定を変更する方法はこちら</p>
          <p>本文の第一段落です。</p>
        </div></div></div>
        """,
        "html.parser",
    )

    body = extract_article_body(soup, min_chars=1)

    assert "JavaScript" not in body
    assert body == "本文の第一段落です。"


def test_extract_article_body_joins_split_paragraph_containers() -> None:
    soup = BeautifulSoup(
        """
        <div id="uamods">
          <div><div><p>画像キャプションです。</p></div></div>
          <div><div>
            <p>本文の第一段落です。</p>
            <p>本文の第二段落です。</p>
          </div></div>
        </div>
        """,
        "html.parser",
    )

    body = extract_article_body(soup, min_chars=1)

    assert "画像キャプションです。" in body
    assert "本文の第一段落です。" in body
    assert "本文の第二段落です。" in body
    assert body.index("画像キャプションです。") < body.index("本文の第一段落です。")
