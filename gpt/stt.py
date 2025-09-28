import speech_recognition as sr

recognizer = sr.Recognizer()

def speech_to_text(timeout=5, phrase_time_limit=10):
    """Capture speech from mic and convert to text."""
    with sr.Microphone() as source:
        print("🎤 Listening...")
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            text = recognizer.recognize_google(audio)  # Google STT
            print(f"📝 You said: {text}")
            return text
        except sr.WaitTimeoutError:
            print("⌛ No speech detected.")
            return None
        except sr.UnknownValueError:
            print("❓ Could not understand audio.")
            return None
        except sr.RequestError as e:
            print(f"⚠️ STT error: {e}")
            return None
