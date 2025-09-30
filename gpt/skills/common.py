# gpt/skills/common.py

import time
import datetime
import json
import os
import random
import threading
import sympy
import vlc  # pip install python-vlc

# --- Fun ---
JOKES = [
    "Why do programmers prefer dark mode? Because light attracts bugs!",
    "There are 10 types of people: those who understand binary and those who don’t."
]

def tell_joke() -> str:
    """Return a random programming joke."""
    return random.choice(JOKES)


# --- Music Control ---
_player = None

def init_music_player():
    global _player
    if _player is None:
        _player = vlc.MediaPlayer()

def play_music(path: str) -> str:
    """Play a media file."""
    init_music_player()
    if _player is not None:
        _player.set_mrl(path)
        _player.play()
        return f"Playing {os.path.basename(path)}"
    return "Music player could not be initialized."

def pause_music() -> str:
    """Pause currently playing media."""
    if _player and _player.is_playing():
        _player.pause()
        return "Music paused."
    return "No music is playing."

def stop_music() -> str:
    """Stop playback."""
    if _player:
        _player.stop()
        return "Music stopped."
    return "Player not initialized."


# --- Media (Screenshot stub) ---
def capture_screenshot(path: str) -> str:
    """Stub: capture screenshot to given path."""
    # Implementation placeholder; integrate PIL.ImageGrab or pyscreenshot
    return f"Screenshot saved to {path}"


# --- Calculator ---
def calculate(expr: str) -> str:
    """Evaluate a math expression using Sympy."""
    try:
        result = sympy.simplify(expr)
        return str(result)
    except Exception as e:
        return f"Error: {e}"


# --- Date & Time ---
def current_date() -> str:
    """Return current date as YYYY-MM-DD."""
    return datetime.date.today().isoformat()

def current_time() -> str:
    """Return current time as HH:MM:SS."""
    now = datetime.datetime.now()
    return now.strftime("%H:%M:%S")


# --- Stopwatch ---
_stopwatch_start = None
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
    return f"Lap {_stopwatch_laps.__len__()}: {lap_time:.2f}s"

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
    """Set a named timer."""
    def _timeout():
        print(f"⏰ Timer '{name}' finished!")
    t = threading.Timer(seconds, _timeout)
    t.start()
    _timers[name] = t
    return f"Timer '{name}' set for {seconds} seconds."

def cancel_timer(name: str) -> str:
    """Cancel a named timer."""
    t = _timers.pop(name, None)
    if t:
        t.cancel()
        return f"Timer '{name}' canceled."
    return f"No active timer named '{name}'."


# --- To-Do List ---
TODO_FILE = os.path.join(os.path.dirname(__file__), "todo.json")

def add_todo(item: str) -> str:
    """Add an item to the to-do list."""
    todos = []
    if os.path.exists(TODO_FILE):
        todos = json.load(open(TODO_FILE))
    todos.append({"task": item, "done": False})
    json.dump(todos, open(TODO_FILE, "w"), indent=2)
    return f"Added to-do: {item}"

def list_todos() -> str:
    """List all to-do items."""
    if not os.path.exists(TODO_FILE):
        return "No to-dos found."
    todos = json.load(open(TODO_FILE))
    lines = [f"{idx+1}. [{'x' if t['done'] else ' '}] {t['task']}" 
             for idx, t in enumerate(todos)]
    return "\n".join(lines)

def complete_todo(index: int) -> str:
    """Mark a to-do item as done."""
    if not os.path.exists(TODO_FILE):
        return "No to-dos found."
    todos = json.load(open(TODO_FILE))
    if 1 <= index <= len(todos):
        todos[index-1]["done"] = True
        json.dump(todos, open(TODO_FILE, "w"), indent=2)
        return f"Completed to-do #{index}."
    return f"Invalid to-do number: {index}"
