import sys
import argparse
import logging
import pyaudio
from contextlib import contextmanager

from device_discovery import DeviceDiscovery
#from speech_capture import SpeechCapture
from hailo_decoder import HailoDecoder

FORMAT = pyaudio.paInt16

log = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)


@contextmanager
def pyaudio_context():
    pa = pyaudio.PyAudio()
    try:
        yield pa
    finally:
        pa.terminate()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CPU Signal to Hailo-10 TPU Whisper Pipeline")
    parser.add_argument("--hef", type=str, default="whisper_base.hef", help="Path to Whisper HEF file for Hailo")
    parser.add_argument("--timeout", type=float, default=5.0, help="Max length of capture in seconds")
    parser.add_argument("--input-device", type=int, default=None, help="Index of the audio input device to use")
    parser.add_argument("--output-device", type=int, default=None, help="Index of the audio output device to use")
    parser.add_argument("--list-devices", action="store_true", help="List available audio input and output devices")
    parser.add_argument("--vad-mode", type=int, default=3, choices=[0, 1, 2, 3], help="WebRTC VAD aggressiveness (0=least, 3=most)")
    parser.add_argument("--language", type=str, default="en", help="Language code for Whisper decoding (e.g. en, de, fr)")
    parser.add_argument("--log-level", type=str, default="DEBUG", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Set the logging level")
    args = parser.parse_args()

    logging.getLogger().setLevel(args.log_level)

    with pyaudio_context() as audio_context:
        discovery = DeviceDiscovery(audio_context)

        if args.list_devices:
            discovery.list_devices()
            sys.exit(0)

        input_device_index = discovery.resolve_input_device(args.input_device)

        #     capturer = SpeechCapture(
        #         input_device_index=input_device_index,
        #         vad_mode=args.vad_mode,
        #         timeout=args.timeout,
        #     )
        #     audio_data = capturer.capture(audio_context)
        #     if audio_data is None:
        #         sys.exit(0)

        # except (RuntimeError, ValueError) as ex:
        #     log.error(str(ex))
        #     sys.exit(1)

    try:
        decoder = HailoDecoder(hef_path=args.hef, language=args.language)
        decoder.load()
        #text = decoder.transcribe(audio_data)
        #print(text)
    except (RuntimeError, FileNotFoundError) as ex:
        log.error(str(ex))
        sys.exit(1)

