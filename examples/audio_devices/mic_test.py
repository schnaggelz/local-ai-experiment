#!/usr/bin/env python3
"""Mic test: rec cue, record, rec cue, replay.

Green-field test per PLAN.md. Sequence: double-beep -> record --seconds from
the mic -> double-beep -> replay the gain-adjusted recording. Device indices
are configurable (--in-device / --out-device); omit them to use the
PortAudio defaults.

Uses the snake_case PyAudio layout (verified: this repo's pyaudio exposes
get_device_count, not getDeviceCount).
"""

from __future__ import annotations

import argparse
import contextlib
import math
import os
import time
import wave
from array import array
from pathlib import Path
from typing import Iterator


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


@contextlib.contextmanager
def _pa_session(loud: bool) -> Iterator[object]:
    """Yield a PyAudio instance; stderr silenced unless --loud."""
    from pyaudio import PyAudio  # heavy dep: lazy import (python skill rule)

    with contextlib.ExitStack() as stack:
        if not loud:
            stack.enter_context(_silence_stderr())
        try:
            pa = PyAudio()
        except OSError as exc:
            raise SystemExit(f"PortAudio init failed (no sound card?): {exc}") from exc
        try:
            yield pa
        finally:
            pa.terminate()  # type: ignore[attr-defined]


def _kind_channels(info: dict[str, object], kind: str) -> int:
    """Input or output channel count of a PortAudio device info dict."""
    return int(info["maxInputChannels" if kind == "input" else "maxOutputChannels"])


def _pick(pa: object, wanted: int | None, kind: str) -> tuple[int, dict[str, object]]:
    """Resolve a device: --in-device/--out-device index, else PortAudio default.

    kind is "input" or "output". Exits with the available devices when the
    wanted index does not provide that direction.
    """
    default_attr = f"get_default_{kind}_device_info"
    found: dict[int, dict[str, object]] = {}
    for idx in range(int(pa.get_device_count())):  # type: ignore[attr-defined]
        info = pa.get_device_info_by_index(idx)  # type: ignore[attr-defined]
        if _kind_channels(info, kind) > 0:
            found[idx] = info
    if not found:
        raise SystemExit(f"no {kind} devices found")

    if wanted is not None:
        if wanted in found:
            return wanted, found[wanted]
        known = ", ".join(str(i) for i in found)
        raise SystemExit(f"device {wanted} has no {kind}. available: {known}")

    default_idx = -1
    try:
        default_idx = int(getattr(pa, default_attr)()["index"])  # type: ignore[attr-defined]
    except (KeyError, OverflowError, OSError):
        pass  # no default of this kind configured
    if default_idx in found:
        return default_idx, found[default_idx]
    idx = next(iter(found))
    print(f"no default {kind} device; using idx={idx} ({found[idx]['name']})")
    return idx, found[idx]


MARK_BEEP = 0.20       # s, each cue beep
MARK_GAP = 0.25        # s, gap between beeps within a group
MARK_GROUP_GAP = 1.0   # s, gap between groups (multi-group patterns)
LEAD_IN = 0.50         # s of silence queued before the content; device
                       # startup eats into THIS, never into the first beep
WARMUP = 0.10          # s settle after the lead write; LEAD_IN - WARMUP
                       # stays buffered, so the device never underruns
                       # (an underrun restart would eat the attack again)
IN_WARMUP = 0.50       # s of dummy input reads; consumes input startup lag
                       # so recorded samples align with the wall clock
DRAIN_SLACK = 0.30     # s added to the drain sleep; device buffer capacity
                       # must not influence when stop_stream() happens
CAPTURE_EARLY = 0.20   # s before the audible cue end that capture starts;
                       # PortAudio write returns ~0.09 s AFTER the audio
                       # played, so firing early keeps the first word intact
CHUNK_FRAMES = 1024    # frames per playback write


def _sine(freq_hz: float, seconds: float, volume: float, rate: int) -> array[int]:
    """Mono int16 sine samples, `seconds` long."""
    out = array("h")
    for i in range(int(rate * seconds)):
        out.append(int(volume * 32767.0 * math.sin(2.0 * math.pi * freq_hz * i / rate)))
    return out


