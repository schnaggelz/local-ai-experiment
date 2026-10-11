#!/usr/bin/env python3
"""Capture spoken utterances from the mic and print their transcript.
Phase 3 (examples/asr/PLAN.md): mic -> WebRTC VAD endpointing -> whisper-base
on the Hailo NPU, all in one process. The HEF is loaded **once** and reused for
every utterance, which is what makes the per-utterance inference timing
meaningful. Records at 16 kHz mono int16 (the native Whisper rate), keeps a
pre-roll to save word starts, and ends the utterance on a silence timeout or a
max-duration cap.

Two modes:
- default: keep listening, transcribe every utterance (Ctrl-C to stop)
- `--once`: one synchronized round for testing - no keypress: it prints a
  `>>> SPEAK NOW <<<` banner and listens, the first voiced frame starts the
  recording, a longer stretch of silence ends it, `>>> STOP TALKING <<<`
  follows, then the transcript (exit code 0, or 1 when nothing was captured).
  `--wait` bounds how long it waits for your first word, so it cannot hang.

Use --no-npu for capture-only runs, `--language`/`--task`/`--hef` to control
recognition (language defaults to auto-detect; a wrong code is not a hint but a
hard instruction), or `transcribe_wav.py` to check a saved WAV offline.
"""

from __future__ import annotations

import argparse
import array
import contextlib
import math
import os
import sys
import time
import wave
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import numpy as np

SAMPLE_RATE = 16000
FRAME_DURATION_MS = 30           # WebRTC VAD accepts 10/20/30 ms
FRAME_SIZE = SAMPLE_RATE * FRAME_DURATION_MS // 1000
ONSET_FRAMES = 2                 # consecutive speech frames to trigger record
PRE_ROLL_FRAMES = 3              # frames kept before onset (save word starts)
SILENCE_TIMEOUT_FRAMES = int(1500 / FRAME_DURATION_MS)  # ~1.5 s ends utterance
MIN_SPEECH_FRAMES = 5            # discard utterances shorter than this
WARMUP_FRAMES = 2                # frames discarded after opening the stream
ENERGY_FLOOR = 0.004             # normalized RMS below this = forced silence
LOW_PEAK = 2000                  # peak below ~-24 dBFS = warn about mic gain
SHARED_VDEVICE_GROUP_ID = "SHARED"   # let several processes share the NPU
REPORT_EVERY = 0.5               # s between live RMS prints while recording


@contextlib.contextmanager
def _silence_stderr() -> Iterator[None]:
    """Point fd 2 at /dev/null briefly (PortAudio backend probing is chatty)."""
    old = os.dup(2)
    devnull = os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(devnull, 2)
        yield
    finally:
        os.dup2(old, 2)
        os.close(old)
        os.close(devnull)


def _frame_rms(frame: bytes) -> float:
    """Normalized RMS (0..1) of one int16 frame."""
    a = array.array("h")
    a.frombytes(frame)
    if not a:
        return 0.0
    sumsq = sum(v * v for v in a)
    return math.sqrt(sumsq / len(a)) / 32768.0


def _input_devices(pa: object) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    for idx in range(int(pa.get_device_count())):  # type: ignore[attr-defined]
        info = pa.get_device_info_by_index(idx)  # type: ignore[attr-defined]
        if int(info["maxInputChannels"]) > 0:
            out.append((idx, str(info["name"])))
    return out


def _supports_16k(pa: object, idx: int) -> bool:
    """Best-effort probe (UNRELIABLE: ALSA reports false negatives).

    Kept only for the --list-devices hint; never used to block a device.
    """
    import pyaudio  # heavy dep: lazy import

    try:
        return bool(pa.is_format_supported(  # type: ignore[attr-defined]
            SAMPLE_RATE, input_device=idx, input_channels=1,
            input_format=pyaudio.paInt16))
    except Exception:  # PortAudioError / ValueError / OSError
        return False


