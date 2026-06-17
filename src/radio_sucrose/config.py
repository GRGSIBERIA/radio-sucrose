from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class AppConfig:
    database_path: str = "radio_sucrose.sqlite3"
    refs_dir: str = "./refs"
    vllm_base_url: str = "http://localhost:8000/v1"
    vllm_api_key: str = "dummy"
    vllm_model: str = "nvidia/Qwen3.6-35B-A3B-NVFP4"
    obs_host: str = "localhost"
    obs_port: int = 4455
    obs_password: str = ""
    obs_message_source: str = "message_box"
    obs_required: bool = False
    loop_sleep_seconds: float = 5.0
    rss_poll_seconds: float = 60.0
    dry_run: bool = False
    dry_run_superchat_message: str = ""
    dry_run_superchat_author: str = "テストリスナー"
    dry_run_superchat_amount: str = "￥500"
    irodori_base_url: str = "http://localhost:8088/v1"
    irodori_api_key: str = "not-used"
    irodori_model: str = "irodori-tts"
    irodori_response_format: str = "wav"
    irodori_speed: float = 1.0
    irodori_upload_voices: bool = True
    irodori_use_ref_wav: bool = False

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            database_path=os.getenv("RADIO_DB", cls.database_path),
            refs_dir=os.getenv("RADIO_REFS_DIR", cls.refs_dir),
            vllm_base_url=os.getenv("VLLM_BASE_URL", cls.vllm_base_url),
            vllm_api_key=os.getenv("VLLM_API_KEY", cls.vllm_api_key),
            vllm_model=os.getenv("VLLM_MODEL", cls.vllm_model),
            obs_host=os.getenv("OBS_HOST", cls.obs_host),
            obs_port=int(os.getenv("OBS_PORT", str(cls.obs_port))),
            obs_password=os.getenv("OBS_PASSWORD", cls.obs_password),
            obs_message_source=os.getenv("OBS_MESSAGE_SOURCE", cls.obs_message_source),
            obs_required=os.getenv("OBS_REQUIRED", "0") in {"1", "true", "TRUE", "yes"},
            loop_sleep_seconds=float(os.getenv("RADIO_LOOP_SLEEP_SECONDS", str(cls.loop_sleep_seconds))),
            rss_poll_seconds=float(os.getenv("RADIO_RSS_POLL_SECONDS", str(cls.rss_poll_seconds))),
            dry_run=os.getenv("RADIO_DRY_RUN", "0") in {"1", "true", "TRUE", "yes"},
            dry_run_superchat_message=os.getenv("RADIO_DRY_RUN_SUPERCHAT_MESSAGE", ""),
            dry_run_superchat_author=os.getenv("RADIO_DRY_RUN_SUPERCHAT_AUTHOR", cls.dry_run_superchat_author),
            dry_run_superchat_amount=os.getenv("RADIO_DRY_RUN_SUPERCHAT_AMOUNT", cls.dry_run_superchat_amount),
            irodori_base_url=os.getenv("IRODORI_BASE_URL", cls.irodori_base_url),
            irodori_api_key=os.getenv("IRODORI_API_KEY", cls.irodori_api_key),
            irodori_model=os.getenv("IRODORI_MODEL", cls.irodori_model),
            irodori_response_format=os.getenv("IRODORI_RESPONSE_FORMAT", cls.irodori_response_format),
            irodori_speed=float(os.getenv("IRODORI_SPEED", str(cls.irodori_speed))),
            irodori_upload_voices=os.getenv("IRODORI_UPLOAD_VOICES", "1") in {"1", "true", "TRUE", "yes"},
            irodori_use_ref_wav=os.getenv("IRODORI_USE_REF_WAV", "0") in {"1", "true", "TRUE", "yes"},
        )
