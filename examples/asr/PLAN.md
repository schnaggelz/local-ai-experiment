# Local ASR Plan (Hailo H10 NPU)

Speech recognition on the Hailo H10 accelerator: whisper-base on the NPU,
mic -> VAD -> text, printed to stdout. Green-field example (the existing
`hailo/speech_recognition/` folder is untested/broken: missing smoke test,
wrong hef default). Companion to `examples/audio_devices/` (mic) and a
future `examples/tts/` (reply).

## Goal
Prove the full listen path works on the NPU: capture a spoken utterance,
run it through whisper-base on the Hailo device, print the transcript.
TTS (Piper, CPU) is a separate later example.

## Design
- **NPU inference**: Hailo genai `Speech2Text` (`hailo_platform.genai`);
  whisper encoder runs on the NPU, decoder on CPU. 16 kHz mono input.
- **Audio**: PyAudio 16 kHz mono int16 (whisper native rate). Device index
  selectable (`--in-device`); discover with `check_audio_devices.py` first,
  never hardcode.
- **Endpointing**: WebRTC VAD (aggressiveness flag) with onset frames,
  pre-roll to save word starts, silence timeout to end an utterance
  (pattern from `hailo/speech_recognition/common/speech_capture.py`).
- **CLI**: `--hef --in-device --vad-mode --language --task --timeout --gain
  --list-devices`.
- **Sync test mode**: `--once` for a hands-on round (Enter arms, a printed
  `>>> SPEAK NOW <<<` banner marks the start, `>>> STOP TALKING <<<` the end,
  then the transcript and an exit code). No audible cue: a banner is enough and
  keeps the tool free of output-device handling.
- Reuse `examples/audio_devices/check_audio_devices.py` for device listing.
- **Rate/device traps (measured)**: raw `hw:0,0` (idx 0) accepts only 48 kHz
  USB-native -> `OSError -9997`; `default`/`sysdefault` resample to 16 kHz for
  us. Enumeration order and the `is_format_supported` probe are both unreliable
  (a busy device can vanish from the list; the probe reports false negatives),
  so device choice trusts a real `open()` with fallback.
- **Language is a hard filter (measured)**: `language` is passed to
  `generate_all_segments`, and a wrong code makes whisper decode in that
  language rather than flag an error. German speech ("Hallo, ich bin der
  Baer") gave: `--language en` -> "Hello, I'm Der Bear.", `--language de` or
  auto-detect -> "Hallo ich bin der Ber.", `--task translate` -> English.
  So both tools default to auto-detect (`None`) and expose
  `--task transcribe|translate`.
- **Mic level (measured)**: card 0 `Headset` capture is already 100%
  (-0.06 dB), yet speech peaks only ~-27 dBFS -> `--gain` software boost.

## Sequence (one run)
1. Load `whisper-base.hef` on the Hailo device (VDevice, genai Speech2Text)
   **once**, before the capture loop (loading costs ~1-6 s).
2. Capture one utterance (VAD-gated) from the mic at 16 kHz mono.
3. Transcribe in-process on the NPU; print text + per-utterance timing.
4. Loop for the next utterance (Ctrl-C to stop).

## Requirements
- `.venv-hailo-sdk` (hailort 5.4.0, numpy, pyaudio, webrtcvad) -- all present.
- `models/whisper-base.hef` (present) and a working Hailo device (H10).

## Roadmap

### Phase 1: NPU Smoke Test
- [x] `transcribe_wav.py`: run whisper-base.hef on a WAV file (no mic) via
      genai Speech2Text, print the transcript.
- [x] Verify on `hailo/resources/what_is_the_temp_today.wav`
      (16 kHz mono, 11 s) - expected text is the file's spoken phrase.
      -> PASS: correct JFK quote; model load 5.6 s, inference 1.0 s / 11 s audio.
- [x] If transcription is empty/garbage, debug before touching mic code.

### Phase 2: Mic Capture
- [x] `transcribe_mic.py`: open mic at 16 kHz mono, VAD endpoint one
      utterance (onset + pre-roll + silence timeout), print RMS/VAD state.
- [x] Verify an utterance captures cleanly (speak, silence, done).
      -> PASS: 1.65 s / 26400 samples captured, `rec`/RMS lines live,
      1.5 s trailing silence ended it; WAV written (52844 bytes).

### Phase 3: Wire NPU + Mic
- [x] Feed the captured utterance to the Hailo whisper pipeline; print text.
      -> implemented in `transcribe_mic.py` (`load_asr` once, `_transcribe` per
      utterance, `--hef/--language/--no-npu`); heavy deps lazily imported.
      Verified offline through the real functions with the reference WAV:
      11.00 s audio -> 1.01 s NPU (10.9x realtime), correct JFK quote.
- [x] Live check: mic + NPU in one process, `--hef models/whisper-base.hef`.
      -> PASS via the new `--once` sync mode (Enter to arm, beep = speak,
      trailing silence = stop, beep = done): 4.50 s utterance at -2 dBFS ->
      NPU 0.38 s (11.9x realtime) -> `TRANSCRIPT: Hello, I'm Der Bear.`
      NOTE: idle wait has no give-up; a `--wait` cap is still missing.
- [x] Loop utterances until Ctrl-C; print per-utterance timing
      (capture vs inference) so NPU speed is visible.
      -> `npu: X.XX s for Y.YY s audio (Z.Zx realtime)` next to the capture
      `utterance: ...` line.
      Caveat: the live mic + NPU run is still pending (see the item above).

### Phase 4: Evidence
- [x] `--save-raw FILE` writes the raw int16 utterance for offline checks.
- [x] Cross-check: pipe the saved WAV through `transcribe_wav.py` -- same
      transcript as the live mic path.
      -> PASS (same audio, NPU 0.2 s): live capture -> `TRANSCRIPT: the`.
      Caveat: the utterance was only 1.65 s and ~-27 dBFS, so the text is thin.
- [x] Nonzero RMS lines while speaking (reuse audio_devices reporting style).
      -> `rec 0.5s rms=33`, `rec 1.0s rms=40` (quiet mic; use `--gain`).
- [x] Re-verify with `--gain 4` that a full sentence transcribes correctly.
      -> PASS: 2.94 s utterance (peak -16 dBFS, 0 clipped samples) ->
      `TRANSCRIPT: I'm going to do the first one.` (NPU 0.4 s).
      Note: louder/closer speech clipped at gain 4 (peak 32768 = 0 dBFS),
      so gain 2 is the safer default for this mic.

## Getting Started
```
.venv-hailo-sdk/bin/python examples/asr/transcribe_wav.py \
    --hef models/whisper-base.hef \
    hailo/resources/what_is_the_temp_today.wav

.venv-hailo-sdk/bin/python examples/asr/transcribe_mic.py \
    --hef models/whisper-base.hef --in-device 0 --language en --gain 4
```
(`--in-device` is optional: it falls back to another input if the raw device
refuses 16 kHz. Use `--list-devices` first; indices shift between runs.)
