from __future__ import annotations

import subprocess
import time
from concurrent.futures import ThreadPoolExecutor

from radio_sucrose.clients.obs import OBSMessageBox
from radio_sucrose.clients.tts import IrodoriTTSClient
from radio_sucrose.config import AppConfig
from radio_sucrose.models import Segment, TTSChunk


class AudioPlayer:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def play(self, audio_path: str) -> None:
        if self.config.dry_run:
            print(f"[AUDIO] {audio_path}")
            return
        subprocess.run(["ffplay", "-nodisp", "-autoexit", "-loglevel", "error", audio_path], check=False)


class SegmentPlayer:
    def __init__(self, tts: IrodoriTTSClient, obs: OBSMessageBox, audio: AudioPlayer) -> None:
        self.tts = tts
        self.obs = obs
        self.audio = audio

    def play_segment(self, segment: Segment) -> None:
        chunks = segment.chunks
        if not chunks:
            return
        previous_speaker: str | None = None
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self.tts.synthesize, chunks[0])
            for index, chunk in enumerate(chunks):
                audio_path = future.result()
                if index + 1 < len(chunks):
                    future = executor.submit(self.tts.synthesize, chunks[index + 1])
                if self.audio.config.log_spoken_text:
                    print(f"[SCRIPT] {chunk.speaker_name}: {chunk.display_text}")
                self.obs.set_text(chunk.display_text)
                self.audio.play(audio_path)
                speaker_changed = previous_speaker is not None and previous_speaker != chunk.speaker
                segment_end = index == len(chunks) - 1
                time.sleep(natural_pause_after(chunk, speaker_changed, segment_end))
                previous_speaker = chunk.speaker
        self.obs.set_text("")


def natural_pause_after(chunk: TTSChunk, speaker_changed: bool, segment_end: bool) -> float:
    pause = 0.0
    if chunk.tts_text.endswith("。"):
        pause += 0.25
    elif chunk.tts_text.endswith("、"):
        pause += 0.12
    if speaker_changed:
        pause += 0.15
    if segment_end:
        pause += 0.60
    return pause