def _list_input_devices(pa: object) -> None:
    import pyaudio  # noqa: F401  (constants live at module level)

    for idx, name in _input_devices(pa):
        probe = "yes" if _supports_16k(pa, idx) else "no"
        print(f"idx={idx}: {name}  [{SAMPLE_RATE} Hz mono probe: {probe}]")
    print("note: indices/order can differ between runs (ALSA enumeration); "
          "the probe above can also be wrong - the real open() decides.")


def _pick_input(pa: object, wanted: int | None) -> int:
    """Resolve --in-device, else the PortAudio default input, else first."""
    if wanted is not None:
        return wanted
    try:
        return int(pa.get_default_input_device_info()["index"])  # type: ignore[attr-defined]
    except (KeyError, OverflowError, OSError):
        pass
    devs = _input_devices(pa)
    if not devs:
        raise SystemExit("no input device found")
    return devs[0][0]


def _open_stream(pa: object, device: int) -> object:
    import pyaudio  # heavy dep: lazy import

    return pa.open(  # type: ignore[attr-defined]
        format=pyaudio.paInt16, channels=1, rate=SAMPLE_RATE, input=True,
        input_device_index=device)


def open_input(pa: object, wanted: int | None) -> tuple[object, int]:
    """Open a 16 kHz mono input stream, falling back to other devices.

    Trusts a real open() attempt: raw ALSA hw devices often accept only their
    native rate (48 kHz for USB mics), the ALSA plug devices ('default',
    'sysdefault') resample for us, and probing for supported rates lies.
    """
    first = _pick_input(pa, wanted)
    order = [first] + [i for i, _ in _input_devices(pa) if i != first]
    errors: list[str] = []
    for rank, idx in enumerate(order):
        try:
            return _open_stream(pa, idx), idx
        except OSError as exc:
            errors.append(f"idx={idx}: {exc}")
            if rank == 0 and len(order) > 1:
                print(f"   device {idx} refused {SAMPLE_RATE} Hz mono - "
                      f"falling back to other inputs", flush=True)
    raise SystemExit(f"no input device could capture {SAMPLE_RATE} Hz mono:\n  "
                     + "\n  ".join(errors))


def _apply_gain(frames: list[bytes], gain: float) -> list[bytes]:
    """Multiply int16 samples by gain, clipping to full scale.

    The beyerdynamic SPACE mic (card 0) has no usable capture gain: its only
    control is already at 100%, peaking around -27 dBFS. A software gain makes
    such quiet far-field mics usable without touching system mixer state.
    """
    if gain == 1.0:
        return frames
    out: list[bytes] = []
    for fr in frames:
        a = array.array("h")
        a.frombytes(fr)
        for i, v in enumerate(a):
            s = int(v * gain)
            a[i] = 32767 if s > 32767 else (-32768 if s < -32768 else s)
        out.append(a.tobytes())
    return out


@dataclass(frozen=True)
class Options:
    """Capture-loop knobs (grouped so the loop signature stays readable)."""

    vad_mode: int = 2
    timeout: float = 10.0
    wait: float | None = 10.0     # --once: give up if no word arrives (None = forever)
    gain: float = 1.0
    language: str | None = None   # None = let whisper auto-detect the language
    task: str = "transcribe"       # "transcribe" | "translate" (translate -> English)
    save_raw: Path | None = None


@dataclass
class Asr:
    """whisper-base loaded on the NPU once, then reused per utterance."""

    vdevice: object
    pipeline: object


def load_asr(hef: Path) -> Asr:
    """Load the HEF on the Hailo device (heavy dep: lazy import).

    Loading costs seconds, so it happens once before the capture loop instead of
    per utterance; only one process can own the NPU at a time, hence the shared
    group id.
    """
    from hailo_platform import VDevice
    from hailo_platform.genai import Speech2Text

    print(f"loading {hef} on the Hailo NPU ...", flush=True)
    t0 = time.monotonic()
    params = VDevice.create_params()
    params.group_id = SHARED_VDEVICE_GROUP_ID
    vdevice = VDevice(params)
    pipeline = Speech2Text(vdevice, str(hef))
    print(f"NPU ready in {time.monotonic() - t0:.1f} s", flush=True)
    return Asr(vdevice=vdevice, pipeline=pipeline)


