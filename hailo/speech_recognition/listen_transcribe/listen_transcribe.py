import sys
import argparse
import logging
import time
import pyaudio
from contextlib import contextmanager

from common.device_discovery import DeviceDiscovery
from common.speech_capture import SpeechCapture
from common.hailo_decoder import HailoDecoder

WAKE_WORD_DEFAULT = "maus"
ACTIVE_TIME_WINDOW = 10  # seconds to stay active after wake word

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
    parser.add_argument("--list-devices", action="store_true", help="List available audio input and output devices")
    parser.add_argument("--vad-mode", type=int, default=2, choices=[0, 1, 2, 3], help="WebRTC VAD aggressiveness (0=least, 3=most)")
    parser.add_argument("--language", type=str, default="en", help="Language code for Whisper decoding (e.g. en, de, fr)")
    parser.add_argument("--wake-word", type=str, default=WAKE_WORD_DEFAULT, help="Wake word/phrase to activate transcription (case-insensitive)")
    parser.add_argument("--no-wake-word", action="store_true", help="Disable wake word, transcribe everything")
    parser.add_argument("--active-time-window", type=float, default=ACTIVE_TIME_WINDOW, help="Seconds to stay active after wake word before sleeping again")
    parser.add_argument("--log-level", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Set the logging level")
    args = parser.parse_args()

    logging.getLogger().setLevel(args.log_level)

    try:
        decoder = HailoDecoder(hef_path=args.hef, language=args.language)
        decoder.load()
    except (RuntimeError, FileNotFoundError) as ex:
        log.error(str(ex))
        sys.exit(1)

    wake_word = args.wake_word.lower().strip()

    with pyaudio_context() as pa:
        discovery = DeviceDiscovery(pa)

        if args.list_devices:
            discovery.list_devices()
            sys.exit(0)

        input_device_index = discovery.resolve_input_device(args.input_device)
        capturer = SpeechCapture(
            input_device_index=input_device_index,
            vad_mode=args.vad_mode,
            timeout=args.timeout,
        )

        active_until = 0.0  # epoch time until which we stay in active mode

        if args.no_wake_word:
            print("Listening  press Ctrl+C to stop.\n")
        else:
            print(f"Sleeping  say '{wake_word}' to activate. Press Ctrl+C to stop.\n")

        try:
            while True:
                frames = capturer.capture(pa)
                if frames is None:
                    continue
                audio_bytes = b"".join(frames)
                text = decoder.transcribe(audio_bytes)
                if not text:
                    continue

                now = time.monotonic()

                if args.no_wake_word or now < active_until:
                    print(f"> {text}")
                elif wake_word in text.lower():
                    log.info(f"Wake word detected")
                    active_until = now + args.active_time_window
                    print(f"[active for {args.active_time_window:.0f}s] > {text}")
                else:
                    log.debug(f"Ignored (sleeping): {text}")
        except KeyboardInterrupt:
            print("\nStopped.")

