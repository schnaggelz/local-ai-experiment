#!/usr/bin/env python3
"""Transcribe a 16 kHz mono WAV with whisper-base on the Hailo NPU.

Phase 1 smoke test (examples/asr/PLAN.md): proves the Hailo genai
Speech2Text path loads the HEF and produces text, without any mic.
Whisper encoder runs on the NPU; the decoder runs on CPU.

The language code is a hard instruction, not a hint: passing a wrong one makes
whisper decode the audio in that language (German speech + `--language en` came
back as English-looking words). Default is auto-detect; `--task translate`
turns German speech into English text on purpose.
"""

from __future__ import annotations

import argparse
import logging
import time
import wave
from pathlib import Path

import numpy as np

log = logging.getLogger("asr.transcribe_wav")

SAMPLE_RATE = 16000


def _read_wav(path: Path) -> np.ndarray:
    """Load a 16 kHz mono WAV as float32 in [-1, 1], little-endian."""
    with wave.open(str(path), "rb") as w:
        rate = w.getframerate()
        ch = w.getnchannels()
        if rate != SAMPLE_RATE or ch != 1:
            raise SystemExit(
                f"need {SAMPLE_RATE} Hz mono WAV, got {rate} Hz / {ch} ch")
        frames = w.readframes(w.getnframes())
    audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    return audio.astype("<f4")


def _normalize(audio: np.ndarray) -> np.ndarray:
    """RMS normalize so quiet input is amplified consistently (cap 20x)."""
    rms = float(np.sqrt(np.mean(audio ** 2)))
    if rms > 1e-4:
        gain = min(0.1 / rms, 20.0)
        audio = np.clip(audio * gain, -1.0, 1.0)
    return audio


def transcribe(hef_path: Path, wav_path: Path, language: str | None,
               task: str = "transcribe") -> str:
    from hailo_platform import VDevice
    from hailo_platform.genai import Speech2Text, Speech2TextTask  # heavy dep

    audio = _normalize(_read_wav(wav_path))
    log.info("loading %s on Hailo device ...", hef_path)
    t0 = time.monotonic()
    vdevice = VDevice(VDevice.create_params())
    pipeline = Speech2Text(vdevice, str(hef_path))
    log.info("device + model ready in %.1f s", time.monotonic() - t0)

    mode = (Speech2TextTask.TRANSLATE if task == "translate"
            else Speech2TextTask.TRANSCRIBE)
    t1 = time.monotonic()
    segments = pipeline.generate_all_segments(
        audio_data=audio,
        task=mode,
        language=language,
        timeout_ms=30000)
    dt = time.monotonic() - t1
    log.info("inference: %.1f s for %.1f s of audio", dt,
             len(audio) / SAMPLE_RATE)
    return "".join(seg.text for seg in segments).strip()


def main() -> None:
    p = argparse.ArgumentParser(
        description="Transcribe a 16 kHz mono WAV on the Hailo NPU.")
    p.add_argument("wav", type=Path, metavar="WAV",
                   help="16 kHz mono WAV to transcribe")
    p.add_argument("--hef", type=Path, default=Path("models/whisper-base.hef"),
                   help="whisper HEF for Hailo "
                        "(default: models/whisper-base.hef)")
    p.add_argument("--language", default=None, metavar="CODE",
                   help="ISO-639-1 language code of the speech, e.g. de "
                        "(default: auto-detect; a wrong code makes whisper "
                        "decode in that language)")
    p.add_argument("--task", default="transcribe",
                   choices=["transcribe", "translate"],
                   help="transcribe in the spoken language, or translate "
                        "into English (default: transcribe)")
    p.add_argument("--loud", action="store_true",
                   help="show hailort backend logs on stderr")
    args = p.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.loud else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S")
    if not args.hef.exists():
        raise SystemExit(f"HEF not found: {args.hef}")
    text = transcribe(args.hef, args.wav, args.language, args.task)
    print(f"TRANSCRIPT: {text}")


if __name__ == "__main__":
    main()