def _frames_to_audio(frames: list[bytes]) -> np.ndarray:
    """Concatenate int16 frames into float32 [-1, 1], RMS-normalized.

    Same normalization as transcribe_wav.py: quiet mic input is amplified to a
    consistent level, capped at 20x so near-silence is not blown up.
    """
    pcm = np.frombuffer(b"".join(frames), dtype=np.int16).astype(np.float32)
    audio = pcm / 32768.0
    rms = float(np.sqrt(np.mean(audio ** 2)))
    if rms > 1e-4:
        audio = np.clip(audio * min(0.1 / rms, 20.0), -1.0, 1.0)
    return audio.astype("<f4")


def _transcribe(asr: Asr, frames: list[bytes], language: str | None,
                task: str = "transcribe") -> str:
    """Run whisper on the NPU: encoder there, decoder on CPU.

    ``language`` is NOT a hint: whisper treats it as the actual language of the
    audio (a wrong code yields wrong-language words), so None is the safe
    default and lets the model detect it. With ``task='translate'`` it is the
    target language of the translation instead.
    """
    from hailo_platform.genai import Speech2TextTask

    mode = (Speech2TextTask.TRANSLATE if task == "translate"
            else Speech2TextTask.TRANSCRIBE)
    segments = asr.pipeline.generate_all_segments(  # type: ignore[attr-defined]
        audio_data=_frames_to_audio(frames),
        task=mode,
        language=language,
        timeout_ms=30000)
    return "".join(seg.text for seg in segments).strip()


def _save_raw(path: Path, frames: list[bytes]) -> None:
    """Write the captured int16 frames as a 16 kHz mono WAV."""
    if path.suffix == "":
        path = path.with_suffix(".wav")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        for fr in frames:
            w.writeframes(fr)
    print(f"saved: {path} ({path.stat().st_size} bytes)")


def _finish(asr: Asr | None, opts: Options, utterance: list[bytes],
            dur: float) -> None:
    """Apply gain, save, report the level, then transcribe on the NPU."""
    if opts.gain != 1.0:
        utterance = _apply_gain(utterance, opts.gain)
    if opts.save_raw is not None:
        _save_raw(opts.save_raw, utterance)
    rms, peak = _stats(utterance)
    db = 20 * math.log10(peak / 32768.0) if peak else -120.0
    print(f"utterance: {dur:.2f}s rms={rms:.0f} peak={peak} "
          f"({len(utterance) * FRAME_SIZE} samples, peak {db:.0f} dBFS)")
    if peak < LOW_PEAK:
        print("   ! very low input level - raise the mic gain "
              "(e.g. `amixer -c 0 controls | grep -i mic`), use "
              "another --in-device, or re-run with --gain 4")
    if asr is None:
        return
    t1 = time.monotonic()
    text = _transcribe(asr, utterance, opts.language, opts.task)
    dt = time.monotonic() - t1
    speed = f"{dur / dt:.1f}x realtime" if dt > 0 else "n/a"
    print(f"   npu: {dt:.2f} s for {dur:.2f} s audio ({speed})")
    print(f"TRANSCRIPT: {text or '(empty)'}")


def once(pa: object, wanted: int | None, opts: Options,
         asr: Asr | None) -> int:
    """One synchronized round; returns a process exit code.

    No keypress: prints "speak now", the first voiced frame starts recording, a
    longer stretch of silence ends it, then the transcript. opts.wait bounds
    the hunt for the first word.
    """
    import webrtcvad  # heavy dep: lazy import

    vad = webrtcvad.Vad(opts.vad_mode)
    stream, device = open_input(pa, wanted)
    try:
        for _ in range(WARMUP_FRAMES):
            stream.read(FRAME_SIZE, exception_on_overflow=False)  # type: ignore[attr-defined]
        silence_s = SILENCE_TIMEOUT_FRAMES * FRAME_DURATION_MS / 1000
        print(f"ready on device {device} ({SAMPLE_RATE} Hz mono, vad mode "
              f"{opts.vad_mode}, ends after {silence_s:.1f} s of silence)")
        print("=" * 52)
        print(">>> SPEAK NOW <<<  (recording starts on your first word)")
        print("=" * 52, flush=True)
        utterance, dur = _one_utterance(stream, vad, opts.timeout, opts.wait)
        if utterance is not None:
            print(">>> STOP TALKING <<<  (utterance complete, transcribing)",
                  flush=True)
    finally:
        stream.stop_stream()  # type: ignore[attr-defined]
        stream.close()  # type: ignore[attr-defined]
    if utterance is None:
        print("(no words captured - nothing to transcribe)")
        return 1
    _finish(asr, opts, utterance, dur)
    return 0


