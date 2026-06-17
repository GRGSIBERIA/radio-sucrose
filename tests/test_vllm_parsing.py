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


def test_parsed_json_with_empty_chunks_falls_back_to_valid_segment() -> None:
    raw = parse_script_json('{"segment_type":"news","chunks":[]}')
    assert raw == {"segment_type": "news", "chunks": []}

    from radio_sucrose.clients.vllm import fallback_segment_payload

    segment = normalize_segment(fallback_segment_payload({"task_type": "news_segment", "news": {"title": "空チャンク"}}, "{}"))
    assert segment.chunks


class _FakeMessage:
    content = '{"segment_type":"news","chunks":[]}'


class _FakeChoice:
    message = _FakeMessage()


class _FakeCompletions:
    def create(self, **kwargs):
        return type("Response", (), {"choices": [_FakeChoice()]})()


class _FakeChat:
    completions = _FakeCompletions()


class _FakeOpenAIClient:
    chat = _FakeChat()


class _FakePromptBuilder:
    def build_messages(self, payload):
        return [
            {"role": "system", "content": "system"},
            {"role": "user", "content": str(payload)},
        ]


def test_vllm_client_generate_segment_falls_back_when_chunks_are_empty() -> None:
    from radio_sucrose.clients.vllm import VLLMScriptClient

    client = VLLMScriptClient.__new__(VLLMScriptClient)
    client.client = _FakeOpenAIClient()
    client.prompt_builder = _FakePromptBuilder()
    client.config = type("Config", (), {"vllm_model": "fake"})()

    segment = client.generate_segment({"task_type": "news_segment", "news": {"title": "空チャンク"}})

    assert segment.segment_type == "news"
    assert segment.chunks
    assert "空チャンク" in segment.chunks[0].display_text


def test_news_fallback_uses_partial_article_body() -> None:
    raw = fallback_segment_payload(
        {
            "task_type": "news_segment",
            "news": {
                "title": "途中本文ニュース",
                "body": "第一段落です。\n第二段落も取得できています。",
            },
        },
        "",
    )

    segment = normalize_segment(raw)

    assert any("第一段落です" in chunk.display_text for chunk in segment.chunks)
    assert any("第二段落も取得" in chunk.display_text for chunk in segment.chunks)