def _zeros(rate: int, seconds: float) -> array[int]:
    """Mono int16 silence, `seconds` long."""
    return array("h", bytes(2 * int(rate * seconds)))


def _pattern_frames(freq_hz: float, volume: float, rate: int,
                    counts: tuple[int, ...]) -> array[int]:
    """Beep groups per `counts`: (2,) = rec cue (beep-beep), (1,2,3) = marker.

    Played before and after the recording: on replay, a missing or short
    group means that end was cut. Built as ONE buffer so it plays atomically.
    """
    beep = _sine(freq_hz, MARK_BEEP, volume, rate)
    intra = _zeros(rate, MARK_GAP)
    out = array("h")
    for n, count in enumerate(counts):
        for i in range(count):
            out.extend(beep)
            if i < count - 1:
                out.extend(intra)
        if n < len(counts) - 1:
            out.extend(_zeros(rate, MARK_GROUP_GAP))
    return out


def _play(pa: object, device: int, rate: int, frames: array[int],
          label: str, on_queued: object = None) -> None:
    """Play `frames` on `device`, then drain before stopping.

    `on_queued` (optional) fires when ~CAPTURE_EARLY s of content remains
    to write - i.e. shortly BEFORE the audible cue ends - so a caller can
    start recording at the cue's end without clipping the first word
    (PortAudio's blocking write returns ~0.09 s after the audio played).
    After an early-fired callback the drain sleep is skipped: the capture
    outlasted the playback, so the tail is already safe.

    Queue LEAD_IN of silence, settle briefly (LEAD_IN - WARMUP stays
    buffered -> no underrun), then queue the content behind the silence;
    the device startup eats into the silence, never into the first beep.
    The drain sleep (lead remainder + frames + slack) guarantees the tail
    is not cut by stop_stream() (PLAN design requirement).

    TODO: a faint residual crack can still occur right at the end of
    playback (cause unclear, suspected ALSA period alignment); deferred.
    """
    from pyaudio import paInt16  # heavy dep: lazy import (python skill rule)

    stream = pa.open(  # type: ignore[attr-defined]
        format=paInt16, channels=1, rate=rate, output=True,
        output_device_index=device)
    try:
        stream.write(  # type: ignore[attr-defined]
            _zeros(rate, LEAD_IN).tobytes(), int(rate * LEAD_IN))
        time.sleep(WARMUP)
        for start in range(0, len(frames), CHUNK_FRAMES):
            chunk = frames[start:start + CHUNK_FRAMES]
            # write the TRUE chunk length: claiming CHUNK_FRAMES for a short
            # final chunk makes PortAudio read past the buffer (garbage tail)
            if on_queued is not None and \
                    (len(frames) - start) <= int(rate * CAPTURE_EARLY):
                on_queued()  # start capture ~CAPTURE_EARLY s before cue end
                on_queued = None  # fire once
            stream.write(  # type: ignore[attr-defined]
                chunk.tobytes(), len(chunk))
        if on_queued is not None:
            # content shorter than CAPTURE_EARLY: fire late, then drain
            on_queued()
            time.sleep((LEAD_IN - WARMUP) + len(frames) / rate + DRAIN_SLACK)
        # else: capture callback already ran and outlasted playback; skip drain
    finally:
        stream.stop_stream()  # type: ignore[attr-defined]
        stream.close()  # type: ignore[attr-defined]
    print(label)


def _beeps(pa: object, device: int, rate: int, freq_hz: float, volume: float,
           counts: tuple[int, ...], on_queued: object = None) -> None:
    """Play a beep-group pattern on `device` (e.g. the rec double-beep)."""
    frames = _pattern_frames(freq_hz, volume, rate, counts)
    label = "beeps " + "-".join(str(c) for c in counts)
    _play(pa, device, rate, frames,
          f"{label} ({len(frames) / rate:.1f} s), drained",
          on_queued=on_queued)


