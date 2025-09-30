import os
import struct
import pvporcupine
import sounddevice as sd
from gpt.config import get_config  # use centralized config [file:9]

def listen_for_wakeword():
    """Block until wake word is detected using Porcupine."""
    cfg = get_config()
    keyword_path = cfg.wakeword_path  # validated path from config [file:9]
    access_key = cfg.picovoice_access_key  # validated key [file:9]

    porcupine = pvporcupine.create(
        access_key=access_key,
        keyword_paths=[keyword_path]
    )

    with sd.InputStream(channels=1, samplerate=porcupine.sample_rate, dtype='int16') as stream:
        print("👂 Waiting for wake word...")
        while True:
            pcm = stream.read(porcupine.frame_length)[0]
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
            result = porcupine.process(pcm)
            if result >= 0:
                print("✅ Wake word detected!")
                return True
