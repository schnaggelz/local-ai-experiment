import logging
import numpy as np
import pyaudio
import webrtcvad

FORMAT = pyaudio.paInt16
SAMPLE_RATE = 16000       # Hz — must be 8000, 16000, 32000, or 48000 for webrtcvad
CHANNELS = 1
FRAME_DURATION_MS = 30    # ms per VAD frame (10, 20, or 30)
FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)  # samples per frame
SILENCE_TIMEOUT_FRAMES = int(1000 / FRAME_DURATION_MS)   # ~1 s of silence ends capture

log = logging.getLogger(__name__)


class SpeechCapture:
    def __init__(self, input_device_index, vad_mode=3, timeout=5.0):
        self._input_device_index = input_device_index
        self._timeout = timeout
        self._vad = webrtcvad.Vad(vad_mode)
        log.debug(f"VAD mode: {vad_mode}")

    def capture(self, pa):
        stream = pa.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            input_device_index=self._input_device_index,
            frames_per_buffer=FRAME_SIZE,
        )
        log.info("Listening... (speak now)")

        max_frames = int(self._timeout * 1000 / FRAME_DURATION_MS)
        speech_frames = []
        triggered = False
        silence_count = 0

        try:
            for _ in range(max_frames):
                frame = stream.read(FRAME_SIZE, exception_on_overflow=False)
                is_speech = self._vad.is_speech(frame, SAMPLE_RATE)
                log.debug(f"VAD: {'speech' if is_speech else 'silence'}")

                if is_speech:
                    if not triggered:
                        log.info("Speech detected — recording")
                        triggered = True
                    silence_count = 0
                    speech_frames.append(frame)
                elif triggered:
                    silence_count += 1
                    speech_frames.append(frame)
                    if silence_count >= SILENCE_TIMEOUT_FRAMES:
                        log.info("Silence detected — end of utterance")
                        break
        finally:
            stream.stop_stream()
            stream.close()

        if not speech_frames:
            log.warning("No speech detected within timeout.")
            return None

        audio_data = np.frombuffer(b"".join(speech_frames), dtype=np.int16)
        log.info(f"Captured {len(audio_data) / SAMPLE_RATE:.2f}s of audio ({len(speech_frames)} frames)")
        return audio_data