def capture(pa: object, wanted: int | None, opts: Options,
            asr: Asr | None) -> None:
    """VAD-endpoint utterances, transcribe each on the NPU; until Ctrl-C."""
    import webrtcvad  # heavy dep: lazy import

    vad = webrtcvad.Vad(opts.vad_mode)
    stream, device = open_input(pa, wanted)
    try:
        for _ in range(WARMUP_FRAMES):
            stream.read(FRAME_SIZE, exception_on_overflow=False)  # type: ignore[attr-defined]
        print(f"listening on device {device} @ {SAMPLE_RATE} Hz "
              f"(vad mode {opts.vad_mode}, silence timeout "
              f"{SILENCE_TIMEOUT_FRAMES * FRAME_DURATION_MS / 1000:.1f} s, "
              f"gain x{opts.gain:g}, "
              f"{'NPU' if asr else 'capture only'}) - Ctrl-C to stop")
        while True:
            utterance, dur = _one_utterance(stream, vad, opts.timeout)
            if utterance is None:
                continue  # too short (click), keep listening
            _finish(asr, opts, utterance, dur)
    finally:
        stream.stop_stream()  # type: ignore[attr-defined]
        stream.close()  # type: ignore[attr-defined]


def _stats(frames: list[bytes]) -> tuple[float, int]:
    peak = 0
    sumsq = 0.0
    total = 0
    for fr in frames:
        a = array.array("h")
        a.frombytes(fr)
        total += len(a)
        for v in a:
            av = v if v >= 0 else -v
            sumsq += av * av
            if av > peak:
                peak = av
    return math.sqrt(sumsq / total) if total else 0.0, peak


def _one_utterance(stream: object, vad: object, timeout: float,
                   wait: float | None = None) -> tuple[list[bytes] | None, float]:
    """Block until one utterance is captured; None if discarded as too short.

    State machine: idle (fill pre-roll, give up after `wait` s) -> recording
    (append, watch for trailing silence). `wait=None` waits for words forever.
    """
    pre_roll: deque[bytes] = deque(maxlen=PRE_ROLL_FRAMES)
    speech_streak = 0       # consecutive voiced frames while idle
    silent_streak = 0       # consecutive unvoiced frames while recording
    frames: list[bytes] = []
    t_idle = time.monotonic()
    t0 = time.monotonic()
    next_report = REPORT_EVERY
    while True:
        data = stream.read(FRAME_SIZE, exception_on_overflow=False)  # type: ignore[attr-defined]
        frame_rms = _frame_rms(data)
        voiced = bool(vad.is_speech(data, SAMPLE_RATE)) and frame_rms >= ENERGY_FLOOR

        if not frames:  # idle
            if wait is not None and time.monotonic() - t_idle >= wait:
                print(f"   (no words within {wait:g}s - giving up)")
                return None, 0.0
            pre_roll.append(data)
            if voiced:
                speech_streak += 1
                if speech_streak >= ONSET_FRAMES:
                    frames = list(pre_roll)  # pre-roll keeps the word start
                    print(">> speech start (pre-roll kept)")
                    t0 = time.monotonic()
                    next_report = REPORT_EVERY
            else:
                speech_streak = 0
            continue

        # recording
        frames.append(data)
        elapsed = time.monotonic() - t0
        if elapsed >= next_report:
            print(f"   rec {elapsed:4.1f}s rms={frame_rms * 32768:6.0f}")
            next_report += REPORT_EVERY
        # a pause between words must NOT end the utterance: only a long run
        # of consecutive unvoiced frames does (trailing silence)
        silent_streak = 0 if voiced else silent_streak + 1
        if silent_streak >= SILENCE_TIMEOUT_FRAMES:
            break  # ~1.5 s of trailing silence ends the utterance
        if elapsed >= timeout:
            print(f"   (reached {timeout:.0f}s cap)")
            break

    if len(frames) < MIN_SPEECH_FRAMES + ONSET_FRAMES:
        print("   (too short, discarded)")
        return None, 0.0
    dur = len(frames) * FRAME_DURATION_MS / 1000.0  # captured audio length
    return frames, dur


