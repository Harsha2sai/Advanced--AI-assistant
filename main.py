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
from gpt.intent_parser import IntentParser
from gpt.skills import system_skills as sys_skills
from gpt.skills import common as common_skills
from gpt.skills import web_services as web_skills
from gpt.skills.installed_apps import get_installed_apps
from gpt.skills import ( # Import all skills directly from the package's __init__.py
    start_screen_recording, stop_screen_recording,
    blank_screen, wake_screen, lock_screen,
    shutdown_system, restart_system, sleep_system,
    hibernate_system, cancel_power_task
)

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

    # Define handler functions for each intent
    def handle_get_volume(params):
        return sys_skills.get_volume()

    def handle_set_volume(params):
        return sys_skills.set_volume(params.get("volume", 50))

    def handle_increase_volume(params):
        return sys_skills.increase_volume(params.get("amount", 10))

    def handle_decrease_volume(params):
        return sys_skills.decrease_volume(params.get("amount", 10))

    def handle_mute_volume(params):
        return sys_skills.mute_volume()

    def handle_unmute_volume(params):
        return sys_skills.unmute_volume()

    def handle_launch_app(params):
        app_name_to_launch = params.get("app", "")
        app_path = find_app_path(installed_apps, app_name_to_launch)
        return sys_skills.launch_app(app_name_to_launch, app_path)

    def handle_take_screenshot(params):
        return sys_skills.take_screenshot()

    def handle_get_time(params):
        return common_skills.current_time()

    def handle_get_date(params):
        return common_skills.current_date()

    def handle_tell_joke(params):
        return common_skills.tell_joke()

    def handle_calculate(params):
        return common_skills.calculate(params.get("expression", ""))

    def handle_get_brightness(params):
        return sys_skills.get_brightness()

    def handle_set_brightness(params):
        return sys_skills.set_brightness(params.get("brightness", 50))

    def handle_increase_brightness(params):
        return sys_skills.increase_brightness()

    def handle_decrease_brightness(params):
        return sys_skills.decrease_brightness()

    # Removed handle_system_info as system_skills.system_info is not defined
    # def handle_system_info(params):
    #     return sys_skills.system_info()

    def handle_web_search(params):
        return web_skills.search_web(params.get("query", ""))

    def handle_get_weather(params):
        return web_skills.get_weather(params.get("location", ""))

    def handle_get_news(params):
        return web_skills.get_news(params.get("query", "latest"))

    def handle_get_forex_news(params):
        return web_skills.get_forex_news()

    def handle_search_wikipedia(params):
        return web_skills.search_wikipedia(params.get("topic", ""))

    def handle_get_crypto_prices(params):
        return web_skills.get_crypto_prices(params.get("symbols", "bitcoin"))

    def handle_get_twitter(params):
        return web_skills.get_twitter_posts(params.get("query", ""))

    def handle_get_reddit(params):
        return web_skills.get_reddit_posts(params.get("subreddit", ""))

    def handle_start_screen_recording(params):
        duration = params.get("duration", 0)
        filename = params.get("filename", "")
        return start_screen_recording(duration, filename)

    def handle_stop_screen_recording(params):
        return stop_screen_recording()

    def handle_blank_screen(params):
        return blank_screen()

    def handle_wake_screen(params):
        return wake_screen()

    def handle_lock_screen(params):
        return lock_screen()

    def handle_shutdown_system(params):
        minutes = params.get("minutes", 0)
        seconds = params.get("seconds", 0)
        return shutdown_system(minutes, seconds)

    def handle_restart_system(params):
        minutes = params.get("minutes", 0)
        seconds = params.get("seconds", 0)
        return restart_system(minutes, seconds)

    def handle_sleep_system(params):
        minutes = params.get("minutes", 0)
        seconds = params.get("seconds", 0)
        return sleep_system(minutes, seconds)

    def handle_hibernate_system(params):
        minutes = params.get("minutes", 0)
        seconds = params.get("seconds", 0)
        return hibernate_system(minutes, seconds)

    def handle_cancel_power_task(params):
        task_id = params.get("task_id", "")
        return cancel_power_task(task_id)

    INTENT_HANDLERS = {
        "get_volume": handle_get_volume,
        "set_volume": handle_set_volume,
        "increase_volume": handle_increase_volume,
        "decrease_volume": handle_decrease_volume,
        "mute_volume": handle_mute_volume,
        "unmute_volume": handle_unmute_volume,
        "launch_app": handle_launch_app,
        "take_screenshot": handle_take_screenshot,
        "get_time": handle_get_time,
        "get_date": handle_get_date,
        "tell_joke": handle_tell_joke,
        "calculate": handle_calculate,
        "get_brightness": handle_get_brightness,
        "set_brightness": handle_set_brightness,
        "increase_brightness": handle_increase_brightness,
        "decrease_brightness": handle_decrease_brightness,
        # "system_info": handle_system_info, # Removed
        "web_search": handle_web_search,
        "get_weather": handle_get_weather,
        "get_news": handle_get_news,
        "get_forex_news": handle_get_forex_news,
        "search_wikipedia": handle_search_wikipedia,
        "get_crypto_prices": handle_get_crypto_prices,
        "get_twitter": handle_get_twitter,
        "get_reddit": handle_get_reddit,
        "start_screen_recording": handle_start_screen_recording,
        "stop_screen_recording": handle_stop_screen_recording,
        "blank_screen": handle_blank_screen,
        "wake_screen": handle_wake_screen,
        "lock_screen": handle_lock_screen,
        "shutdown_system": handle_shutdown_system,
        "restart_system": handle_restart_system,
        "sleep_system": handle_sleep_system,
        "hibernate_system": handle_hibernate_system,
        "cancel_power_task": handle_cancel_power_task,
    }

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
                    handler = INTENT_HANDLERS.get(intent)
                    if handler:
                        response = handler(params)
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
