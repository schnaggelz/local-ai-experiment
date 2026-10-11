# Mic Test Plan (`mic_test.py`)

Full-loop microphone test: beep -> record -> beep -> replay, all through PyAudio.
Green-field implementation; the script is written from scratch.

## Goal
Prove end-to-end that a microphone captures and speakers play back, with the
recording verified by ear (replay) and by file (WAV dump).

## Design Requirements
- **Device index configurable**: `--in-device IDX` / `--out-device IDX` select
  the PortAudio devices; when omitted, use the PortAudio system default.
  Never hardcode a device index — discover it first with `check_audio_devices.py`
  (the "ls" of audio devices).
- **Drain before stop**: after the last playback write, sleep out the remaining
  buffered duration before `stop_stream()`/`close()`, so the tail is not cut.
- **Gain control**: `--gain` multiplies replay samples (clamped to int16 range);
  quiet mics need boost, so default gain > 1.
- **Self-test mode**: `--sine-loop` fills the "recording" with a generated tone
  instead of mic input — proves the output path without the microphone.
- **WAV evidence**: `--save FILE` writes the mono 16-bit capture as WAV.

## Sequence (one run)
1. Beep on the output device.
2. Record `--seconds` (default 3) from the input device, mono 16-bit at
   `--rate` (default 48000); print RMS/max every 0.5 s while recording.
3. Beep again (marks end of recording).
4. Replay the gain-adjusted recording on the output device.
5. If `--save` given, write the WAV.

## Requirements
- Python 3 with `pyaudio` (e.g. `pip install pyaudio`; needs ALSA headers/libs
  to build on Debian: `libasound2-dev`, `portaudio19-dev`).
- Run with any interpreter that has pyaudio installed.
- An input device and an output device (same card is fine).

## Roadmap

### Phase 1: Implement
- [x] Write `mic_test.py` implementing the sequence and design requirements.
- [x] CLI: `--freq --seconds --volume --gain --rate --in-device --out-device
  --sine-loop --save --loud`.

### Phase 2: Discover Devices
- [x] Run `check_audio_devices.py`; note the input/output device indices.
  -> idx=0 `SPACE: USB Audio (hw:0,0)` (in=1, out=2) for both.

### Phase 3: Bisect Output Path
- [x] Run with `--sine-loop`.
  - works -> output path OK; issues are on the input side.
  - Verified: beep-beep pause beep-beep pause long-beep all audible.

### Phase 4: Full Mic Loop
- [x] Run with real mic input (beep -> record -> beep -> replay).
- [x] Verify replay is audible and complete (not truncated).
  - Vocal-count protocol: 7/7 words captured in a 6 s window.

### Phase 5: Evidence
- [x] `--save` WAV; check file size = rate * seconds * 2 bytes + 44 B header.
  -> exact (44 + 2 x samples) every run.
- [x] Check per-0.5-s RMS/max lines are nonzero while speaking.
- [ ] Optional cross-check: `aplay` the saved WAV.

## Fixes Applied (after first run)
- Input stream is opened+warmed BEFORE the rec cue; capture starts ~0.2 s
  before the cue ends (on_queued, CAPTURE_EARLY) - first spoken word no
  longer clipped.
- Input stream stays open through the end cue: the input-close ->
  output-open transition had been swallowing the end cue on this USB card.
- Post-capture drain is skipped (capture outlasts playback) - the end cue
  now sounds ~0.6 s after recording stops, not ~2 s.
- Residual crack at end of the end-cue playback: deferred (device/ALSA
  artifact, script TODO unchanged).
- Sparse-count note: user must stay within the `--seconds` window; words
  spoken after it are not captured.

## Getting Started
```
python3 examples/audio_devices/check_audio_devices.py   # find device indices
python3 examples/audio_devices/mic_test.py --sine-loop --in-device IDX --out-device IDX
python3 examples/audio_devices/mic_test.py --in-device IDX --out-device IDX --save /tmp/mic.wav
```
