import sys
import argparse
import numpy as np
import pyaudio
import webrtcvad

FORMAT = pyaudio.paInt16

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CPU Signal to Hailo-10 TPU Whisper Pipeline")
    parser.add_argument("--hef", type=str, default="whisper_base.hef", help="Path to Whisper HEF file for Hailo")
    parser.add_argument("--timeout", type=float, default=5.0, help="Max length of capture in seconds")
    args = parser.parse_args()