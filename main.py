# main.py (terminal-only, config-integrated)


import os, sys
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import sys
import time
from gpt.config import validate_config, get_config  # config wiring [file:9]
from gpt.wakeword import listen_for_wakeword
from gpt.stt import speech_to_text
from gpt.tts import speak
from gpt.chat_engine import ChatEngine
from gpt.import_skills import import_all_skills
from gpt.intent_parser import parse_intent
from gpt.skills.common import (
    tell_joke, calculate, current_time, current_date, set_timer,
    add_todo, list_todos, complete_todo
)
import_all_skills()

IDLE_TIMEOUT = 15 * 60  # 15 minutes


def run_voice_assistant():
    cfg = get_config()  # ensure config instantiated [file:9]
    print("Zoya is ready! Say the configured wake word.")  # startup prompt [file:9]
    active_session = False
    last_interaction = 0
    chat_engine = ChatEngine()

    while True:
        if not active_session:
            print("👂 Waiting for wake word...")
            listen_for_wakeword()  # blocks until detected [file:8]
            speak("Yes, I'm listening.")  # TTS confirmation [file:9]
            active_session = True
            last_interaction = time.time()
            chat_engine.reset()
            continue

        print("🎤 Listening for command...")
        query = speech_to_text()  # mic capture + Google STT [file:7]

        if query:
            print(f"User: {query}")
            intent, params = parse_intent(query)

            if intent == "get_time":
                response = current_time()
            elif intent == "get_date":
                response = current_date()
            elif intent == "tell_joke":
                response = tell_joke()
            elif intent == "calculate":
                expr = str(params.get("expr", ""))
                response = calculate(expr)
            elif intent == "set_timer":
                seconds = int(params.get("seconds", 0))
                response = set_timer("default", seconds)
            elif intent == "add_todo":
                item = str(params.get("item", ""))
                response = add_todo(item)
            elif intent == "list_todos":
                response = list_todos()
            elif intent == "complete_todo":
                idx = int(params.get("index", 0))
                response = complete_todo(idx)
            else:
                result = chat_engine.ask(query)
                response = result["short"]

            print(f"Zoya: {response}")
            speak(response)
            last_interaction = time.time()
        else:
            if time.time() - last_interaction > IDLE_TIMEOUT:
                speak("I'll go to sleep now. Say the wake word to wake me again.")  # [file:9]
                active_session = False
                chat_engine.reset()

        time.sleep(0.1)

if __name__ == '__main__':
    ok = validate_config()  # fail-fast check [file:9]
    if not ok:
        print("❌ Invalid configuration. Please fix the errors above and retry.")  # [file:9]
        sys.exit(1)
    try:
        run_voice_assistant()
    except KeyboardInterrupt:
        print("\n👋 Exiting Zoya...")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
