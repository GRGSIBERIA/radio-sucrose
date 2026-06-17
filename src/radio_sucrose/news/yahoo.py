from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin

from bs4 import BeautifulSoup
import requests

from radio_sucrose.models import NewsArticle, RSSItem
from radio_sucrose.text import clean_article_text

YAHOO_RSS_FEEDS: dict[str, dict[str, str]] = {
    "top": {"label": "主要", "url": "https://news.yahoo.co.jp/rss/topics/top-picks.xml"},
    "domestic": {"label": "国内", "url": "https://news.yahoo.co.jp/rss/topics/domestic.xml"},
    "world": {"label": "国際", "url": "https://news.yahoo.co.jp/rss/topics/world.xml"},
    "business": {"label": "経済", "url": "https://news.yahoo.co.jp/rss/topics/business.xml"},
    "entertainment": {"label": "エンタメ", "url": "https://news.yahoo.co.jp/rss/topics/entertainment.xml"},
    "sports": {"label": "スポーツ", "url": "https://news.yahoo.co.jp/rss/topics/sports.xml"},
    "it": {"label": "IT", "url": "https://news.yahoo.co.jp/rss/topics/it.xml"},
    "science": {"label": "科学", "url": "https://news.yahoo.co.jp/rss/topics/science.xml"},
    "local": {"label": "地域", "url": "https://news.yahoo.co.jp/rss/topics/local.xml"},
}

ARTICLE_BODY_SELECTORS = [
    "#uamods > div:nth-of-type(1) > div",
    "#uamods",
    "article",
    "main",
]

DROP_TEXT_PATTERNS = (
    "この記事はいかがでしたか",
    "関連記事",
    "コメント",
    "シェア",
    "Facebook",
    "LINE",
    "Xで",
    "現在JavaScriptが無効になっています",
    "Yahoo!ニュースのすべての機能を利用するためには",
    "JavaScriptの設定を変更する方法はこちら",
)


@dataclass(frozen=True)
class HTTPClient:
    session: requests.Session

    @classmethod
    def create(cls) -> "HTTPClient":
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (compatible; RadioSucroseBot/0.1; "
                    "+https://example.invalid)"
                )
            }
        )
        return cls(session=session)

    def get_text(self, url: str, timeout: float = 10.0) -> str:
        response = self.session.get(url, timeout=timeout)
        response.raise_for_status()
        if not response.encoding:
            response.encoding = response.apparent_encoding
        return response.text


def parse_rss_items(xml: str) -> list[RSSItem]:
    soup = BeautifulSoup(xml, "xml")
    items: list[RSSItem] = []
    for item in soup.select("channel > item"):
        title = _select_text(item, "title")
        link = _select_text(item, "link")
        pub_date = _select_text(item, "pubDate")
        if title and link:
            items.append(RSSItem(title=title, link=link, pub_date=pub_date))
    return items


def find_full_article_url(html: str, base_url: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    for anchor in soup.find_all("a"):
        text = anchor.get_text(" ", strip=True)
        if "記事全文を読む" in text:
            href = anchor.get("href")
            if href:
                return urljoin(base_url, href)
    return None


def extract_title(soup: BeautifulSoup) -> str | None:
    for selector in ("header h1", "h1"):
        title = _select_text(soup, selector)
        if title:
            return title
    return None


def extract_article_body(soup: BeautifulSoup, min_chars: int = 100) -> str:
    bodies: list[str] = []
    seen: set[str] = set()
    for selector in ARTICLE_BODY_SELECTORS:
        for container in soup.select(selector):
            paragraphs = _extract_paragraphs(container)
            if not paragraphs:
                continue
            body = clean_article_text("\n".join(paragraphs))
            if body and body not in seen:
                seen.add(body)
                bodies.append(body)
    if not bodies:
        return ""

    full_body = clean_article_text("\n".join(bodies))
    if len(full_body) >= min_chars:
        return full_body

    return max(bodies, key=len)


def _extract_paragraphs(container: BeautifulSoup) -> list[str]:
    paragraphs: list[str] = []
    for paragraph in container.find_all("p", recursive=True):
        text = clean_article_text(paragraph.get_text(" ", strip=True))
        if text and not _is_noise(text):
            paragraphs.append(text)
    return paragraphs



class YahooNewsFetcher:
    def __init__(self, http: HTTPClient | None = None) -> None:
        self.http = http or HTTPClient.create()

    def fetch_rss_items(self, rss_url: str) -> list[RSSItem]:
        return parse_rss_items(self.http.get_text(rss_url))

    def fetch_article(self, item: RSSItem, category: str) -> NewsArticle:
        initial_html = self.http.get_text(item.link)
        full_url = find_full_article_url(initial_html, item.link)
        article_url = full_url or item.link
        article_html = self.http.get_text(article_url) if full_url else initial_html
        soup = BeautifulSoup(article_html, "html.parser")
        title = extract_title(soup) or item.title
        body = extract_article_body(soup)
        return NewsArticle(
            url=item.link,
            full_article_url=full_url,
            title=title,
            body=body,
            category=category,
            published_at=item.pub_date,
        )


def _select_text(soup: BeautifulSoup, selector: str) -> str | None:
    element = soup.select_one(selector)
    if element is None:
        return None
    text = element.get_text(" ", strip=True)
    return text or None


def _is_noise(text: str) -> bool:
    return any(pattern in text for pattern in DROP_TEXT_PATTERNS)
