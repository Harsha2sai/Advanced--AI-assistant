# main.py (terminal-only, config-integrated)


import os, sys, pathlib, logging
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info(f"cwd={os.getcwd()} sys.path[0]={sys.path[0]} file_dir={pathlib.Path(__file__).parent}")

import sys
import time
from gpt.config import validate_config, get_config  # config wiring [file:9]
from gpt.wakeword import listen_for_wakeword
from gpt.stt import speech_to_text
from gpt.tts import speak
from gpt.chat_engine import ChatEngine
from gpt.import_skills import import_all_skills
from gpt.intent_parser import IntentParser
from gpt.skills import system_skills as sys_skills
from gpt.skills import common as common_skills
from gpt.skills import web_services as web_skills
from gpt.skills.installed_apps import get_installed_apps
import_all_skills()

def find_app_path(installed_apps: dict, app_name: str) -> str:
    # Simplify comparison
    app_name = app_name.lower().strip()
    # Exact and partial match search (case-insensitive)
    matches = {name:path for name, path in installed_apps.items() if app_name in name.lower()}
    
    if not matches:
        return ""
    # Return first match path
    return list(matches.values())[0]

IDLE_TIMEOUT = 15 * 60  # 15 minutes


def run_voice_assistant():
    cfg = get_config()  # ensure config instantiated [file:9]
    print("Zoya is ready! Say the configured wake word.")  # startup prompt [file:9]
    active_session = False
    last_interaction = 0
    chat_engine = ChatEngine()
    intent_parser = IntentParser() # Initialize intent parser here
    installed_apps = get_installed_apps()
    print(f"Discovered {len(installed_apps)} installed applications.")

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
            
            # Try intent parsing first
            intent, params = intent_parser.parse(query)
            
            if intent:
                print(f"🎯 Intent matched: {intent} with params: {params}")
                
                # Route to appropriate skill function
                try:
                    if intent == "get_volume":
                        response = sys_skills.get_volume()
                    elif intent == "set_volume":
                        response = sys_skills.set_volume(params.get("volume", 50))
                    elif intent == "increase_volume":
                        response = sys_skills.increase_volume(params.get("amount", 10))
                    elif intent == "decrease_volume":
                        response = sys_skills.decrease_volume(params.get("amount", 10))
                    elif intent == "mute_volume":
                        response = sys_skills.mute_volume()
                    elif intent == "unmute_volume":
                        response = sys_skills.unmute_volume()
                    elif intent == "launch_app":
                        app_name_to_launch = params.get("app", "")
                        app_path = find_app_path(installed_apps, app_name_to_launch)
                        response = sys_skills.launch_app(app_name_to_launch, app_path)
                    elif intent == "take_screenshot":
                        response = sys_skills.take_screenshot()
                    elif intent == "get_time":
                        response = common_skills.current_time()
                    elif intent == "get_date":
                        response = common_skills.current_date()
                    elif intent == "tell_joke":
                        response = common_skills.tell_joke()
                    elif intent == "calculate":
                        response = common_skills.calculate(params.get("expression", ""))
                    elif intent == "get_brightness":
                        response = sys_skills.get_brightness()
                    elif intent == "set_brightness":
                        response = sys_skills.set_brightness(params.get("brightness", 50))
                    elif intent == "increase_brightness":
                        response = sys_skills.increase_brightness()
                    elif intent == "decrease_brightness":
                        response = sys_skills.decrease_brightness()
                    elif intent == "system_info":
                        response = sys_skills.system_info()
                    
                    # Web services
                    elif intent == "web_search":
                        response = web_skills.search_web(params.get("query", ""))
                    elif intent == "get_weather":
                        response = web_skills.get_weather(params.get("location", ""))
                    elif intent == "get_news":
                        response = web_skills.get_news(params.get("query", "latest"))
                    elif intent == "get_forex_news":
                        response = web_skills.get_forex_news()
                    elif intent == "search_wikipedia":
                        response = web_skills.search_wikipedia(params.get("topic", ""))
                    elif intent == "get_crypto_prices":
                        response = web_skills.get_crypto_prices(params.get("symbols", "bitcoin"))
                    elif intent == "get_twitter":
                        response = web_skills.get_twitter_posts(params.get("query", ""))
                    elif intent == "get_reddit":
                        response = web_skills.get_reddit_posts(params.get("subreddit", ""))
                    else:
                        response = f"Intent '{intent}' not implemented yet"
                    
                    print(f"✅ Skill response: {response}")
                    
                except Exception as e:
                    print(f"❌ Skill execution failed: {e}")
                    response = f"Sorry, there was an error executing that command: {e}"
            
            else:
                # Fallback to LLM for conversational responses
                print("🤖 No intent matched, routing to LLM...")
                result = chat_engine.ask(query)
                response = result["short"]

            print(f"Zoya: {response}")
            speak(str(response)) # Explicitly cast to str
            last_interaction = time.time()
        else:
            if time.time() - last_interaction > IDLE_TIMEOUT:
                speak("I'll go to sleep now. Say the wake word to wake me again.")
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