def main() -> None:
    import pyaudio  # heavy dep: lazy import

    # stream output line by line even when stdout is a file/pipe (nohup, tee)
    sys.stdout.reconfigure(line_buffering=True)
    p = argparse.ArgumentParser(
        description="Capture VAD-endpointed utterances and transcribe them "
                    "with whisper-base on the Hailo NPU.")
    p.add_argument("--hef", type=Path, default=Path("models/whisper-base.hef"),
                   help="whisper HEF for Hailo (default: models/whisper-base.hef)")
    p.add_argument("--language", default=None, metavar="CODE",
                   help="ISO-639-1 language code of the speech, e.g. de "
                        "(default: auto-detect; a wrong code makes whisper "
                        "decode in that language)")
    p.add_argument("--task", default="transcribe",
                   choices=["transcribe", "translate"],
                   help="transcribe in the spoken language, or translate "
                        "into English (default: transcribe)")
    p.add_argument("--no-npu", action="store_true",
                   help="capture only; do not load whisper on the NPU")
    p.add_argument("--in-device", type=int, default=None, metavar="IDX",
                   help="PortAudio input device index (default: system default)")
    p.add_argument("--list-devices", action="store_true",
                   help="list input devices and exit")
    p.add_argument("--vad-mode", type=int, default=2, choices=[0, 1, 2, 3],
                   help="WebRTC VAD aggressiveness 0..3 (default: 2)")
    p.add_argument("--timeout", type=float, default=10.0,
                   help="max utterance length in seconds (default: 10)")
    p.add_argument("--gain", type=float, default=1.0, metavar="X",
                   help="software gain on captured audio (default: 1.0; "
                        "try 4 for quiet far-field USB mics)")
    p.add_argument("--wait", type=float, default=10.0, metavar="S",
                   help="in --once mode, seconds to wait for the first word "
                        "(default: 10; 0 = wait forever)")
    p.add_argument("--once", action="store_true",
                   help="one synchronized round: banner says speak, transcript, "
                        "exit (no keypress needed)")
    p.add_argument("--save-raw", type=Path, default=None, metavar="FILE",
                   help="save each utterance to FILE.wav (16 kHz mono)")
    p.add_argument("--loud", action="store_true",
                   help="show PortAudio/ALSA probe warnings on stderr")
    args = p.parse_args()

    with _silence_stderr() if not args.loud else contextlib.nullcontext():
        pa = pyaudio.PyAudio()
    try:
        if args.list_devices:
            _list_input_devices(pa)
            return
        if not args.no_npu and not args.hef.exists():
            raise SystemExit(f"HEF not found: {args.hef}")
        opts = Options(vad_mode=args.vad_mode, timeout=args.timeout,
                       wait=args.wait if args.wait > 0 else None,
                       gain=args.gain, language=args.language,
                       task=args.task, save_raw=args.save_raw)
        asr = None if args.no_npu else load_asr(args.hef)
        if args.once:
            code = once(pa, args.in_device, opts, asr)
        else:
            capture(pa, args.in_device, opts, asr)
            code = 0
    finally:
        pa.terminate()
    if code:
        raise SystemExit(code)


if __name__ == "__main__":
    main()
