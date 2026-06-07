import logging
import pyaudio
import webrtcvad

FORMAT = pyaudio.paInt16
SAMPLE_RATE = 16000       # Hz — required by webrtcvad and Whisper
CHANNELS = 1
FRAME_DURATION_MS = 30    # ms per VAD frame (10, 20, or 30)
FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)
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

        return speech_frames


if __name__ == "__main__":
    import time

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    DEVICE_INDEX = 0  # USB Microphone — captured directly at 16000 Hz

    pa = pyaudio.PyAudio()
    try:
        capturer = SpeechCapture(input_device_index=DEVICE_INDEX)

        print("Press Ctrl+C to stop.\n")
        while True:
            t_start = time.monotonic()
            audio = capturer.capture(pa)
            duration = time.monotonic() - t_start
            if audio is not None:
                recorded_s = len(audio) / SAMPLE_RATE
                print(f"Recorded {recorded_s:.2f}s of speech (wall time: {duration:.2f}s). Waiting for next utterance...\n")
            else:
                print(f"No speech detected (waited {duration:.2f}s). Listening again...\n")
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        pa.terminate()
