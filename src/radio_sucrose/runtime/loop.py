from __future__ import annotations

import json
import time

from radio_sucrose.clients.obs import OBSMessageBox
from radio_sucrose.clients.tts import IrodoriTTSClient
from radio_sucrose.config import AppConfig
from radio_sucrose.models import SuperChatMessage
from radio_sucrose.news.yahoo import YAHOO_RSS_FEEDS, YahooNewsFetcher
from radio_sucrose.runtime.director import ProgramDirector
from radio_sucrose.runtime.playback import AudioPlayer, SegmentPlayer
from radio_sucrose.storage.sqlite import SQLiteRepository
from radio_sucrose.clients.dry_run import DryRunScriptClient


class RadioLoop:
    def __init__(
        self,
        config: AppConfig,
        repository: SQLiteRepository,
        news_fetcher: YahooNewsFetcher,
        script_client,
        player: SegmentPlayer,
        director: ProgramDirector,
    ) -> None:
        self.config = config
        self.repository = repository
        self.news_fetcher = news_fetcher
        self.script_client = script_client
        self.player = player
        self.director = director
        self._last_rss_poll = 0.0
        self._dry_run_superchat_seeded = False

    def run_forever(self) -> None:
        self.script_client.warmup()
        while True:
            self.run_once()
            time.sleep(self.config.loop_sleep_seconds)

    def run_once(self) -> None:
        self.poll_rss_if_due()
        self.seed_dry_run_superchat_if_needed()
        payload = self.director.choose_payload()
        print("[PAYLOAD]", json.dumps(payload, ensure_ascii=False)[:500])
        segment = self.script_client.generate_segment(payload)
        self.player.play_segment(segment)
        self.director.mark_payload_done(payload)

    def seed_dry_run_superchat_if_needed(self) -> None:
        if not self.config.dry_run or self._dry_run_superchat_seeded:
            return
        message = getattr(self.config, "dry_run_superchat_message", "")
        if not message:
            return
        self.director.enqueue_superchat(
            SuperChatMessage(
                author=getattr(self.config, "dry_run_superchat_author", "テストリスナー"),
                message=message,
                amount_text=getattr(self.config, "dry_run_superchat_amount", "￥500"),
                currency="JPY",
            )
        )
        self._dry_run_superchat_seeded = True

    def poll_rss_if_due(self) -> None:
        now = time.monotonic()
        if now - self._last_rss_poll < self.config.rss_poll_seconds:
            return
        self._last_rss_poll = now
        for feed in YAHOO_RSS_FEEDS.values():
            try:
                items = self.news_fetcher.fetch_rss_items(feed["url"])
                for item in items[:8]:
                    try:
                        article = self.news_fetcher.fetch_article(item, feed["label"])
                    except Exception as exc:  # keep live loop resilient
                        print(f"[WARN] article fetch failed: {item.link}: {exc}")
                        continue
                    self.repository.insert_article(article)
            except Exception as exc:  # keep live loop resilient
                print(f"[WARN] RSS fetch failed: {feed['url']}: {exc}")


def build_radio_loop(config: AppConfig) -> RadioLoop:
    repository = SQLiteRepository(config.database_path)
    news_fetcher = YahooNewsFetcher()
    from radio_sucrose.prompt import PromptBuilder

    if config.dry_run:
        script_client = DryRunScriptClient()
    else:
        from radio_sucrose.clients.vllm import VLLMScriptClient

        script_client = VLLMScriptClient(config, PromptBuilder(config.refs_dir))
    obs = OBSMessageBox(config)
    tts = IrodoriTTSClient(config)
    audio = AudioPlayer(config)
    player = SegmentPlayer(tts=tts, obs=obs, audio=audio)
    director = ProgramDirector(repository)
    return RadioLoop(config, repository, news_fetcher, script_client, player, director)
