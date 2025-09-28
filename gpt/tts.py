import pyttsx3
import re

def speak(text: str):
    """Convert text to speech in smaller chunks (blocking)."""
    if not text:
        return
    print(f"🔊 Speaking: {text}")

    chunks = re.split(r'(?<=[.!?]) +|\n+', text)
    engine = pyttsx3.init()
    engine.setProperty("rate", 170)
    engine.setProperty("volume", 1.0)

    for chunk in chunks:
        if chunk.strip():
            engine.say(chunk.strip())
            engine.runAndWait()
    engine.stop()

def speak_stream(text_stream):
    """Speak streaming text chunks as they arrive."""
    engine = pyttsx3.init()
    engine.setProperty("rate", 170)
    engine.setProperty("volume", 1.0)

    buffer = ""

    for chunk in text_stream:
        print(chunk, end="", flush=True)
        buffer += chunk

        if buffer.endswith((".", "!", "?", "\n")) or len(buffer) > 80:
            engine.say(buffer.strip())
            engine.runAndWait()
            buffer = ""

    if buffer.strip():
        engine.say(buffer.strip())
        engine.runAndWait()
    engine.stop()
