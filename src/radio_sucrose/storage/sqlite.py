from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

from radio_sucrose.models import NewsArticle

SCHEMA = """
CREATE TABLE IF NOT EXISTS articles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  url TEXT NOT NULL UNIQUE,
  canonical_url TEXT,
  full_article_url TEXT,
  title TEXT NOT NULL,
  body TEXT,
  source TEXT,
  category TEXT NOT NULL,
  published_at TEXT,
  discovered_at TEXT NOT NULL,
  read_at TEXT,
  status TEXT NOT NULL DEFAULT 'candidate'
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_articles_full_article_url
ON articles(full_article_url)
WHERE full_article_url IS NOT NULL;

CREATE TABLE IF NOT EXISTS idle_topics (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  large_category TEXT NOT NULL,
  middle_category TEXT NOT NULL,
  small_category TEXT NOT NULL,
  used_at TEXT NOT NULL
);
"""


class SQLiteRepository:
    def __init__(self, path: str) -> None:
        self.path = path
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True) if Path(path).parent != Path(".") else None
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def insert_article(self, article: NewsArticle) -> bool:
        try:
            self.conn.execute(
                """
                INSERT INTO articles (
                  url, canonical_url, full_article_url, title, body, source,
                  category, published_at, discovered_at, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'candidate')
                """,
                (
                    article.url,
                    article.canonical_url,
                    article.full_article_url,
                    article.title,
                    article.body,
                    article.source,
                    article.category,
                    article.published_at,
                    article.discovered_at,
                ),
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def insert_articles(self, articles: Iterable[NewsArticle]) -> int:
        return sum(1 for article in articles if self.insert_article(article))

    def next_candidate_article(self) -> NewsArticle | None:
        row = self.conn.execute(
            """
            SELECT * FROM articles
            WHERE status = 'candidate'
            ORDER BY published_at DESC, discovered_at DESC
            LIMIT 1
            """
        ).fetchone()
        if row is None:
            return None
        return NewsArticle(
            url=row["url"],
            canonical_url=row["canonical_url"],
            full_article_url=row["full_article_url"],
            title=row["title"],
            body=row["body"] or "",
            source=row["source"] or "Yahoo!ニュース",
            category=row["category"],
            published_at=row["published_at"],
            discovered_at=row["discovered_at"],
        )

    def mark_read(self, url: str, read_at: str) -> None:
        self.conn.execute(
            "UPDATE articles SET status = 'read', read_at = ? WHERE url = ?",
            (read_at, url),
        )
        self.conn.commit()
