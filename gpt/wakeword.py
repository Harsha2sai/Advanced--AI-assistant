import os
import struct
import pvporcupine
import sounddevice as sd
from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

load_dotenv()


def listen_for_wakeword():
    """Block until wake word is detected."""

    keyword_path = os.path.join(PROJECT_ROOT, "I:\Projects\AI PROJCTS\web gpt\selina_en_windows_v3_0_0 - Copy.ppn")
    
    access_key = os.getenv("PICOVOICE_ACCESS_KEY")
    if not access_key:
        raise ValueError("❌ Missing PICOVOICE_ACCESS_KEY in .env")

    if not os.path.exists(keyword_path):
        raise FileNotFoundError(f"❌ Wakeword file not found at: {keyword_path}")

    porcupine = pvporcupine.create(access_key=access_key, keyword_paths=[keyword_path])

    with sd.InputStream(channels=1, samplerate=porcupine.sample_rate, dtype='int16') as stream:
        print("👂 Waiting for wake word...")
        while True:
            pcm = stream.read(porcupine.frame_length)[0]
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
            result = porcupine.process(pcm)
            if result >= 0:
                print("✅ Wake word detected!")
                return True
