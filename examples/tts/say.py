#!/usr/bin/env python3
"""Synthesize speech locally with Piper (CPU) and save it as a WAV.

Phase 1 (examples/tts/PLAN.md): the synth smoke test - text in, 16 kHz mono
WAV out, plus timing - so the engine is proven before any audio-device code
exists. Piper runs on the CPU; the Hailo NPU has no TTS op (genai 5.4.0 only
exposes LLM / Speech2Text / VLM).

Voices are language-specific model files in `models/tts/<voice>.onnx`
(+ a `.onnx.json` sidecar), so `--voice de_DE-thorsten-low` is how German is
selected. Fetch one with:
    python -m piper.download_voices --download-dir models/tts <voice>
"""

from __future__ import annotations

import argparse
import array
import contextlib
import os
import sys
import time
import wave
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

DEFAULT_VOICE_DIR = Path("models/tts")
DEFAULT_VOICE = "de_DE-thorsten-low"   # German, male, 16 kHz mono (see PLAN.md)
LEAD_IN_SECONDS = 0.75   # prime: this ALSA path eats the head of a fresh stream
                         # (measured: 0.5 s still clipped, 0.75 s clean -- see PLAN.md)
CHUNK_SECONDS = 0.02    # feed the device in small pieces; one huge write starves dmix (XRUN)


@dataclass(frozen=True)
class Speech:
    """One synthesized utterance: raw int16 PCM plus its sample rate."""

    pcm: bytes
    sample_rate: int

    @property
    def seconds(self) -> float:
        """Audio length; 2 bytes per mono int16 sample."""
        return len(self.pcm) / 2 / self.sample_rate


def resolve_voice(voice: str, voice_dir: Path) -> Path:
    """Accept a voice name or a path; return the .onnx model path."""
    model = Path(voice)
    if model.suffix != ".onnx":
        model = voice_dir / f"{voice}.onnx"
    if not model.exists():
        raise SystemExit(
            f"voice model not found: {model}\n"
            f"download it with: python -m piper.download_voices "
            f"--download-dir {voice_dir} {model.stem}")
    if not model.with_suffix(".onnx.json").exists():
        raise SystemExit(f"missing voice config: {model}.json")
    return model


def list_voices(voice_dir: Path) -> None:
    """Print the voices available locally (name, size, sidecar present)."""
    models = sorted(voice_dir.glob("*.onnx"))
    if not models:
        print(f"no voices in {voice_dir}")
        return
    for model in models:
        sidecar = "ok" if model.with_suffix(".onnx.json").exists() else "MISSING"
        print(f"{model.stem:24s} {model.stat().st_size / 1e6:6.1f} MB  json: {sidecar}")


def synthesize(text: str, model: Path,
               length_scale: float | None = None) -> Speech:
    """Run Piper on the CPU: text -> int16 PCM (heavy dep: lazy import)."""
    from piper import PiperVoice, SynthesisConfig

    t0 = time.monotonic()
    voice = PiperVoice.load(str(model))
    load_s = time.monotonic() - t0

    t1 = time.monotonic()
    chunks = list(voice.synthesize(text, SynthesisConfig(length_scale=length_scale)))
    synth_s = time.monotonic() - t1

    speech = Speech(pcm=b"".join(c.audio_int16_bytes for c in chunks),
                    sample_rate=voice.config.sample_rate)
    rtf = synth_s / speech.seconds if speech.seconds else 0.0
    print(f"load {load_s:.2f}s | synth {synth_s:.2f}s | audio "
          f"{speech.seconds:.2f}s | RTF {rtf:.2f}x", flush=True)
    return speech


def save_wav(path: Path, speech: Speech) -> None:
    """Write the PCM as a mono 16-bit WAV at the voice's own rate."""
    if path.suffix == "":
        path = path.with_suffix(".wav")
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(speech.sample_rate)
        w.writeframes(speech.pcm)
    print(f"wrote {path} ({speech.sample_rate} Hz mono, {speech.seconds:.2f} s, "
          f"{path.stat().st_size} bytes)")


@contextlib.contextmanager
def _silence_stderr() -> Iterator[None]:
    """Point fd 2 at /dev/null briefly (PortAudio ALSA probing is chatty)."""
    old = os.dup(2)
    devnull = os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(devnull, 2)
        yield
    finally:
        os.dup2(old, 2)
        os.close(old)
        os.close(devnull)


def _output_devices(pa: object) -> list[int]:
    """Indices of every device that can play something."""
    out: list[int] = []
    for idx in range(int(pa.get_device_count())):  # type: ignore[attr-defined]
        info = pa.get_device_info_by_index(idx)  # type: ignore[attr-defined]
        if int(info["maxOutputChannels"]) > 0:
            out.append(idx)
    return out


def _candidates(pa: object, requested: int | None) -> list[int | None]:
    """Devices to try in order; None means "let PortAudio pick".

    Requested first (so a refusal is visible), then the system default
    (`default` resamples any rate), then every other output, then None.
    """
    outputs = _output_devices(pa)
    if not outputs:
        raise SystemExit("no output devices found")
    try:
        default = int(pa.get_default_output_device_info()["index"])  # type: ignore[attr-defined]
    except (KeyError, OverflowError, OSError):
        default = None
    order: list[int | None] = ([] if requested is None else [requested]) \
        + [default, *outputs, None]
    return [idx for i, idx in enumerate(order)
            if idx not in order[:i]]


