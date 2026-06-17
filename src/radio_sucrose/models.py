from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Literal

SpeakerId = Literal["A", "B"]
SegmentType = Literal["news", "superchat", "idle_talk", "comment"]


@dataclass(frozen=True)
class SpeakerProfile:
    speaker: SpeakerId
    speaker_name: str
    role: str
    corpus_path: str
    reference_audio_path: str


SPEAKERS: dict[SpeakerId, SpeakerProfile] = {
    "A": SpeakerProfile(
        speaker="A",
        speaker_name="スクロース",
        role="radio_personality",
        corpus_path="./refs/sucrose.txt",
        reference_audio_path="./refs/sucrose.wav",
    ),
    "B": SpeakerProfile(
        speaker="B",
        speaker_name="ドリー",
        role="guest",
        corpus_path="./refs/dori.txt",
        reference_audio_path="./refs/dori.wav",
    ),
}


@dataclass(frozen=True)
class TTSChunk:
    speaker: SpeakerId
    speaker_name: str
    tts_text: str
    display_text: str


@dataclass(frozen=True)
class Segment:
    segment_type: SegmentType
    chunks: list[TTSChunk]
    target_duration_sec: int | None = None
    max_duration_sec: int | None = None
    summary_for_memory: str = ""
    topic: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class RSSItem:
    title: str
    link: str
    pub_date: str | None = None


@dataclass(frozen=True)
class NewsArticle:
    url: str
    title: str
    category: str
    source: str = "Yahoo!ニュース"
    body: str = ""
    full_article_url: str | None = None
    canonical_url: str | None = None
    published_at: str | None = None
    discovered_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass(frozen=True)
class SuperChatMessage:
    author: str
    message: str
    amount_text: str | None = None
    amount_micros: int | None = None
    currency: str | None = None
    received_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class RadioEventType(str, Enum):
    NEWS = "news"
    SUPERCHAT = "superchat"
    COMMENT = "comment"
    IDLE_TALK = "idle_talk"


@dataclass(order=True)
class RadioEvent:
    sort_key: tuple[int, float]
    event_type: RadioEventType = field(compare=False)
    payload: dict = field(compare=False)
    created_at: float = field(compare=False, default=0.0)
