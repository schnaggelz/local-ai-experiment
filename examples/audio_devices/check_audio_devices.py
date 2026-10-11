#!/usr/bin/env python3
"""List PortAudio audio input and output devices.

Supports both PyAudio layouts:
- new (>= 0.2.16): module ``pyaudio``, snake_case calls, dict device info
- classic:        module ``PyAudio``, camelCase calls, struct device info
"""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import json
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DeviceRecord:
    """One PortAudio device (input, output, or both)."""

    index: int
    kinds: tuple[str, ...]  # non-empty subset of ("input", "output")
    name: str
    default_sample_rate: float
    max_input_channels: int
    max_output_channels: int
    is_default: bool


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


def _records_new(pa: object) -> list[DeviceRecord]:
    """Modern snake_case API; device info is a dict."""
    default_in = default_out = -1
    try:
        default_in = int(pa.get_default_input_device_info()["index"])  # type: ignore[attr-defined]
    except (KeyError, OverflowError, OSError):  # no default input device
        pass
    try:
        default_out = int(pa.get_default_output_device_info()["index"])  # type: ignore[attr-defined]
    except (KeyError, OverflowError, OSError):  # no default output device
        pass
    records: list[DeviceRecord] = []
    for idx in range(int(pa.get_device_count())):  # type: ignore[attr-defined]
        info = pa.get_device_info_by_index(idx)  # type: ignore[attr-defined]
        max_in, max_out = int(info["maxInputChannels"]), int(info["maxOutputChannels"])
        if max_in <= 0 and max_out <= 0:
            continue
        rate = float(info["defaultSampleRate"])
        records.append(
            DeviceRecord(idx, ("input",) * (max_in > 0) + ("output",) * (max_out > 0),
                         str(info["name"]), rate if rate > 0 else 0.0, max_in, max_out,
                         idx == default_in or idx == default_out)
        )
    return records


def _records_classic(pa: object) -> list[DeviceRecord]:
    """Classic camelCase API; device info is a struct-like object."""
    records: list[DeviceRecord] = []
    count = pa.getDeviceCount()  # type: ignore[attr-defined]
    for idx in range(int(count)):
        info = pa.getDeviceInfoByIndex(idx)  # type: ignore[attr-defined]
        max_in, max_out = int(info.maxInputChannels), int(info.maxOutputChannels)
        if max_in <= 0 and max_out <= 0:
            continue
        is_default = bool(pa.isDefaultInputDevice(idx)) or bool(  # type: ignore[attr-defined]
            pa.isDefaultOutputDevice(idx)  # type: ignore[attr-defined]
        )
        records.append(
            DeviceRecord(idx, ("input",) * (max_in > 0) + ("output",) * (max_out > 0),
                         str(info.name), float(info.defaultSampleRate), max_in, max_out,
                         is_default)
        )
    return records


def core(as_json: bool, loud: bool) -> None:
    """Enumerate audio devices, print as table or JSON."""
    try:  # new release renamed module to lowercase
        from pyaudio import PyAudio
    except ModuleNotFoundError:
        from PyAudio import PyAudio  # classic layout

    stack = contextlib.ExitStack()
    if not loud:
        stack.enter_context(_silence_stderr())
    with stack:  # always restore stderr before printing
        try:
            pa = PyAudio()
        except OSError as exc:
            raise SystemExit(f"PortAudio init failed (no sound card?): {exc}") from exc
        try:
            if hasattr(pa, "get_device_count"):  # new layout
                records = _records_new(pa)
            else:  # classic layout
                records = _records_classic(pa)
        finally:
            pa.terminate()

    if as_json:
        print(json.dumps([dataclasses.asdict(r) for r in records], indent=2))
        return
    if not records:
        print("no audio input or output devices found")
        return
    for d in records:
        kind = "/".join(k[:3].upper() for k in d.kinds)  # IN / OUT / IN/OUT
        mark = "*" if d.is_default else " "
        print(
            f"[{kind:<5}] idx={d.index:<2} {mark} "
            f"{d.default_sample_rate:7.0f} Hz "
            f"in={d.max_input_channels} out={d.max_output_channels}  {d.name}"
        )


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="List audio input/output devices.")
    p.add_argument("--json", action="store_true", help="emit JSON instead of table")
    p.add_argument(
        "--loud",
        action="store_true",
        help="show raw ALSA/JACK backend probe warnings on stderr",
    )
    return p.parse_args()


def main() -> None:
    a = parse_args()
    core(a.json, a.loud)


if __name__ == "__main__":
    main()
