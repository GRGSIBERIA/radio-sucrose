from __future__ import annotations

from radio_sucrose.clients.vllm import fallback_segment_payload, parse_script_json
from radio_sucrose.validation import normalize_segment


def test_parse_script_json_accepts_fenced_json() -> None:
    parsed = parse_script_json(
        '''```json
{"segment_type":"news","chunks":[{"speaker":"A","speaker_name":"スクロース","tts_text":"📖本文です。","display_text":"本文です。"}]}
```'''
    )

    assert parsed is not None
    assert parsed["segment_type"] == "news"


def test_parse_script_json_extracts_first_balanced_object_after_preamble() -> None:
    parsed = parse_script_json(
        '少し説明します。{"segment_type":"news","chunks":[{"speaker":"A","speaker_name":"スクロース","tts_text":"📖本文です。","display_text":"本文です。"}]} 以上です。'
    )

    assert parsed is not None
    assert parsed["chunks"][0]["display_text"] == "本文です。"


def test_invalid_vllm_content_falls_back_to_valid_segment() -> None:
    raw = fallback_segment_payload(
        {
            "task_type": "news_segment",
            "news": {"title": "テストニュース"},
        },
        "",
    )

    segment = normalize_segment(raw)

    assert segment.segment_type == "news"
    assert segment.chunks[0].display_text
