#!/usr/bin/env python3
"""Play a sine test tone: left channel first, then right.

Uses the modern snake_case PyAudio layout (pyaudio >= 0.2.16 in this repo's venv).
"""

from __future__ import annotations

import argparse
import contextlib
import math
import os


@contextlib.contextmanager
def _silence_stderr() -> None:
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


def _sine_block(freq_hz: float, rate: int, seconds: int,
                volume: float, pan: int | None) -> bytes:
    """Stereo 16-bit LE PCM; `pan` 0 = left, 1 = right, None = both channels."""
    n = int(rate * max(seconds, 0))
    step = 2.0 * math.pi * freq_hz / rate
    samples: list[int] = []
    amp = max(0.0, min(1.0, volume)) * 32767.0
    for i in range(n):
        v = int(math.sin(i * step) * amp)
        if pan == 0:
            samples += (v, 0)
        elif pan == 1:
            samples += (0, v)
        else:
            samples += (v, v)
    return b"".join(s.to_bytes(2, "little", signed=True) for s in samples)


def core(freq_hz: float, seconds: int, volume: float, rate: int,
         device_idx: int | None, loud: bool) -> None:
    """Enumerate outputs, pick device, stream tone in L then R."""
    from pyaudio import PyAudio  # type: ignore[import-untyped,no-redef]

    stack = contextlib.ExitStack()
    if not loud:
        stack.enter_context(_silence_stderr())
    with stack:
        try:
            pa = PyAudio()
        except OSError as exc:
            raise SystemExit(f"PortAudio init failed (no sound card?): {exc}") from exc
        try:
            outputs = []
            for idx in range(int(pa.get_device_count())):  # type: ignore[attr-defined]
                info = pa.get_device_info_by_index(idx)  # type: ignore[attr-defined]
                max_out = int(info["maxOutputChannels"])
                if max_out > 0:
                    outputs.append((idx, str(info["name"]), max_out))

            if not outputs:
                raise SystemExit("no output devices found")

            default_out = -1
            try:
                default_out = int(pa.get_default_output_device_info()["index"])  # type: ignore[attr-defined]
            except (KeyError, OverflowError, OSError):
                pass

            if device_idx is None:
                device_idx = default_out if default_out >= 0 else outputs[0][0]
                picked = next((d for d in outputs if d[0] == device_idx), None)
                print(f"using default output device idx={device_idx}"
                      + (f" ({picked[1]}, out={picked[2]})" if picked else ""))
            elif not any(d[0] == device_idx for d in outputs):
                known = ", ".join(str(i) for i, _, _ in outputs)
                raise SystemExit(f"device {device_idx} has no output. available: {known}")

            info = pa.get_device_info_by_index(device_idx)  # type: ignore[attr-defined]
            ch = min(2, int(info["maxOutputChannels"]))  # stereo when device allows

            try:
                stream = pa.open(format=pa.get_format_from_width(2),  # type: ignore[attr-defined]
                                 channels=ch, rate=rate, output=True,
                                 output_device_index=device_idx)
            except OSError as exc:
                raise SystemExit(f"open stream on device {device_idx} "
                                  f"@ {rate} Hz x{ch}: {exc}") from exc
            try:
                for pan, label in ((0, "LEFT"), (1, "RIGHT")):
                    # mono devices: tone goes to the single channel, both passes
                    tone = 0 if ch == 1 else pan
                    print(f"[{label}] {freq_hz:.0f} Hz {seconds}s")
                    stream.write(_sine_block(freq_hz, rate, seconds, volume, tone))
            finally:
                stream.stop_stream()
                stream.close()
        finally:
            pa.terminate()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Play a sine tone: left then right.")
    p.add_argument("--freq", type=float, default=440.0,
                   help="tone frequency in Hz (default: 440)")
    p.add_argument("--seconds", type=int, default=1,
                   help="duration of each channel pass in seconds (default: 1)")
    p.add_argument("--volume", type=float, default=0.3,
                   help="amplitude 0..1 (default: 0.3)")
    p.add_argument("--rate", type=int, default=48000,
                   help="sample rate in Hz (default: 48000)")
    p.add_argument("--device", type=int, default=None, metavar="IDX",
                   help="PortAudio output device index (default: system default)")
    p.add_argument("--loud", action="store_true",
                   help="show raw ALSA/JACK backend probe warnings on stderr")
    return p.parse_args()


def main() -> None:
    a = parse_args()
    if a.freq <= 0 or a.rate <= 0:
        raise SystemExit("--freq and --rate must be positive")
    if a.seconds <= 0:
        raise SystemExit("--seconds must be positive")
    core(a.freq, a.seconds, a.volume, a.rate, a.device, a.loud)


if __name__ == "__main__":
    main()
