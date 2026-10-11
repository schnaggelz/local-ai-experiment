# Local TTS Plan (Piper, CPU)

Text to speech on the CPU with Piper (ONNX neural TTS), played through the
same USB speakerphone the ASR example records from. Companion to
`examples/asr/` (listen) and the future reply loop (listen -> think -> speak).

## Goal
Turn a string into audible speech locally: `say.py "text"` synthesizes with
Piper and plays it on the SPACE speaker. No cloud, no NPU (the Hailo genai
5.4.0 API exposes only `LLM`, `Speech2Text`, `Speech2TextTask`, `VDevice`,
`VLM` -- there is no TTS op, so the encoder/decoder stays on the CPU).

## Design
- **Engine**: `piper-tts` 1.8.0 + `onnxruntime` 1.31.0, installed **only** in
  `.venv-hailo-sdk`. Python API, not a subprocess:
  `PiperVoice.load(model.onnx)` once, then `voice.synthesize(text)` yields
  `AudioChunk`s with `audio_int16_bytes`.
- **Voices**: files live in `models/tts/` (`<voice>.onnx` + `<voice>.onnx.json`),
  fetched with `python -m piper.download_voices --download-dir models/tts
  <voice>`. Language is selectable by picking the voice file (`--voice NAME`),
  not by a language code: German `de_DE-thorsten-low`, English `en_US-amy-low`
  are already downloaded (63 MB each).
- **Rate luck**: these voices emit **16 kHz mono int16** -- exactly Whisper's
  native rate in `examples/asr`, and a rate the ALSA `default` output device
  accepts, so neither part of a reply loop needs resampling.
- **Playback**: PyAudio at the voice's own rate, same open-with-fallback lesson
  as the mic: raw `hw:0,0` (idx 0) accepts only 48 kHz, `default` (idx 6)
  resamples anything (16 / 22.05 / 24 / 48 kHz all OK). `aplay` remains the
  documented fallback for a quick manual check of a saved file.
  Three hard-won details (see "Playback notes" below): chunked writes, an
  explicit `start_stream()`, and a **0.75 s silence lead-in**, because this
  PortAudio/ALSA path eats the head of a freshly started stream.
