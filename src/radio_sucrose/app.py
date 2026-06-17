from __future__ import annotations

import argparse

from radio_sucrose.config import AppConfig


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run radio-sucrose live loop.")
    parser.add_argument("--once", action="store_true", help="Run one loop iteration and exit.")
    parser.add_argument("--dry-run", action="store_true", help="Use fake vLLM/TTS/OBS outputs.")
    args = parser.parse_args(argv)

    config = AppConfig.from_env()
    if args.dry_run:
        config = AppConfig(**{**config.__dict__, "dry_run": True})

    from radio_sucrose.runtime.loop import build_radio_loop

    loop = build_radio_loop(config)
    if args.once:
        loop.run_once()
    else:
        loop.run_forever()


if __name__ == "__main__":
    main()
