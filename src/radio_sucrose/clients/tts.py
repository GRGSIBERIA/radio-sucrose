from __future__ import annotations

import hashlib
from pathlib import Path
import wave

from radio_sucrose.config import AppConfig
from radio_sucrose.models import SPEAKERS, TTSChunk


class IrodoriTTSClient:
    """Irodori-TTS-Server client with a dry-run silent WAV fallback."""

    def __init__(self, config: AppConfig, output_dir: str = "tmp/tts", session=None) -> None:
        self.config = config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if session is None and not config.dry_run:

            import requests

            session = requests.Session()
        self.session = session
        self._uploaded_voice_ids: set[str] = set()

    def synthesize(self, chunk: TTSChunk) -> str:
        digest = hashlib.sha256(f"{chunk.speaker}:{chunk.tts_text}".encode("utf-8")).hexdigest()[:16]
        path = self.output_dir / f"{digest}.{self.config.irodori_response_format}"
        if self.config.dry_run:
            if not path.exists():
                _write_silent_wav(path)
            return str(path)

        voice_id = self.voice_id_for_speaker(chunk.speaker)
        self.ensure_voice_uploaded(chunk.speaker, voice_id)
        response = self.session.post(
            self._url("/audio/speech"),
            headers=self._headers(),
            json=self._speech_payload(chunk, voice_id),
            timeout=120,
        )
        response.raise_for_status()
        path.write_bytes(response.content)
        return str(path)

    def ensure_voice_uploaded(self, speaker: str, voice_id: str) -> None:
        if not self.config.irodori_upload_voices or voice_id in self._uploaded_voice_ids:
            return
        reference_path = Path(self.reference_audio_path(speaker))
        if not reference_path.exists():
            return
        with reference_path.open("rb") as voice_file:
            response = self.session.post(
                self._url("/audio/voices"),
                headers=self._auth_headers(),
                data={"voice_id": voice_id},
                files={"file": (reference_path.name, voice_file, "audio/wav")},
                timeout=60,
            )
        if getattr(response, "status_code", 200) not in {200, 201, 204, 409}:
            response.raise_for_status()
        self._uploaded_voice_ids.add(voice_id)

    def reference_audio_path(self, speaker: str) -> str:
        return SPEAKERS[speaker].reference_audio_path

    def voice_id_for_speaker(self, speaker: str) -> str:
        return Path(SPEAKERS[speaker].corpus_path).stem

    def _speech_payload(self, chunk: TTSChunk, voice_id: str) -> dict:
        payload = {
            "model": self.config.irodori_model,
            "input": chunk.tts_text,
            "voice": voice_id,
            "response_format": self.config.irodori_response_format,
            "speed": self.config.irodori_speed,
            "irodori": {
                "chunking_enabled": False,
            },
        }
        if self.config.irodori_use_ref_wav:
            payload["irodori"]["ref_wav"] = self.reference_audio_path(chunk.speaker)
        return payload

    def _url(self, path: str) -> str:
        return self.config.irodori_base_url.rstrip("/") + path

    def _headers(self) -> dict[str, str]:
        return {**self._auth_headers(), "Content-Type": "application/json"}

    def _auth_headers(self) -> dict[str, str]:
        if not self.config.irodori_api_key or self.config.irodori_api_key == "not-used":
            return {}
        return {"Authorization": f"Bearer {self.config.irodori_api_key}"}

def _write_silent_wav(path: Path, duration_seconds: float = 0.15, sample_rate: int = 16000) -> None:
    frames = int(duration_seconds * sample_rate)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b"\x00\x00" * frames)
