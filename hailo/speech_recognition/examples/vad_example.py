#!/usr/bin/env python3
"""Minimal VAD example: captures mic audio, prints speech/silence decisions in real time."""

import sys

import pyaudio
import webrtcvad

SAMPLE_RATE = 16000           # Hz  required by webrtcvad
FRAME_MS = 30                 # frame length: 10, 20, or 30 ms
FRAME_SAMPLES = int(SAMPLE_RATE * FRAME_MS / 1000)


def main(device_index: int | None = None, vad_mode: int = 3) -> None:
    vad = webrtcvad.Vad(vad_mode)
    pa = pyaudio.PyAudio()

    stream = pa.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=SAMPLE_RATE,
        input=True,
        input_device_index=device_index,
        frames_per_buffer=FRAME_SAMPLES,
    )

    print(f"VAD mode {vad_mode}  press Ctrl+C to stop\n")
    try:
        while True:
            raw = stream.read(FRAME_SAMPLES, exception_on_overflow=False)
            is_speech = vad.is_speech(raw, SAMPLE_RATE)
            label = "SPEECH " if is_speech else "silence"
            print(f"\r[{label}]", end="", flush=True)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()


if __name__ == "__main__":
    idx = int(sys.argv[1]) if len(sys.argv) > 1 else None
    mode = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    main(device_index=idx, vad_mode=mode)
