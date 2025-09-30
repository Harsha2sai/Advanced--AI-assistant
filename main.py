# main.py (refactored for skill-based architecture)

import os
import sys
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import time
from gpt.config import validate_config, get_config
from gpt.wakeword import listen_for_wakeword
from gpt.stt import speech_to_text
from gpt.tts import speak
from gpt.chat_engine import ChatEngine
from gpt.import_skills import import_all_skills
from gpt.intent_parser import parse_intent

# Import all skills to populate the registry.
# This needs to be done once at startup.
import_all_skills()

IDLE_TIMEOUT = 15 * 60  # 15 minutes

def run_voice_assistant():
    """
    Main loop for the voice assistant.

    Handles wake word listening, command processing, and session management.
    """
    cfg = get_config()
    print("Zoya is ready! Say the configured wake word.")
    active_session = False
    last_interaction = 0
    chat_engine = ChatEngine()

    while True:
        if not active_session:
            print("👂 Waiting for wake word...")
            listen_for_wakeword()
            speak("Yes, I'm listening.")
            active_session = True
            last_interaction = time.time()
            chat_engine.reset()
            continue

        print("🎤 Listening for command...")
        query = speech_to_text()

        if query:
            print(f"User: {query}")

            # Use the new intent parser to find a skill and its parameters
            skill_func, params = parse_intent(query)

            if skill_func:
                # If a specific skill is found, execute it
                try:
                    response = skill_func(**params)
                except Exception as e:
                    response = f"Error executing skill: {e}"
            else:
                # Otherwise, fall back to the general chat engine
                result = chat_engine.ask(query)
                response = result["short"]

            print(f"Zoya: {response}")
            speak(response)
            last_interaction = time.time()

        # Check for idle timeout
        if time.time() - last_interaction > IDLE_TIMEOUT:
            speak("I'll go to sleep now. Say the wake word to wake me again.")
            active_session = False
            chat_engine.reset()

        time.sleep(0.1)

if __name__ == '__main__':
    ok = validate_config()
    if not ok:
        print("❌ Invalid configuration. Please fix the errors above and retry.")
        sys.exit(1)

    try:
        run_voice_assistant()
    except KeyboardInterrupt:
        print("\n👋 Exiting Zoya...")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        # Consider logging the full traceback for debugging
        import traceback
        traceback.print_exc()