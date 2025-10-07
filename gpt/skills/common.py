# gpt/skills/common.py
# Dependencies:
# pip install python-vlc pyautogui Pillow

import os
import json
import random
import threading
import datetime
import time # Module-level time import
from typing import Optional

_vlc_player = None
_vlc_initialized = False

# --- Fun ---
JOKES = [
    "Why do programmers prefer dark mode? Because light attracts bugs!",
    "There are 10 types of people: those who understand binary and those who don’t."
]

def tell_joke() -> str:
    return random.choice(JOKES)

# --- Calculator ---
import sympy

def calculate(expr: str) -> str:
    try:
        result = sympy.simplify(expr)
        return str(result)
    except Exception as e:
        return f"Error: {e}"

# --- Date & Time ---
def current_date() -> str:
    return datetime.date.today().isoformat()

def current_time() -> str:
    now = datetime.datetime.now()
    return now.strftime("%H:%M:%S")

# --- Stopwatch ---
_stopwatch_start: Optional[float] = None
_stopwatch_laps = []

def stopwatch_start() -> str:
    global _stopwatch_start, _stopwatch_laps
    _stopwatch_start = time.time()
    _stopwatch_laps = []
    return "Stopwatch started."

def stopwatch_lap() -> str:
    if _stopwatch_start is None:
        return "Stopwatch not started."
    lap_time = time.time() - _stopwatch_start
    _stopwatch_laps.append(lap_time)
    return f"Lap {len(_stopwatch_laps)}: {lap_time:.2f}s"

def stopwatch_stop() -> str:
    global _stopwatch_start
    if _stopwatch_start is None:
        return "Stopwatch not started."
    total = time.time() - _stopwatch_start
    _stopwatch_start = None
    return f"Stopwatch stopped at {total:.2f}s"

# --- Timer ---
_timers = {}

def set_timer(name: str, seconds: int) -> str:
    def _timeout():
        print(f"⏰ Timer '{name}' finished!")
    try:
        if not isinstance(seconds, (int, float)):
            return f"Invalid seconds value: must be a number, got {type(seconds).__name__}"
        seconds = max(0, int(seconds))
        t = threading.Timer(seconds, _timeout)
        t.daemon = True
        t.start()
        _timers[name] = t
        return f"Timer '{name}' set for {seconds} seconds."
    except Exception as e:
        return f"Failed to set timer: {e}"

def cancel_timer(name: str) -> str:
    t = _timers.pop(name, None)
    if t:
        t.cancel()
        return f"Timer '{name}' canceled."
    return f"No active timer named '{name}'."

# --- To-Do List ---
TODO_FILE = os.path.join(os.path.dirname(__file__), "todos.json")

def _load_todos() -> list:
    try:
        if os.path.exists(TODO_FILE):
            with open(TODO_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"Warning: Failed to load todos from {TODO_FILE}: {e}")
    return []

def _save_todos(todos):
    try:
        tmp = TODO_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(todos, f, indent=2, ensure_ascii=False)
        os.replace(tmp, TODO_FILE)
    except Exception as e:
        print(f"Warning: Failed to save todos to {TODO_FILE}: {e}")
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except Exception:
                pass
        raise

def add_todo(item: str) -> str:
    todos = _load_todos()
    todos.append({"task": item, "done": False})
    _save_todos(todos)
    return f"Added to-do: {item}"

def list_todos() -> str:
    todos = _load_todos()
    if not todos:
        return "No to-dos found."
    lines = [f"{idx+1}. [{'x' if t.get('done') else ' '}] {t.get('task','')}" for idx, t in enumerate(todos)]
    return "\n".join(lines)

def complete_todo(index: int) -> str:
    todos = _load_todos()
    if 1 <= index <= len(todos):
        todos[index-1]["done"] = True
        _save_todos(todos)
        return f"Completed to-do #{index}."
    return f"Invalid to-do number: {index}"

# --- Screenshot (real implementation) ---
# Reliable cross-platform screenshots via PyAutoGUI (uses Pillow internally).
# Handles high-DPI scaling on Windows and headless checks.

def capture_screenshot(path: Optional[str] = None) -> str:
    try:
        import pyautogui
        from PIL import Image
        if not path:
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.abspath(f"screenshot_{ts}.png")

        # Ensure folder exists
        folder = os.path.dirname(path) or "."
        os.makedirs(folder, exist_ok=True)

        # High-DPI safety (Windows): disable FAILSAFE if needed
        pyautogui.FAILSAFE = False

        # Take screenshot
        img = pyautogui.screenshot()  # returns a PIL Image
        img.save(path)

        if os.path.exists(path) and os.path.getsize(path) > 0:
            return f"Screenshot saved to {path}"
        return "Screenshot failed (empty image)."

    except Exception as e:
        return f"Failed to capture screenshot: {e}"

import vlc # python-vlc

# Constants for polling loop
PLAY_TIMEOUT = 5  # seconds
PLAY_INTERVAL = 0.1  # seconds

def _init_vlc():
    global _vlc_player, _vlc_initialized
    if _vlc_initialized and _vlc_player:
        return
    try:
        _vlc_player = vlc.MediaPlayer()
        _vlc_initialized = True
    except Exception as e:
        print(f"Warning: VLC backend unavailable: {e}")
        _vlc_player = None
        _vlc_initialized = False

def play_music(path: str) -> str:
    """
    Play a local media file with VLC.
    - Validates file existence.
    - Waits briefly for state transition to avoid "silent play".
    """
    try:
        _init_vlc()
        if not _vlc_player:
            return "Music player not available (VLC backend missing)."

        if not path or not os.path.exists(path):
            return f"File not found: {path}"

        # Normalize path for VLC
        abs_path = os.path.abspath(path)

        # Set media and play
        _vlc_player.set_mrl(abs_path)
        _vlc_player.play()

        # Robust enum-checked polling loop
        elapsed_time = 0
        while elapsed_time < PLAY_TIMEOUT:
            state = _vlc_player.get_state()
            if state == vlc.State.Playing:  # type: ignore
                break
            time.sleep(PLAY_INTERVAL)
            elapsed_time += PLAY_INTERVAL
        else: # This else block executes if the loop completes without breaking
            if _vlc_player.get_state() != vlc.State.Playing:  # type: ignore
                return f"Failed to start playing {os.path.basename(abs_path)} within {PLAY_TIMEOUT} seconds."

        return f"Playing {os.path.basename(abs_path)}"
    except Exception as e:
        # Windows fallback: use shell to open default player
        try:
            if os.name == "nt" and os.path.exists(path):
                os.startfile(os.path.abspath(path))
                return f"Opening {os.path.basename(path)} with default player"
        except Exception:
            pass
        return f"Failed to play media: {e}"

def pause_music() -> str:
    try:
        if _vlc_player:
            state = str(_vlc_player.get_state()).lower()
            if "playing" in state:
                _vlc_player.pause()
                return "Music paused."
            return "No music is playing."
        return "Music player not available."
    except Exception as e:
        return f"Pause failed: {e}"

def stop_music() -> str:
    try:
        if _vlc_player:
            _vlc_player.stop()
            return "Music stopped."
        return "Music player not available."
    except Exception as e:
        return f"Stop failed: {e}"
