#!/usr/bin/env python3
"""Smoke test: verify Hailo-10 hardware + Speech2Text pipeline on this Raspberry Pi.

Stages:
  1. Device node /dev/h1x-0 exists
  2. Kernel module hailo1x_pci loaded
  3. hailortcli can see the device
  4. Python SDK opens VDevice and loads the Whisper HEF
  5. Real inference pass on generated audio completes within a sane time

Usage:
  .venv-hailo-sdk/bin/python smoke_test.py
  .venv-hailo-sdk/bin/python smoke_test.py --hef models/whisper-base.hef --duration 3
"""
import argparse
import os
import subprocess
import sys
import time

import numpy as np

from hailo_platform import VDevice
from hailo_platform.genai import Speech2Text, Speech2TextTask


DEVICE_NODE = "/dev/h1x-0"
KMOD = "hailo1x_pci"


def check_device_node():
    if os.path.exists(DEVICE_NODE):
        return True, f"device node {DEVICE_NODE} exists"
    return False, f"{DEVICE_NODE} missing"


def check_kernel_module():
    try:
        out = subprocess.check_output(["cat", "/proc/modules"], text=True)
    except FileNotFoundError:
        out = ""
    if KMOD in out:
        return True, f"kernel module {KMOD} loaded"
    return False, f"kernel module {KMOD} not loaded"


def check_hailortcli():
    try:
        out = subprocess.check_output(
            ["hailortcli", "scan"], text=True, timeout=15, stderr=subprocess.STDOUT
        )
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
        return False, f"hailortcli scan failed: {e}"
    if "0001:01:00.0" in out or "HAILO10H" in out or "Device" in out:
        return True, "hailortcli sees the device"
    return False, "hailortcli ran but reported no device\n" + out


def load_pipeline(hef):
    if not os.path.isfile(hef):
        return None, False, f"HEF not found: {hef}"
    try:
        params = VDevice.create_params()
        params.group_id = "smoke_test"
        vdev = VDevice(params)
        pipe = Speech2Text(vdev, hef)
    except Exception as e:
        return None, False, f"Speech2Text init failed: {e}"
    return pipe, True, "VDevice opened + HEF loaded"


def run_inference(pipe, duration_s, language):
    sr = 16000
    samples = int(duration_s * sr)
    # 2 s of silence is enough; format matches Whisper input (float32, [-1, 1]).
    audio = np.zeros(samples, dtype="<f4")
    t0 = time.time()
    try:
        segments = pipe.generate_all_segments(
            audio_data=audio,
            task=Speech2TextTask.TRANSCRIBE,
            language=language,
            timeout_ms=60000,
        )
    except Exception as e:
        return False, f"inference raised: {e}"
    dt = time.time() - t0
    rt_factor = dt / duration_s if duration_s else float("inf")
    text = " ".join((s.text or "") for s in segments).strip() if segments else ""
    msg = f"inference done in {dt:.2f}s (RT factor {rt_factor:.1f}x)"
    if segments:
        msg += f" -> {text!r}"
    if rt_factor > 30:
        return False, msg + " (too slow)"
    return True, msg


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hef", default="models/whisper-base.hef", help="path to whisper HEF")
    ap.add_argument("--duration", type=float, default=2.0, help="audio length in seconds for inference")
    ap.add_argument("--language", default="en", help="Whisper language code")
    args = ap.parse_args()

    results = []
    print("== Hailo-10 smoke test ==")
    for name, fn in [
        ("device node", check_device_node),
        ("kernel module", check_kernel_module),
        ("hailortcli scan", check_hailortcli),
    ]:
        ok, msg = fn()
        results.append(ok)
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {msg}")

    pipe, ok, msg = load_pipeline(args.hef)
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] SDK load: {msg}")
    if not ok:
        print("\nSUMMARY: FAILED")
        return 1

    ok2, msg2 = run_inference(pipe, args.duration, args.language)
    results.append(ok2)
    print(f"[{'PASS' if ok2 else 'FAIL'}] inference: {msg2}")

    print("\nSUMMARY: " + ("ALL PASS" if all(results) else "FAILED"))
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
