import argparse
import logging
import sys
import time
from contextlib import contextmanager

import pyaudio

from command_translator import CommandTranslator
from device_discovery import DeviceDiscovery
from home_assistant import HomeAssistant
from hailo_decoder import HailoDecoder
from speech_capture import SpeechCapture

WAKE_WORD_DEFAULT = "maus"
ACTIVE_TIME_WINDOW = 10  # seconds to stay active after wake word

log = logging.getLogger(__name__)

@contextmanager
def pyaudio_context():
    pa = pyaudio.PyAudio()
    try:
        yield pa
    finally:
        pa.terminate()


def run(
    decoder: HailoDecoder,
    translator: CommandTranslator,
    ha: HomeAssistant,
    input_device: int | None,
    vad_mode: int,
    timeout: float,
    wake_word: str | None,
    active_time_window: float,
) -> None:
    active_until = 0.0

    with pyaudio_context() as pa:
        discovery = DeviceDiscovery(pa)
        input_device_index = discovery.resolve_input_device(input_device)
        capturer = SpeechCapture(
            input_device_index=input_device_index,
            vad_mode=vad_mode,
            timeout=timeout,
        )

        if wake_word is None:
            print("Listening — press Ctrl+C to stop.\n")
        else:
            print(f"Sleeping — say '{wake_word}' to activate. Press Ctrl+C to stop.\n")

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
                is_active = wake_word is None or now < active_until

                if not is_active:
                    if wake_word in text.lower():
                        log.info("Wake word detected")
                        active_until = now + active_time_window
                        print(f"[active for {active_time_window:.0f}s] heard: {text}")
                        translator.translate_and_execute(text)
                    else:
                        log.debug("Ignored (sleeping): %s", text)
                    continue

                print(f"> {text}")
                if not translator.translate_and_execute(text):
                    log.debug("No HA command matched.")

        except KeyboardInterrupt:
            print("\nStopped.")
        finally:
            ha.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    parser = argparse.ArgumentParser(description="Voice → Home Assistant light control via Hailo Whisper")
    parser.add_argument("--hef", required=True, help="Path to Whisper HEF file for Hailo")
    parser.add_argument("--input-device", type=int, default=None, help="Audio input device index")
    parser.add_argument("--list-devices", action="store_true", help="List audio devices and exit")
    parser.add_argument("--timeout", type=float, default=5.0, help="Max capture length in seconds")
    parser.add_argument("--vad-mode", type=int, default=2, choices=[0, 1, 2, 3], help="WebRTC VAD aggressiveness")
    parser.add_argument("--language", default="de", help="Whisper language code (default: de)")
    parser.add_argument("--wake-word", default=WAKE_WORD_DEFAULT, help="Wake word to activate (default: maus)")
    parser.add_argument("--no-wake-word", action="store_true", help="Process every utterance without a wake word")
    parser.add_argument("--active-time-window", type=float, default=ACTIVE_TIME_WINDOW,
                        help="Seconds to stay active after wake word")
    parser.add_argument("--ha-url", default="http://192.168.242.21:8123", help="Home Assistant base URL")
    parser.add_argument("--ha-token", default=None,
                        help="HA long-lived access token (default: read from HA_TOKEN env var)")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    args = parser.parse_args()

    logging.getLogger().setLevel(args.log_level)

    try:
        decoder = HailoDecoder(hef_path=args.hef, language=args.language)
        decoder.load()
    except (RuntimeError, FileNotFoundError) as ex:
        log.error(str(ex))
        sys.exit(1)

    try:
        ha = HomeAssistant(base_url=args.ha_url, token=args.ha_token)
    except ValueError as ex:
        log.error(str(ex))
        sys.exit(1)

    translator = CommandTranslator(ha=ha)

    if args.list_devices:
        with pyaudio_context() as pa:
            DeviceDiscovery(pa).list_devices()
        sys.exit(0)

    run(
        decoder=decoder,
        translator=translator,
        ha=ha,
        input_device=args.input_device,
        vad_mode=args.vad_mode,
        timeout=args.timeout,
        wake_word=None if args.no_wake_word else args.wake_word.lower().strip(),
        active_time_window=args.active_time_window,
    )
