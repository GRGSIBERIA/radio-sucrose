from __future__ import annotations

from datetime import datetime, timezone

from radio_sucrose.models import NewsArticle, SuperChatMessage
from radio_sucrose.text import clean_article_text
from radio_sucrose.storage.sqlite import SQLiteRepository


class ProgramDirector:
    def __init__(self, repository: SQLiteRepository) -> None:
        self.repository = repository
        self._pending_superchats: list[SuperChatMessage] = []
        self._prefer_superchat_after_news = False

    def enqueue_superchat(self, message: SuperChatMessage) -> None:
        self._pending_superchats.append(message)

    def pending_superchat_count(self) -> int:
        return len(self._pending_superchats)

    def choose_payload(self) -> dict:
        if self._pending_superchats and self._prefer_superchat_after_news:
            return self._superchat_payload(self._pending_superchats[0])

        article = self.repository.next_candidate_article()
        if article is not None:
            return self._news_payload(article)

        if self._pending_superchats:
            return self._superchat_payload(self._pending_superchats[0])

        return self._idle_payload()

    def mark_payload_done(self, payload: dict) -> None:
        if payload.get("task_type") == "news_segment":
            url = payload["news"]["url"]
            self.repository.mark_read(url, datetime.now(timezone.utc).isoformat())
            self._prefer_superchat_after_news = bool(self._pending_superchats)
        elif payload.get("task_type") == "superchat_segment":
            if self._pending_superchats:
                self._pending_superchats.pop(0)
            self._prefer_superchat_after_news = False
        else:
            self._prefer_superchat_after_news = False

    def _news_payload(self, article: NewsArticle) -> dict:
        return {
            "task_type": "news_segment",
            "news": {
                "category": article.category,
                "title": article.title,
                "source": article.source,
                "published_at": article.published_at,
                "url": article.full_article_url or article.url,
                "body": clean_article_text(article.body),
                "body_excerpt": clean_article_text(article.body),
            },
            "constraints": {
                "target_duration_sec": 180,
                "max_duration_sec": 210,
                "target_total_japanese_chars": 1000,
                "must_include_small_talk": True,
            },
        }

    def _superchat_payload(self, message: SuperChatMessage) -> dict:
        return {
            "task_type": "superchat_segment",
            "superchat": {
                "author": message.author,
                "message": message.message,
                "amount_text": message.amount_text,
                "amount_micros": message.amount_micros,
                "currency": message.currency,
                "received_at": message.received_at,
            },
            "constraints": {
                "treat_as_listener_letter": True,
                "do_not_base_depth_only_on_amount": True,
            },
        }

    def _idle_payload(self) -> dict:
        return {
            "task_type": "idle_talk",
            "constraints": {
                "duration_sec": 120,
                "use_topic_taxonomy": True,
                "taxonomy_depth": 3,
            },
        }