def _replay(pa: object, device: int, rate: int, samples: array[int],
            gain: float) -> None:
    """Play the recording back at `gain`, clamped to the int16 range.

    Quiet mics need boost, so the default gain is > 1 (PLAN requirement);
    clamping prevents overflow instead of crashing array('h') appends.
    """
    out = array("h")
    for v in samples:
        x = int(v * gain)
        out.append(32767 if x > 32767 else -32768 if x < -32768 else x)
    _play(pa, device, rate, out,
          f"replay: {len(out) / rate:.1f} s at gain {gain:g}, drained")


def _rms_max(samples: array[int]) -> tuple[float, int]:
    """RMS and peak amplitude of int16 samples."""
    if not len(samples):
        return 0.0, 0
    peak = 0
    sumsq = 0.0
    for v in samples:
        av = v if v >= 0 else -v
        sumsq += float(av) * float(av)
        if av > peak:
            peak = av
    return math.sqrt(sumsq / len(samples)), peak


def _open_input(pa: object, device: int, rate: int) -> object:
    """Open the input stream and warm it (IN_WARMUP of discarded reads).

    PortAudio/ALSA input needs ~0.5-1 s after open before delivering
    samples; warming here makes the stream ready for capture. Call this
    BEFORE the rec cue so the device is primed when the cue ends.
    """
    from pyaudio import paInt16  # heavy dep: lazy import (python skill rule)

    stream = pa.open(  # type: ignore[attr-defined]
        format=paInt16, channels=1, rate=rate, input=True,
        input_device_index=device)
    warm_reads = int(rate * IN_WARMUP) // CHUNK_FRAMES
    for _ in range(warm_reads):  # discard: absorbs input startup lag
        stream.read(CHUNK_FRAMES, exception_on_overflow=False)  # type: ignore[attr-defined]
    return stream


def _read_input(stream: object, rate: int, seconds: int) -> array[int]:
    """Capture `seconds` of mono 16-bit from an OPEN, warmed stream.

    Prints RMS/max every 0.5 s so silence vs speech is visible in the log.
    The stream is left open (caller closes it).
    """
    total = rate * seconds
    half = rate // 2  # report every 0.5 s of recorded frames
    samples = array("h")
    window = array("h")
    next_report = half
    while len(samples) < total:
        data = stream.read(  # type: ignore[attr-defined]
            CHUNK_FRAMES, exception_on_overflow=False)
        chunk = array("h")
        chunk.frombytes(data)
        samples.extend(chunk)
        window.extend(chunk)
        if len(samples) >= next_report:
            rms, peak = _rms_max(window)
            t = len(samples) / rate
            print(f"rec: t={t:4.1f}s RMS={rms:6.0f} max={peak}")
            window = array("h")
            next_report += half
    return samples[:total]


def _record(pa: object, device: int, rate: int, seconds: int, sine_loop: bool,
            freq_hz: float, volume: float) -> array[int]:
    """Record `seconds` of mono 16-bit from `device` (open+warm+read).

    In --sine-loop mode, generate the tone instead (self-test: proves the
    beep/replay/save path without the microphone). The real-input branch
    is the simple open->read wrapper; core() uses _open_input directly so
    capture can start at the rec cue's end.
    """
    if sine_loop:
        samples = _sine(freq_hz, float(seconds), volume, rate)
        rms, peak = _rms_max(samples)
        print(f"sine-loop: generated {freq_hz:.0f} Hz, {seconds} s, "
              f"RMS={rms:.0f} max={peak}")
        return samples
    stream = _open_input(pa, device, rate)
    try:
        return _read_input(stream, rate, seconds)
    finally:
        stream.stop_stream()  # type: ignore[attr-defined]
        stream.close()  # type: ignore[attr-defined]


def _save(path: Path, rate: int, samples: array[int]) -> None:
    """Write the mono 16-bit capture as a WAV file (PLAN evidence).

    Prints the size check used in Phase 5: 44-byte header + 2 bytes/sample.
    """
    if path.suffix == "":
        path = path.with_suffix(".wav")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(samples.tobytes())
    expected = 44 + 2 * len(samples)
    print(f"saved: {path} ({path.stat().st_size} bytes; "
          f"expected {expected} = 44 + 2 x {len(samples)})")


