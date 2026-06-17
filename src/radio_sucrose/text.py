from __future__ import annotations

NOISE_LINES = (
    "現在JavaScriptが無効になっています",
    "Yahoo!ニュースのすべての機能を利用するためには、JavaScriptの設定を有効にしてください。",
    "JavaScriptの設定を変更する方法はこちら",
)


def clean_article_text(text: str) -> str:
    cleaned_lines: list[str] = []
    for line in text.splitlines():
        cleaned = line.strip()
        if not cleaned:
            continue
        for noise in NOISE_LINES:
            cleaned = cleaned.replace(noise, "").strip()
        if cleaned:
            cleaned_lines.append(cleaned)
    return "\n".join(cleaned_lines)


def truncate_by_paragraphs(body: str, max_chars: int = 1800) -> str:
    body = clean_article_text(body)
    paragraphs: list[str] = []
    total = 0
    for paragraph in body.splitlines():
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        next_total = total + len(paragraph) + (1 if paragraphs else 0)
        if next_total > max_chars:
            break
        paragraphs.append(paragraph)
        total = next_total
    return "\n".join(paragraphs)
