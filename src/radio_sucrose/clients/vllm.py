from __future__ import annotations

import json

from openai import OpenAI

from radio_sucrose.config import AppConfig
from radio_sucrose.prompt import PromptBuilder
from radio_sucrose.validation import normalize_segment
from radio_sucrose.models import Segment


class VLLMScriptClient:
    def __init__(self, config: AppConfig, prompt_builder: PromptBuilder) -> None:
        self.config = config
        self.prompt_builder = prompt_builder
        self.client = OpenAI(base_url=config.vllm_base_url, api_key=config.vllm_api_key)

    def generate_segment(self, payload: dict) -> Segment:
        response = self.client.chat.completions.create(
            model=self.config.vllm_model,
            messages=self.prompt_builder.build_messages(payload),
            temperature=0.7,
            max_tokens=3000,
        )
        content = response.choices[0].message.content or "{}"
        return normalize_segment(json.loads(content))

    def warmup(self) -> None:
        self.client.chat.completions.create(
            model=self.config.vllm_model,
            messages=self.prompt_builder.build_messages({"task_type": "warmup", "instruction": "OKとだけ返してください。"}),
            temperature=0.0,
            max_tokens=4,
        )