def core(freq_hz: float, seconds: int, volume: float, gain: float, rate: int,
         in_device: int | None, out_device: int | None, sine_loop: bool,
         save_path: Path | None, loud: bool) -> None:
    """Rec cue, record `seconds`, end cue, replay. Sequential, no concurrency.

    The input stream is opened+warmed before the rec cue and capture starts
    the moment the cue's beeps are queued (see _open_input/_read_input), so
    the first spoken words are NOT cut - speak as the cue fades.
    """
    with _pa_session(loud) as pa:
        in_idx, in_info = _pick(pa, in_device, "input")
        out_idx, out_info = _pick(pa, out_device, "output")
        print(f"in : idx={in_idx} ch={_kind_channels(in_info, 'input')} "
              f"{in_info['name']}")
        print(f"out: idx={out_idx} ch={_kind_channels(out_info, 'output')} "
              f"{out_info['name']}")
        if sine_loop:
            samples = _record(pa, in_idx, rate, seconds, True,
                              freq_hz, volume)
            _beeps(pa, out_idx, rate, freq_hz, volume, (2,))  # rec cue
            _beeps(pa, out_idx, rate, freq_hz, volume, (2,))  # end cue
            _replay(pa, out_idx, rate, samples, gain)
        else:
            # Open+warm the input BEFORE the rec cue so the device is
            # primed; capture starts ~CAPTURE_EARLY s before the cue ends
            # (on_queued), so the first spoken words survive. The input
            # stream stays open through the end cue to avoid the
            # input-close -> output-open transition that swallowed output
            # on this USB card (end cue was inaudible). The drain after
            # the rec cue is skipped, so the end cue sounds promptly when
            # recording stops.
            in_stream = _open_input(pa, in_idx, rate)
            captured: dict[str, array[int]] = {}

            def start_capture() -> None:
                captured["samples"] = _read_input(in_stream, rate, seconds)

            _beeps(pa, out_idx, rate, freq_hz, volume, (2,),
                   on_queued=start_capture)  # rec cue; records while draining
            samples = captured["samples"]
            _beeps(pa, out_idx, rate, freq_hz, volume, (2,))  # end cue
            in_stream.stop_stream()  # type: ignore[attr-defined]
            in_stream.close()  # type: ignore[attr-defined]
            _replay(pa, out_idx, rate, samples, gain)
        if save_path is not None:
            _save(save_path, rate, samples)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Beep, record, beep, replay.")
    p.add_argument("--freq", type=float, default=440.0,
                   help="beep frequency in Hz (default: 440)")
    p.add_argument("--seconds", type=int, default=3,
                   help="recording duration in seconds (default: 3)")
    p.add_argument("--volume", type=float, default=0.3,
                   help="beep amplitude 0..1 (default: 0.3)")
    p.add_argument("--gain", type=float, default=10.0,
                   help="replay gain >0 applied to the recording (default: 10)")
    p.add_argument("--rate", type=int, default=48000,
                   help="sample rate in Hz (default: 48000)")
    p.add_argument("--in-device", type=int, default=None, metavar="IDX",
                   help="PortAudio input device index (default: system default)")
    p.add_argument("--out-device", type=int, default=None, metavar="IDX",
                   help="PortAudio output device index (default: system default)")
    p.add_argument("--sine-loop", action="store_true",
                   help="self-test: fill the recording with a generated tone "
                        "instead of the mic (proves replay without input)")
    p.add_argument("--save", type=Path, default=None, metavar="FILE",
                   help="write the raw mono 16-bit capture to FILE.wav")
    p.add_argument("--loud", action="store_true",
                   help="show raw ALSA/JACK backend probe warnings on stderr")
    return p.parse_args()


def main() -> None:
    a = parse_args()
    if a.freq <= 0 or a.rate <= 0:
        raise SystemExit("--freq and --rate must be positive")
    if a.seconds <= 0:
        raise SystemExit("--seconds must be positive")
    if a.gain <= 0:
        raise SystemExit("--gain must be positive")
    if not 0.0 <= a.volume <= 1.0:
        raise SystemExit("--volume must be in 0..1")
    core(a.freq, a.seconds, a.volume, a.gain, a.rate,
         a.in_device, a.out_device, a.sine_loop, a.save, a.loud)


if __name__ == "__main__":
    main()
