from __future__ import annotations

from typing import Any

from .emoji import ensure_initial_emoji, remove_initial_emoji
from .models import SPEAKERS, Segment, TTSChunk


def normalize_segment(raw: dict[str, Any]) -> Segment:
    chunks: list[TTSChunk] = []
    for item in raw.get("chunks", []):
        speaker = item.get("speaker")
        if speaker not in SPEAKERS:
            raise ValueError(f"unknown speaker: {speaker}")
        profile = SPEAKERS[speaker]
        tts_text = ensure_initial_emoji(str(item.get("tts_text", "")).strip())
        display_text = str(item.get("display_text") or remove_initial_emoji(tts_text)).strip()
        chunks.append(
            TTSChunk(
                speaker=speaker,
                speaker_name=profile.speaker_name,
                tts_text=tts_text,
                display_text=display_text,
            )
        )
    if not chunks:
        raise ValueError("segment has no chunks")
    return Segment(
        segment_type=raw.get("segment_type", "idle_talk"),
        target_duration_sec=raw.get("target_duration_sec"),
        max_duration_sec=raw.get("max_duration_sec"),
        summary_for_memory=raw.get("summary_for_memory", ""),
        topic=raw.get("topic") or {},
        chunks=chunks,
    )
