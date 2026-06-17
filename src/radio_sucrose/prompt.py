from __future__ import annotations

import json
from pathlib import Path

from .emoji import emoji_markdown_table
from .models import SPEAKERS

PROMPT_VERSION = "2026-06-16.001"

PROMPT_RULES = """
# Application Role
You are the script generator for a Japanese YouTube live radio application.

# Chat Role Contract
The system message fixes all long-lived behavior, character corpora, Irodori-TTS emoji rules, and JSON output schema.
The user message provides only the current task payload, such as news title, news body, Super Chat, comment, or idle-talk request.
The assistant must respond only with the formatted dialogue-script JSON. Do not add markdown fences, commentary, or extra text.

# Speaker Role Rules
Speaker A is スクロース, the radio personality and host. スクロース introduces news, summarizes facts, manages transitions, introduces listener letters, and closes segments.
Speaker B is ドリー, the guest. ドリー reacts, asks listener-style questions, expands idle talk, and gives guest commentary.

# Progression Rules
Do not interrupt a news segment for Super Chat. Queue Super Chats and treat them as listener letters after the current segment completes.

# News Segment Rules
A news segment is around 3 minutes and must be at most 3 minutes 30 seconds. Target 900-1200 Japanese characters and never exceed 1400 Japanese characters. Start with a summary, then add context, then add related natural small talk, then close.

# Idle Talk Rules
When no news or comments are available, generate idle talk around a three-level taxonomy: large_category, middle_category, small_category. Examples: 旅行・フランス・ノートルダム大聖堂, 食べ物・食材・馬鈴薯, 科学・気象・積乱雲.

# Irodori-TTS Chunk Rules
Every tts_text chunk must start with exactly one emoji from the Irodori-TTS emoji table. Use the emoji as voice expression, not decoration. Split when emotion changes. Prefer 50-80 Japanese characters per chunk.

# OBS Rules
Every chunk must include display_text. Only display_text is sent to OBS message_box. display_text should normally omit the Irodori-TTS control emoji.

# Output JSON Schema
Return only JSON in this shape:
{
  "segment_type": "news | superchat | idle_talk | comment",
  "target_duration_sec": 180,
  "max_duration_sec": 210,
  "summary_for_memory": "short segment summary",
  "topic": {"large_category": "", "middle_category": "", "small_category": ""},
  "chunks": [
    {"speaker": "A", "speaker_name": "スクロース", "tts_text": "📖...", "display_text": "..."}
  ]
}
""".strip()


def read_text_if_exists(path: Path) -> str:
    if not path.exists():
        return f"[missing local reference file: {path}]"
    return path.read_text(encoding="utf-8")


class PromptBuilder:
    def __init__(self, refs_dir: str = "./refs") -> None:
        self.refs_dir = Path(refs_dir)
        self._system_prompt: str | None = None

    def system_prompt(self) -> str:
        if self._system_prompt is None:
            sucrose = read_text_if_exists(self.refs_dir / "sucrose.txt")
            dori = read_text_if_exists(self.refs_dir / "dori.txt")
            self._system_prompt = "\n\n".join(
                [
                    f"# RADIO_SYSTEM_PROMPT_VERSION: {PROMPT_VERSION}",
                    "# Speaker Definitions",
                    json.dumps(
                        {
                            speaker: profile.__dict__
                            for speaker, profile in SPEAKERS.items()
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                    "# Sucrose Dialogue Corpus\n" + sucrose,
                    "# Dori Dialogue Corpus\n" + dori,
                    "# Irodori-TTS Emoji Annotation Table\n" + emoji_markdown_table(),
                    PROMPT_RULES,
                ]
            )
        return self._system_prompt

    def user_prompt(self, payload: dict) -> str:
        dynamic = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        return "\n".join(
            [
                "# Current User Request",
                "以下のJSON payloadだけを今回の入力として扱い、systemで固定されたルール通りにassistantの台本JSONを出力してください。",
                dynamic,
            ]
        )

    def build_messages(self, payload: dict) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": self.system_prompt()},
            {"role": "user", "content": self.user_prompt(payload)},
        ]

    def fixed_prefix(self) -> str:
        return self.system_prompt()

    def build(self, payload: dict) -> str:
        return f"{self.system_prompt()}\n\n{self.user_prompt(payload)}"
