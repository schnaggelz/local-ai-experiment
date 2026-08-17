import collections
import logging

import numpy as np
import pyaudio
import webrtcvad

FORMAT = pyaudio.paInt16
SAMPLE_RATE = 16000       # Hz  required by webrtcvad and Whisper
CHANNELS = 1
FRAME_DURATION_MS = 30    # ms per VAD frame (10, 20, or 30)
FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)
SILENCE_TIMEOUT_FRAMES = int(1500 / FRAME_DURATION_MS)  # ~1.5 s of silence ends capture
ONSET_FRAMES = 2       # consecutive speech frames required to trigger recording
PRE_ROLL_FRAMES = 3    # frames kept before onset to avoid clipping word starts
MIN_SPEECH_FRAMES = 5  # discard utterances shorter than this
WARMUP_FRAMES = 2      # frames discarded after opening stream (mic/AGC stabilisation)
ENERGY_THRESHOLD = 0.004  # RMS floor below which a frame is unconditionally silence

log = logging.getLogger(__name__)


class SpeechCapture:
    def __init__(self, input_device_index, vad_mode=3, timeout=5.0,
                 energy_threshold=ENERGY_THRESHOLD):
        self._input_device_index = input_device_index
        self._timeout = timeout
        self._energy_threshold = energy_threshold
        self._vad = webrtcvad.Vad(vad_mode)
        log.debug(f"VAD mode: {vad_mode}, energy threshold: {energy_threshold}")

    @staticmethod
    def _frame_rms(frame: bytes) -> float:
        """RMS energy of a raw int16 PCM frame, normalised to [0, 1]."""
        samples = np.frombuffer(frame, dtype=np.int16).astype(np.float32) / 32768.0
        return float(np.sqrt(np.mean(samples ** 2)))

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

        for _ in range(WARMUP_FRAMES):
            stream.read(FRAME_SIZE, exception_on_overflow=False)

        max_frames = int(self._timeout * 1000 / FRAME_DURATION_MS)
        speech_frames = []
        triggered = False
        silence_count = 0
        onset_count = 0
        onset_buffer = []   # frames buffered during onset detection
        pre_roll = collections.deque(maxlen=PRE_ROLL_FRAMES)  # recent silence frames

        try:
            for _ in range(max_frames):
                frame = stream.read(FRAME_SIZE, exception_on_overflow=False)

                # Skip low-level background noise
                rms = self._frame_rms(frame)
                if rms < self._energy_threshold:
                    is_speech = False
                else:
                    is_speech = self._vad.is_speech(frame, SAMPLE_RATE)
                log.debug(f"VAD: {'speech' if is_speech else 'silence'} rms={rms:.4f}")

                if is_speech:
                    if not triggered:
                        onset_count += 1
                        onset_buffer.append(frame)
                        if onset_count >= ONSET_FRAMES:
                            log.info("Speech detected  recording")
                            triggered = True
                            speech_frames.extend(pre_roll)
                            speech_frames.extend(onset_buffer)
                            onset_buffer.clear()
                            pre_roll.clear()
                    else:
                        silence_count = 0
                        speech_frames.append(frame)
                else:
                    onset_count = 0
                    onset_buffer.clear()
                    if triggered:
                        silence_count += 1
                        speech_frames.append(frame)
                        if silence_count >= SILENCE_TIMEOUT_FRAMES:
                            log.info("Silence detected  end of utterance")
                            break
                    else:
                        pre_roll.append(frame)  # deque auto-evicts oldest when full
        finally:
            stream.stop_stream()
            stream.close()

        if not speech_frames or len(speech_frames) < MIN_SPEECH_FRAMES:
            log.warning("No speech detected within timeout.")
            return None

        return speech_frames


if __name__ == "__main__":
    import time

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    DEVICE_INDEX = 0  # USB Microphone  captured directly at 16000 Hz

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
