from __future__ import annotations

from radio_sucrose.models import Segment
from radio_sucrose.validation import normalize_segment


class DryRunScriptClient:
    def generate_segment(self, payload: dict) -> Segment:
        if payload.get("task_type") == "news_segment":
            title = payload["news"]["title"]
            raw = {
                "segment_type": "news",
                "target_duration_sec": 180,
                "max_duration_sec": 210,
                "summary_for_memory": title,
                "chunks": [
                    {
                        "speaker": "A",
                        "speaker_name": "スクロース",
                        "tts_text": f"📖続いては、{title}、というニュースです。",
                        "display_text": f"続いては、{title}、というニュースです。",
                    },
                    {
                        "speaker": "B",
                        "speaker_name": "ドリー",
                        "tts_text": "🤔これは気になりますね。少し背景も知りたいところです。",
                        "display_text": "これは気になりますね。少し背景も知りたいところです。",
                    },
                ],
            }
        elif payload.get("task_type") == "superchat_segment":
            superchat = payload["superchat"]
            author = superchat.get("author") or "匿名"
            message = superchat.get("message") or ""
            amount_text = superchat.get("amount_text")
            thanks = "スーパーチャットもいただきました。ありがとうございます。" if amount_text else "お便りありがとうございます。"
            raw = {
                "segment_type": "superchat",
                "target_duration_sec": 60,
                "summary_for_memory": f"{author}さんからのお便り。",
                "chunks": [
                    {
                        "speaker": "A",
                        "speaker_name": "スクロース",
                        "tts_text": f"📖ここで、ラジオネーム{author}さんからお便りが届いております。",
                        "display_text": f"ここで、ラジオネーム{author}さんからお便りが届いております。",
                    },
                    {
                        "speaker": "A",
                        "speaker_name": "スクロース",
                        "tts_text": f"🙏{thanks}",
                        "display_text": thanks,
                    },
                    {
                        "speaker": "B",
                        "speaker_name": "ドリー",
                        "tts_text": f"🤔ご相談は、{message}、という内容ですね。",
                        "display_text": f"ご相談は、{message}、という内容ですね。",
                    },
                    {
                        "speaker": "A",
                        "speaker_name": "スクロース",
                        "tts_text": "🫶すぐに断定せず、状況を分けて一緒に考えていきましょう。",
                        "display_text": "すぐに断定せず、状況を分けて一緒に考えていきましょう。",
                    },
                ],
            }
        else:
            raw = {
                "segment_type": "idle_talk",
                "target_duration_sec": 120,
                "summary_for_memory": "食べ物・食材・馬鈴薯の雑談。",
                "topic": {"large_category": "食べ物", "middle_category": "食材", "small_category": "馬鈴薯"},
                "chunks": [
                    {
                        "speaker": "A",
                        "speaker_name": "スクロース",
                        "tts_text": "📖ニュースが落ち着いているので、少し雑談を挟みましょう。",
                        "display_text": "ニュースが落ち着いているので、少し雑談を挟みましょう。",
                    },
                    {
                        "speaker": "B",
                        "speaker_name": "ドリー",
                        "tts_text": "😊今日は馬鈴薯の話なんてどうでしょう。料理の幅が広い食材ですよね。",
                        "display_text": "今日は馬鈴薯の話なんてどうでしょう。料理の幅が広い食材ですよね。",
                    },
                ],
            }
        return normalize_segment(raw)

    def warmup(self) -> None:
        print("[DRY-RUN] skip vLLM warmup")
