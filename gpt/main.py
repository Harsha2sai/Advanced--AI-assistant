# main.py (terminal-only)

import time

from wakeword import listen_for_wakeword
from stt import speech_to_text
from tts import speak
from chat_engine import ChatEngine

IDLE_TIMEOUT = 15 * 60  # 15 minutes

def run_voice_assistant():
    print("Sara is ready! Say 'Sara' to wake me up.")  # wake word prompt [file:1]
    active_session = False
    last_interaction = 0
    chat_engine = ChatEngine()

    while True:
        if not active_session:
            print("👂 Waiting for wake word...")  # waiting state [file:1]
            listen_for_wakeword()  # blocks until detected [file:8]
            speak("Yes, I'm listening.")  # TTS confirmation [file:5]
            active_session = True
            last_interaction = time.time()
            chat_engine.reset()
            continue

        print("🎤 Listening for command...")  # STT prompt [file:1]
        query = speech_to_text()  # mic capture + Google STT [file:7]

        if query:
            print(f"User: {query}")  # echo user input [file:1]
            result = chat_engine.ask(query)  # call LLM [file:4]
            print(f"Sara (short): {result['short']}")  # short answer [file:1]
            if result.get("extra"):
                print(f"Sara (extra):\n{result['extra']}")  # extra details [file:1]
            speak(result["short"])  # TTS speak response [file:5]
            last_interaction = time.time()
        else:
            # If idle for too long, end the active session
            if time.time() - last_interaction > IDLE_TIMEOUT:
                speak("I'll go to sleep now. Say Sara to wake me again.")  # TTS idle exit [file:1]
                active_session = False
                chat_engine.reset()

        time.sleep(0.1)  # small loop yield [file:1]

if __name__ == '__main__':
    try:
        run_voice_assistant()  # run in terminal only [file:1]
    except KeyboardInterrupt:
        print("\n👋 Exiting Sara...")  # graceful exit [file:1]
    except Exception as e:
        print(f"An unexpected error occurred: {e}")  # error log [file:1]