- **CLI**: `say.py TEXT | --text TEXT`, `--voice NAME`, `--out FILE.wav`,
  `--no-play` (synth only), `--out-device IDX`, `--loud` (raw ALSA probe
  chatter), `--list-voices`, `--length-scale` (speed, Piper's `length_scale`).
  Still to come: `--stdin` (speak each line).
- Split: `parse_args() -> main() -> synthesize()/play()`, heavy dep imported
  lazily inside `synthesize()` (repo Python skill rules).

## Measured (Pi 5, this repo, 2026-10-10)
| fact | value |
|---|---|
| piper-tts / onnxruntime | 1.8.0 / 1.31.0 (aarch64 wheels from piwheels) |
| voice model size | 63,104,526 bytes each (low) |
| voice sample rate | 16000 Hz mono int16 |
| model load | 3.3 s (once per voice) |
| synth speed | RTF 0.08-0.10x -> ~10x faster than realtime |
| example | 47 chars -> 2.64 s audio in 0.24 s, 84524-byte WAV (say.py) |
| stderr noise | `Missing phoneme from id map: ̧` (U+0327) on German synth -- real bug, see below |
| playback probe | `default` idx 6: 16/22.05/24/48 kHz OK; `hw:0,0` idx 0: 48 kHz only |
| playback wall | 1.41 s audio -> 2.52 s wall with pad 1.0 s; pad 0.75 s is also clean |
| synth determinism | two identical runs differ (27,028 of 31,276 bytes); `SynthesisConfig(noise_scale=0, noise_w_scale=0)` is byte-reproducible |

## Playback notes (PyAudio + ALSA on this box)
Symptom: `aplay -D default` played a saved file cleanly, while in-process
Playback of the same bytes sounded **clipped at the start** and (with one big
`stream.write()`) had a **hole mid-stream**.

| change tested | result |
|---|---|
| one `stream.write()` of the whole utterance | hole mid-stream |
| chunked 20 ms writes (`CHUNK_SECONDS`) | hole gone -> keep |
| mono stream (`channels=1`) | possible extra startup damage; sibling `play_test_tone.py` uses 2 -> duplicate mono to `min(2, max)`, keep |
| explicit `start=False` + `start_stream()` | keep (implicit start is the suspicious part) |
| lead-in pad 0.0 / 0.15 / 0.5 / 0.75 / 1.0 s | 3 / 3 / 4 / 5 / 5 of 5 test tones audible -> **0.75 s works** |

Test signal for this was ear-countable, not a recording: 5 x 100 ms tones
(1.0-3.0 kHz, no gaps) + 300 ms silence + speech, played in-process vs `aplay`.
A mic recording with `arecord` was tried and **abandoned** -- the speakerphone's
AGC/echo smeared the first ~1.4 s, so it could not tell loss from gain.

Conclusion: a fixed ~0.2 s startup loss does **not** explain a pad that keeps
helping up to 1.0 s; the likely mechanism is the device's own gain/AEC ramp
right after a stream opens. The pad covers it, at the cost of ~0.75 s of dead
air before each utterance (fine for a reply bot; revisit for barge-in).

## Sequence (one run)
1. Resolve `--voice` to `models/tts/<voice>.onnx`, load it (3.3 s).
2. Synthesize the text to int16 PCM at 16 kHz.
3. Play it on the output device (fall back if the requested one refuses).
4. Print what was said plus `synth X.XXs | audio Y.YYs | RTF Z.ZZx`; with
   `--out` also write the WAV.

## Requirements
- `.venv-hailo-sdk` with `piper-tts` (installed) and a voice in `models/tts/`.
- A working output device (idx 6 `default`, or 0 with 48 kHz resampling).

## Roadmap

### Phase 1: Synth Smoke Test
- [x] `say.py --text "..." --voice de_DE-thorsten-low --out out.wav --no-play`:
      synthesize only, write a 16 kHz mono WAV, print timing.
      -> implemented (synth-only by design: `--out` saves, otherwise nothing is
      written); `say.py --voice ... --text ... --out /tmp/say_de.wav` gives
      `load 3.06s | synth 0.24s | audio 2.64s | RTF 0.09x` and an 84524-byte
      16000 Hz mono WAV. Also: `--list-voices`, `--voice <path.onnx>`,
      `--length-scale`, missing-voice exit code 1 with a download hint.
- [x] Verify the WAV plays and is intelligible (`aplay -D default out.wav`).
      -> PASS: `aplay` reports `Signed 16 bit Little Endian, Rate 16000 Hz,
      Mono` and plays both voices; intelligibility confirmed by ear.
- [x] Verify a second voice/language works by only changing `--voice`.
      -> PASS: `en_US-amy-low` (English) vs `de_DE-thorsten-low` (German),
      same command, no other change.

### Phase 2: Live Playback
- [x] Play the synthesized PCM in-process at 16 kHz.
      -> done: `synthesize() -> save (--out) -> play()`, mono duplicated to the
      device's channels, lazy `pyaudio` import.
- [x] Output-device fallback when the requested device refuses the rate.
      -> done: `[--out-device] -> system default -> every output -> None`;
      verified with `--out-device 0` (48 kHz-only card) -> warns
      `! device 0 refused 16000 Hz ([Errno -9997] Invalid sample rate); trying
      others` and plays on idx 6.
- [x] Print `synth | audio | RTF` per utterance so CPU cost is visible.
      -> done: `load 3.27s | synth 0.12s | audio 1.41s | RTF 0.09x`, then
      `playing idx 6 (default) @ 16000 Hz x2, 1.41s` and `played in 2.52s wall`.
- [x] Startup robustness (not in the original list, found by ear): chunked
      writes, explicit `start_stream()`, 0.75 s silence lead-in -> see
      "Playback notes".

### Phase 3: Speak Lines (reply-bot shape)
- [ ] `--stdin` reads lines and speaks each until Ctrl-C or EOF.
- [ ] Keep the model loaded across lines (no 3.3 s reload per sentence).
- [ ] Optional: `--length-scale` for slower/faster speech.

### Phase 4: Evidence
- [ ] Saved WAV from the live path matches the played audio byte for byte.
      Caveat: Piper sampling is stochastic by default, so compare the WAV that
      `play()` was handed within one run, or synthesize with `noise_scale=0`.
- [ ] Timing table for both voices (chars, audio s, synth s, RTF).
- [ ] Round trip with `examples/asr`: speak a Piper WAV file, transcribe it
      back on the Hailo NPU, compare the text to the original string.

## Getting Started
```
.venv-hailo-sdk/bin/python -m piper.download_voices \
    --download-dir models/tts de_DE-thorsten-low en_US-amy-low

.venv-hailo-sdk/bin/python examples/tts/say.py \
    --voice de_DE-thorsten-low --text "Hallo, ich bin der Baer." \
    --out /tmp/tts_out.wav          # plays in-process AND saves

.venv-hailo-sdk/bin/python examples/tts/say.py \
    --voice de_DE-thorsten-low --text "Hallo, ich bin der Baer." \
    --out /tmp/tts_out.wav --no-play   # synth only

aplay -D default /tmp/tts_out.wav      # reference playback
```

## Open Questions
- **German `ç` is dropped (real bug, unfixed).** `piper-tts` 1.8.0 NFD-splits
  espeak-ng's IPA into codepoints (`phonemize_espeak.py`), but these
  `piper_version 0.2.0` voices store only the precomposed phoneme, so
  `phoneme_id_map["ç"]` is never hit: `ich` -> `ɪ c` and the combining cedilla
  is skipped. Audible result: `ich`/`München`/`Küche` -> `ik`/`Münken`/`Küke`.
  English barely uses `ç`, so only German is affected. Fix options: re-merge
  base+combining with NFC when the merged char exists in the voice's map, or
  switch to a voice whose map has the combining marks. Not touched yet.
- Pad cost settled: 0.5 s clips, **0.75 s is clean** -> that is `LEAD_IN_SECONDS`.
  Re-tune per device if the speaker changes.
- German voice quality: `-low` is fast (RTF 0.1); is `de_DE-thorsten-medium`
  (bigger, slower) worth it on the Pi 5?
- Barge-in: should playback stop if the ASR side hears speech? (Not needed
  until the reply loop exists.)
- Long text: chunk by sentence so the first words are heard sooner.
- `espeak-ng` as a zero-model fallback engine (needs apt/sudo, so not now).