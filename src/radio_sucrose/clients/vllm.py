from __future__ import annotations

import json
from json import JSONDecodeError


from radio_sucrose.config import AppConfig
from radio_sucrose.models import Segment
from radio_sucrose.prompt import PromptBuilder
from radio_sucrose.validation import normalize_segment


class VLLMScriptClient:
    def __init__(self, config: AppConfig, prompt_builder: PromptBuilder) -> None:
        self.config = config
        self.prompt_builder = prompt_builder
        from openai import OpenAI

        self.client = OpenAI(base_url=config.vllm_base_url, api_key=config.vllm_api_key)

    def generate_segment(self, payload: dict) -> Segment:
        response = self.client.chat.completions.create(
            model=self.config.vllm_model,
            messages=self.prompt_builder.build_messages(payload),
            temperature=0.7,
            max_tokens=3000,
        )
        content = response.choices[0].message.content or ""
        raw = parse_script_json(content)
        if raw is None:
            raw = fallback_segment_payload(payload, content)
        try:
            return normalize_segment(raw)
        except ValueError:
            return normalize_segment(fallback_segment_payload(payload, content))

    def warmup(self) -> None:
        self.client.chat.completions.create(
            model=self.config.vllm_model,
            messages=self.prompt_builder.build_messages({"task_type": "warmup", "instruction": "OKとだけ返してください。"}),
            temperature=0.0,
            max_tokens=4,
        )


def parse_script_json(content: str) -> dict | None:
    stripped = content.strip()
    if not stripped:
        return None

    candidates = [stripped]
    fenced = _extract_fenced_json(stripped)
    if fenced is not None:
        candidates.insert(0, fenced)

    balanced = _extract_first_balanced_json_object(stripped)
    if balanced is not None:
        candidates.append(balanced)

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def fallback_segment_payload(payload: dict, content: str) -> dict:
    preview = content.strip().replace("\n", " ")[:120] or "vLLMから空の応答が返りました"
    if payload.get("task_type") == "news_segment":
        news = payload.get("news", {})
        title = news.get("title", "ニュース")
        body_preview = _news_body_preview(news)
        return {
            "segment_type": "news",
            "summary_for_memory": f"fallback: {title}",
            "chunks": [
                {
                    "speaker": "A",
                    "speaker_name": "スクロース",
                    "tts_text": f"📖{title}についてお伝えします。台本生成が不安定だったため、分かっている内容を短く整理します。",
                    "display_text": f"{title}についてお伝えします。台本生成が不安定だったため、分かっている内容を短く整理します。",
                },
                {
                    "speaker": "A",
                    "speaker_name": "スクロース",
                    "tts_text": f"📖記事によると、{body_preview}",
                    "display_text": f"記事によると、{body_preview}",
                },
            ],
        }
    return {
        "segment_type": "idle_talk",
        "summary_for_memory": "fallback for invalid vLLM output",
        "chunks": [
            {
                "speaker": "A",
                "speaker_name": "スクロース",
                "tts_text": f"😟台本生成の形式が少し崩れました。内容の一部は、{preview}、です。",
                "display_text": f"台本生成の形式が少し崩れました。内容の一部は、{preview}、です。",
            }
        ],
    }


def _news_body_preview(news: dict) -> str:
    body = str(news.get("body") or news.get("body_excerpt") or "本文情報は取得できていません。")
    body = " ".join(part.strip() for part in body.splitlines() if part.strip())
    return body[:180] + ("。" if not body[:180].endswith("。") else "")


def _extract_fenced_json(content: str) -> str | None:
    fence_start = content.find("```")
    if fence_start == -1:
        return None
    after_start = content.find("\n", fence_start)
    if after_start == -1:
        return None
    fence_end = content.find("```", after_start + 1)
    if fence_end == -1:
        return None
    return content[after_start + 1 : fence_end].strip()


def _extract_first_balanced_json_object(content: str) -> str | None:
    start = content.find("{")
    if start == -1:
        return None
    depth = 0
    in_string = False
    escape = False
    for index in range(start, len(content)):
        char = content[index]
        if escape:
            escape = False
            continue
        if char == "\\":
            escape = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return content[start : index + 1]
    return None
