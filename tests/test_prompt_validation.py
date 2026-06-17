from pathlib import Path

from radio_sucrose.emoji import ALLOWED_IRODORI_EMOJIS, emoji_markdown_table
from radio_sucrose.prompt import PromptBuilder
from radio_sucrose.validation import normalize_segment


def test_prompt_uses_system_for_fixed_role_and_user_for_dynamic_payload(tmp_path: Path) -> None:
    refs = tmp_path / "refs"
    refs.mkdir()
    (refs / "sucrose.txt").write_text("スクロースの固定セリフ", encoding="utf-8")
    (refs / "dori.txt").write_text("ドリーの固定セリフ", encoding="utf-8")
    builder = PromptBuilder(str(refs))

    payload_a = {"task_type": "news_segment", "news": {"title": "A", "body_excerpt": "本文A"}}
    payload_b = {"task_type": "news_segment", "news": {"title": "B", "body_excerpt": "本文B"}}
    messages_a = builder.build_messages(payload_a)
    messages_b = builder.build_messages(payload_b)

    assert [message["role"] for message in messages_a] == ["system", "user"]
    assert messages_a[0]["content"] == messages_b[0]["content"]
    assert "スクロースの固定セリフ" in messages_a[0]["content"]
    assert "# Irodori-TTS Emoji Annotation Table" in messages_a[0]["content"]
    assert "assistant must respond only with the formatted dialogue-script JSON" in messages_a[0]["content"]
    assert "本文A" not in messages_a[0]["content"]
    assert "本文A" in messages_a[1]["content"]
    assert "本文B" in messages_b[1]["content"]


def test_emoji_table_contains_all_allowed_emojis() -> None:
    table = emoji_markdown_table()
    for emoji in ALLOWED_IRODORI_EMOJIS:
        assert emoji in table


def test_normalize_segment_repairs_missing_emoji_and_uses_display_text() -> None:
    segment = normalize_segment(
        {
            "segment_type": "news",
            "chunks": [
                {
                    "speaker": "A",
                    "speaker_name": "スクロース",
                    "tts_text": "ニュースです。",
                    "display_text": "ニュースです。",
                }
            ],
        }
    )

    assert segment.chunks[0].tts_text.startswith("📖")
    assert segment.chunks[0].display_text == "ニュースです。"


def test_package_cli_help_imports_without_runtime_dependencies(capsys) -> None:
    import pytest

    from radio_sucrose.app import main

    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])

    assert exc_info.value.code == 0
    assert "Run radio-sucrose live loop" in capsys.readouterr().out


def test_clean_article_text_removes_yahoo_javascript_warning() -> None:
    from radio_sucrose.text import clean_article_text, truncate_by_paragraphs

    noisy = "現在JavaScriptが無効になっています\nYahoo!ニュースのすべての機能を利用するためには、JavaScriptの設定を有効にしてください。 JavaScriptの設定を変更する方法はこちら\n本文です。"

    assert clean_article_text(noisy) == "本文です。"
    assert truncate_by_paragraphs(noisy, max_chars=1) == "本文です。"
