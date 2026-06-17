from __future__ import annotations

from pathlib import Path

from radio_sucrose.clients.tts import IrodoriTTSClient
from radio_sucrose.config import AppConfig
from radio_sucrose.models import TTSChunk


class FakeResponse:
    def __init__(self, content: bytes = b"RIFFfake") -> None:
        self.content = content

    def raise_for_status(self) -> None:
        return None


class FakeSession:
    def __init__(self) -> None:
        self.posts: list[dict] = []

    def post(self, url: str, **kwargs) -> FakeResponse:
        self.posts.append({"url": url, **kwargs})
        return FakeResponse()


def test_irodori_tts_client_calls_server_and_writes_audio(tmp_path: Path) -> None:
    session = FakeSession()
    config = AppConfig(
        dry_run=False,
        irodori_base_url="http://localhost:8088/v1",
        irodori_upload_voices=False,
    )
    client = IrodoriTTSClient(config, output_dir=str(tmp_path), session=session)  # type: ignore[arg-type]
    chunk = TTSChunk(speaker="A", speaker_name="スクロース", tts_text="📖こんにちは。", display_text="こんにちは。")

    audio_path = Path(client.synthesize(chunk))

    assert audio_path.exists()
    assert audio_path.read_bytes() == b"RIFFfake"
    assert session.posts[0]["url"] == "http://localhost:8088/v1/audio/speech"
    assert session.posts[0]["json"]["model"] == "irodori-tts"
    assert session.posts[0]["json"]["input"] == "📖こんにちは。"
    assert session.posts[0]["json"]["voice"] == "sucrose"
    assert session.posts[0]["json"]["irodori"]["chunking_enabled"] is False


def test_irodori_tts_client_uploads_reference_voice_once(tmp_path: Path) -> None:
    refs = tmp_path / "refs"
    refs.mkdir()
    (refs / "sucrose.wav").write_bytes(b"fake wav")
    session = FakeSession()
    config = AppConfig(
        dry_run=False,
        irodori_base_url="http://localhost:8088/v1",
        irodori_upload_voices=True,
    )
    client = IrodoriTTSClient(config, output_dir=str(tmp_path / "tts"), session=session)  # type: ignore[arg-type]
    client.reference_audio_path = lambda speaker: str(refs / "sucrose.wav")  # type: ignore[method-assign]
    chunk = TTSChunk(speaker="A", speaker_name="スクロース", tts_text="📖こんにちは。", display_text="こんにちは。")

    client.synthesize(chunk)
    client.synthesize(chunk)

    upload_posts = [post for post in session.posts if post["url"].endswith("/audio/voices")]
    speech_posts = [post for post in session.posts if post["url"].endswith("/audio/speech")]
    assert len(upload_posts) == 1
    assert upload_posts[0]["data"] == {"voice_id": "sucrose"}
    assert len(speech_posts) == 2