def _to_channels(pcm: bytes, channels: int) -> bytes:
    """Duplicate mono int16 PCM into `channels` interleaved channels.

    PortAudio's ALSA plug garbles a 1-channel stream on some multichannel
    devices; the sibling play_test_tone.py also opens 2 channels.
    """
    if channels == 1:
        return pcm
    mono = array.array("h")
    mono.frombytes(pcm)          # native endian = s16le on this box
    return array.array("h", [s for s in mono
                             for _ in range(channels)]).tobytes()


def _write_pcm(stream: object, pcm: bytes, chunk_bytes: int) -> None:
    """Write PCM to a blocking output stream in small, steady pieces.

    One single `stream.write()` of a whole utterance lets ALSA's dmix run dry
    mid-stream (a hole in the audio); blocked 20 ms chunks keep it fed.
    """
    for i in range(0, len(pcm), chunk_bytes):
        stream.write(pcm[i:i + chunk_bytes])  # type: ignore[attr-defined]


def play(speech: Speech, device_idx: int | None = None,
         loud: bool = False) -> bool:
    """Play int16 mono PCM at the voice's rate; first device that opens wins."""
    from pyaudio import PyAudio  # type: ignore[import-untyped]

    stack = contextlib.nullcontext() if loud else _silence_stderr()
    try:
        with stack:  # only the JACK/ALSA probe chatter is worth hiding
            pa = PyAudio()
    except OSError as exc:
        print(f"! play failed (PortAudio init): {exc}", file=sys.stderr)
        return False
    try:
        for idx in _candidates(pa, device_idx):
            if idx is None:
                dev = pa.get_default_output_device_info()  # type: ignore[attr-defined]
                name = f"default ({dev['name']})"
            else:
                dev = pa.get_device_info_by_index(idx)  # type: ignore[attr-defined]
                name = str(dev["name"])
            ch = min(2, max(1, int(dev["maxOutputChannels"])))
            try:
                stream = pa.open(format=pa.get_format_from_width(2),  # type: ignore[attr-defined]
                                 channels=ch, rate=speech.sample_rate,
                                 output=True, output_device_index=idx,
                                 start=False)
            except OSError as exc:
                if idx == device_idx:
                    print(f"! device {idx} refused {speech.sample_rate} Hz "
                          f"({exc}); trying others", file=sys.stderr)
                continue
            print(f"playing idx {idx} ({name}) @ {speech.sample_rate} Hz x{ch}, "
                  f"{speech.seconds:.2f}s", flush=True)
            try:
                stream.start_stream()
                # Silence first, so a dropped startup buffer eats the pad,
                # not the first phoneme.
                stream.write(b"\x00" * int(speech.sample_rate
                                           * LEAD_IN_SECONDS) * 2 * ch)
                _write_pcm(stream, _to_channels(speech.pcm, ch),
                           int(speech.sample_rate * CHUNK_SECONDS) * 2 * ch)
            finally:
                stream.stop_stream()
                stream.close()
            return True
        print("! play failed: no output device accepted "
              f"{speech.sample_rate} Hz mono", file=sys.stderr)
        return False
    finally:
        pa.terminate()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Synthesize text to speech locally with Piper (CPU).")
    p.add_argument("words", nargs="*", metavar="TEXT",
                   help="text to speak (quotes optional; --text also works)")
    p.add_argument("--text", default=None,
                   help="text to speak (alternative to the positional form)")
    p.add_argument("--voice", default=DEFAULT_VOICE,
                   help=f"voice name in --voice-dir or a .onnx path "
                        f"(default: {DEFAULT_VOICE})")
    p.add_argument("--voice-dir", type=Path, default=DEFAULT_VOICE_DIR,
                   help=f"directory holding the voice models "
                        f"(default: {DEFAULT_VOICE_DIR})")
    p.add_argument("--out", type=Path, default=None, metavar="FILE",
                   help="write the audio to FILE (default: do not save)")
    p.add_argument("--length-scale", type=float, default=None, metavar="X",
                   help="Piper speech speed: >1 slower, <1 faster "
                        "(default: the voice's own tempo)")
    p.add_argument("--list-voices", action="store_true",
                   help="list the voices in --voice-dir and exit")
    p.add_argument("--out-device", type=int, default=None, metavar="IDX",
                   help="PortAudio output device index (default: system default)")
    p.add_argument("--no-play", action="store_true",
                   help="synthesize only; do not play through the speaker")
    p.add_argument("--loud", action="store_true",
                   help="show raw ALSA/JACK backend probe warnings on stderr")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    if args.list_voices:
        list_voices(args.voice_dir)
        return
    text = args.text if args.text is not None else " ".join(args.words)
    if not text.strip():
        raise SystemExit("nothing to say: pass TEXT or --text "
                         "(or use --list-voices)")
    model = resolve_voice(args.voice, args.voice_dir)
    print(f"voice: {model.stem} | text: {text} | chars: {len(text)}", flush=True)
    speech = synthesize(text, model, args.length_scale)
    if args.out is not None:
        save_wav(args.out, speech)
    else:
        print("(not saved; pass --out FILE to write a WAV)")
    if args.no_play:
        return
    t0 = time.monotonic()
    played = play(speech, args.out_device, args.loud)
    wall = time.monotonic() - t0
    print(f"played in {wall:.2f}s wall" if played
          else f"playback skipped after {wall:.2f}s")
    if not played:
        raise SystemExit(1)


if __name__ == "__main__":
    sys.exit(main())