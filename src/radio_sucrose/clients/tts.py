from __future__ import annotations

import hashlib
from pathlib import Path
import wave

from radio_sucrose.config import AppConfig
from radio_sucrose.models import SPEAKERS, TTSChunk


class IrodoriTTSClient:
    """Irodori-TTS wrapper.

    The real HTTP/SDK integration is intentionally isolated here. In dry-run mode
    this writes a tiny silent WAV so the playback loop and tests can run without
    the TTS service.
    """

    def __init__(self, config: AppConfig, output_dir: str = "tmp/tts") -> None:
        self.config = config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def synthesize(self, chunk: TTSChunk) -> str:
        if not self.config.dry_run:
            raise NotImplementedError("Configure the real Irodori-TTS backend in this wrapper.")
        digest = hashlib.sha256(f"{chunk.speaker}:{chunk.tts_text}".encode("utf-8")).hexdigest()[:16]
        path = self.output_dir / f"{digest}.wav"
        if not path.exists():
            _write_silent_wav(path)
        return str(path)

    def reference_audio_path(self, speaker: str) -> str:
        return SPEAKERS[speaker].reference_audio_path


def _write_silent_wav(path: Path, duration_seconds: float = 0.15, sample_rate: int = 16000) -> None:
    frames = int(duration_seconds * sample_rate)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b"\x00\x00" * frames)
