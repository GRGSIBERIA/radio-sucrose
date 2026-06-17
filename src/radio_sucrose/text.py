from __future__ import annotations


def truncate_by_paragraphs(body: str, max_chars: int = 1800) -> str:
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
