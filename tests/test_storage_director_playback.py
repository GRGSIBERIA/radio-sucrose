from radio_sucrose.clients.dry_run import DryRunScriptClient
from radio_sucrose.models import NewsArticle, SuperChatMessage, TTSChunk
from radio_sucrose.runtime.director import ProgramDirector
from radio_sucrose.runtime.playback import natural_pause_after
from radio_sucrose.storage.sqlite import SQLiteRepository


def test_sqlite_deduplicates_articles_by_url() -> None:
    repo = SQLiteRepository(":memory:")
    article = NewsArticle(url="https://example.com/a", title="A", category="主要")

    assert repo.insert_article(article) is True
    assert repo.insert_article(article) is False


def test_director_prefers_news_then_marks_read() -> None:
    repo = SQLiteRepository(":memory:")
    repo.insert_article(NewsArticle(url="https://example.com/a", title="A", category="主要", body="本文"))
    director = ProgramDirector(repo)

    payload = director.choose_payload()
    assert payload["task_type"] == "news_segment"
    assert payload["news"]["title"] == "A"
    director.mark_payload_done(payload)
    assert director.choose_payload()["task_type"] == "idle_talk"


def test_natural_pause_uses_period_speaker_change_and_segment_end() -> None:
    chunk = TTSChunk(speaker="A", speaker_name="スクロース", tts_text="📖テストです。", display_text="テストです。")

    assert natural_pause_after(chunk, speaker_changed=True, segment_end=True) == 1.0


def test_superchat_waits_until_after_news_when_news_is_available() -> None:
    repo = SQLiteRepository(":memory:")
    repo.insert_article(NewsArticle(url="https://example.com/news", title="News", category="主要", body="本文"))
    director = ProgramDirector(repo)
    director.enqueue_superchat(SuperChatMessage(author="相談者", message="進路で迷っています"))

    first = director.choose_payload()
    assert first["task_type"] == "news_segment"

    director.mark_payload_done(first)
    second = director.choose_payload()
    assert second["task_type"] == "superchat_segment"
    assert second["superchat"]["author"] == "相談者"

    director.mark_payload_done(second)
    assert director.pending_superchat_count() == 0


def test_superchat_is_chosen_when_no_news_is_available() -> None:
    repo = SQLiteRepository(":memory:")
    director = ProgramDirector(repo)
    director.enqueue_superchat(SuperChatMessage(author="相談者", message="転職すべきか悩んでいます", amount_text="￥1,000"))

    payload = director.choose_payload()

    assert payload["task_type"] == "superchat_segment"
    assert payload["constraints"]["treat_as_listener_letter"] is True


def test_dry_run_script_client_generates_superchat_reading() -> None:
    client = DryRunScriptClient()
    segment = client.generate_segment(
        {
            "task_type": "superchat_segment",
            "superchat": {
                "author": "相談者",
                "message": "転職すべきか悩んでいます",
                "amount_text": "￥1,000",
            },
        }
    )

    assert segment.segment_type == "superchat"
    assert any("ラジオネーム相談者さん" in chunk.display_text for chunk in segment.chunks)
    assert any("スーパーチャット" in chunk.display_text for chunk in segment.chunks)
    assert any("転職すべきか悩んでいます" in chunk.display_text for chunk in segment.chunks)

def test_director_sends_full_cleaned_article_body_to_vllm() -> None:
    repo = SQLiteRepository(":memory:")
    body = "本文1。\n" + "長い本文。" * 500
    repo.insert_article(NewsArticle(url="https://example.com/full", title="Full", category="国内", body=body))
    director = ProgramDirector(repo)

    payload = director.choose_payload()

    assert payload["news"]["body"] == body
    assert payload["news"]["body_excerpt"] == body
    assert len(payload["news"]["body_excerpt"]) > 1800


def test_segment_player_logs_spoken_display_text(capsys, tmp_path) -> None:
    from radio_sucrose.clients.obs import OBSMessageBox
    from radio_sucrose.clients.tts import IrodoriTTSClient
    from radio_sucrose.config import AppConfig
    from radio_sucrose.models import Segment
    from radio_sucrose.runtime.playback import AudioPlayer, SegmentPlayer

    config = AppConfig(dry_run=True, log_spoken_text=True)
    player = SegmentPlayer(
        tts=IrodoriTTSClient(config, output_dir=str(tmp_path)),
        obs=OBSMessageBox(config),
        audio=AudioPlayer(config),
    )
    segment = Segment(
        segment_type="news",
        chunks=[TTSChunk(speaker="A", speaker_name="スクロース", tts_text="📖こんにちは。", display_text="こんにちは。")],
    )

    player.play_segment(segment)

    assert "[SCRIPT] スクロース: こんにちは。" in capsys.readouterr().out

