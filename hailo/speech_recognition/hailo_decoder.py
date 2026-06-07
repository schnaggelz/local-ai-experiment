import logging
from pathlib import Path

import numpy as np

from hailo_platform import VDevice
from hailo_platform.genai import Speech2Text, Speech2TextTask

log = logging.getLogger(__name__)

SHARED_VDEVICE_GROUP_ID = "SHARED"
SAMPLE_RATE = 16000
N_MELS = 80


class HailoDecoder:
    """Run Whisper encoder on Hailo-10 and decoder on CPU via openai-whisper."""

    def __init__(self, hef_path: str, language: str = "en"):
        self._hef_path = Path(hef_path)
        self._language = language
        self._pipeline = None


    def transcribe(self, raw_audio: np.ndarray) -> str:
        """Transcribe int16 PCM audio to text."""
        
        audio_data = np.frombuffer(raw_audio, dtype=np.int16)

        # Convert 16-bit to float32 and normalize
        audio_data = audio_data.astype(np.float32) / 32768.0

        # Ensure little-endian format as expected by the model
        audio_data = audio_data.astype('<f4')

        # Create generator parameters and generate segments
        segments = self._pipeline.generate_all_segments(
            audio_data=audio_data,
            task=Speech2TextTask.TRANSCRIBE,
            language="en",
            timeout_ms=15000)

        if segments and len(segments) > 0:
            # Combine all segments into a single transcription
            transcription = ''.join([seg.text for seg in segments])
            return transcription.strip()
        
        return None


    def load(self):
        if not self._hef_path.exists():
            raise FileNotFoundError(f"HEF file not found: {self._hef_path}")
        
        log.info(f"Initializing Hailo device...")
        params = VDevice.create_params()
        params.group_id = SHARED_VDEVICE_GROUP_ID
        vdevice = VDevice(params)

        log.info(f"Loading HEF: {self._hef_path}")
        self._pipeline = Speech2Text(vdevice, str(self._hef_path))


if __name__ == "__main__":
    import wave

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    _SCRIPT_DIR = Path(__file__).parent.parent
    HEF_PATH = _SCRIPT_DIR / "models" / "whisper-base.hef"
    WAV_PATH = _SCRIPT_DIR / "resources" / "what_is_the_temp_today.wav"

    with wave.open(str(WAV_PATH), "rb") as wf:
        assert wf.getframerate() == SAMPLE_RATE, f"Expected {SAMPLE_RATE} Hz, got {wf.getframerate()}"
        assert wf.getsampwidth() == 2, "Expected 16-bit PCM"
        raw_audio = wf.readframes(wf.getnframes())

    decoder = HailoDecoder(hef_path=HEF_PATH, language="en")
    decoder.load()

    result = decoder.transcribe(raw_audio)
    print(f"Transcription: {result}")
