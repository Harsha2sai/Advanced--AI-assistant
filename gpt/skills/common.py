# gpt/skills/common.py

import time
import datetime
import json
import os
import random
import threading
import sympy
from gpt.skill_registry import skill

# Graceful import for vlc
try:
    import vlc
except (ImportError, OSError):
    vlc = None

# --- Fun ---
JOKES = [
    "Why do programmers prefer dark mode? Because light attracts bugs!",
    "There are 10 types of people: those who understand binary and those who don’t."
]

@skill(
    patterns=[r"tell me a joke", r"say a joke"],
    description="Tells a random programming joke."
)
def tell_joke() -> str:
    """Return a random programming joke."""
    return random.choice(JOKES)


# --- Music Control ---
_player = None

def init_music_player():
    """Initializes the VLC player instance if available."""
    global _player
    if vlc and _player is None:
        try:
            _player = vlc.MediaPlayer()
        except Exception as e:
            print(f"Failed to initialize VLC MediaPlayer: {e}")
            _player = None

@skill(
    patterns=[r"play music from (?P<path>.+)", r"play (?P<path>.+)"],
    description="Plays a media file from a given path. Requires VLC."
)
def play_music(path: str) -> str:
    """Play a media file."""
    if not vlc:
        return "Music playback is not available (VLC library is missing or could not be loaded)."

    init_music_player()

    if _player is None:
        return "Music player could not be initialized."

    if os.path.isfile(path):
        _player.set_mrl(path)
        _player.play()
        return f"Playing {os.path.basename(path)}"
    return "Error: File not found or is not a valid media file."

@skill(
    patterns=[r"pause music", r"pause playback"],
    description="Pauses the currently playing music."
)
def pause_music() -> str:
    """Pause currently playing media."""
    if not vlc or _player is None:
        return "Music player is not available."
    if _player.is_playing():
        _player.pause()
        return "Music paused."
    return "No music is playing."

@skill(
    patterns=[r"stop music", r"stop playback"],
    description="Stops the music playback."
)
def stop_music() -> str:
    """Stop playback."""
    if not vlc or _player is None:
        return "Music player is not available."
    _player.stop()
    return "Music stopped."


# --- Date & Time ---
@skill(
    patterns=[r"what is the date", r"current date"],
    description="Gets the current date."
)
def current_date() -> str:
    """Return current date as YYYY-MM-DD."""
    return datetime.date.today().isoformat()

@skill(
    patterns=[r"what time is it", r"current time"],
    description="Gets the current time."
)
def current_time() -> str:
    """Return current time as HH:MM:SS."""
    now = datetime.datetime.now()
    return now.strftime("%H:%M:%S")


# --- Calculator ---
@skill(
    patterns=[
        r"calculate (?P<expr>.+)",
        # This pattern requires at least one digit to avoid capturing general questions.
        r"what is (?P<expr>.*\d.*)"
    ],
    description="Evaluates a mathematical expression."
)
def calculate(expr: str) -> str:
    """Evaluate a math expression using Sympy."""
    try:
        if any(x in expr for x in ['import', 'eval', 'exec']):
            return "Error: Expression contains forbidden keywords."
        result = sympy.simplify(expr)
        return str(result)
    except Exception as e:
        return f"Error: {e}"


# --- Stopwatch ---
_stopwatch_start = None
_stopwatch_laps = []

@skill(patterns=[r"start stopwatch"], description="Starts a stopwatch.")
def stopwatch_start() -> str:
    global _stopwatch_start, _stopwatch_laps
    _stopwatch_start = time.time()
    _stopwatch_laps = []
    return "Stopwatch started."

@skill(patterns=[r"stopwatch lap", r"lap"], description="Records a lap time on the stopwatch.")
def stopwatch_lap() -> str:
    if _stopwatch_start is None:
        return "Stopwatch not started."
    lap_time = time.time() - _stopwatch_start
    _stopwatch_laps.append(lap_time)
    return f"Lap {len(_stopwatch_laps)}: {lap_time:.2f}s"

@skill(patterns=[r"stop stopwatch"], description="Stops the stopwatch.")
def stopwatch_stop() -> str:
    global _stopwatch_start
    if _stopwatch_start is None:
        return "Stopwatch not started."
    total = time.time() - _stopwatch_start
    _stopwatch_start = None
    return f"Stopwatch stopped at {total:.2f}s"


# --- Timer ---
_timers = {}

@skill(
    patterns=[r"set a timer for (?P<amount>\d+) (?P<unit>second|minute|hour)s?"],
    description="Sets a timer for a specified duration (e.g., 'set a timer for 5 minutes')."
)
def set_timer(amount: str, unit: str) -> str:
    """Set a named timer based on a textual command."""
    try:
        seconds = int(amount)
        multiplier = {"second": 1, "minute": 60, "hour": 3600}[unit.lower()]
        total_seconds = seconds * multiplier
        timer_name = f"timer_{int(time.time())}"

        def _timeout():
            print(f"⏰ Timer '{timer_name}' finished!")

        t = threading.Timer(total_seconds, _timeout)
        t.start()
        _timers[timer_name] = t
        return f"Timer set for {amount} {unit}s."
    except (ValueError, KeyError) as e:
        return f"Error setting timer: Invalid amount or unit. {e}"

@skill(
    patterns=[r"cancel timer (?P<name>\w+)"],
    description="Cancels a specific named timer."
)
def cancel_timer(name: str) -> str:
    """Cancel a named timer."""
    t = _timers.pop(name, None)
    if t:
        t.cancel()
        return f"Timer '{name}' canceled."
    return f"No active timer named '{name}'."


# --- To-Do List ---
TODO_FILE = os.path.join(os.path.dirname(__file__), "todo.json")

@skill(
    patterns=[r"add to-do (?P<item>.+)", r"add (?P<item>.+) to my to-do list"],
    description="Adds an item to the to-do list."
)
def add_todo(item: str) -> str:
    """Add an item to the to-do list."""
    todos = []
    if os.path.exists(TODO_FILE):
        try:
            with open(TODO_FILE, 'r') as f:
                todos = json.load(f)
        except json.JSONDecodeError:
            pass
    todos.append({"task": item, "done": False})
    with open(TODO_FILE, "w") as f:
        json.dump(todos, f, indent=2)
    return f"Added to-do: {item}"

@skill(
    patterns=[r"list to-dos", r"show my to-dos"],
    description="Lists all items in the to-do list."
)
def list_todos() -> str:
    """List all to-do items."""
    if not os.path.exists(TODO_FILE):
        return "No to-dos found."
    try:
        with open(TODO_FILE, 'r') as f:
            todos = json.load(f)
        if not todos:
            return "Your to-do list is empty."
        lines = [f"{idx+1}. [{'x' if t['done'] else ' '}] {t['task']}"
                 for idx, t in enumerate(todos)]
        return "\n".join(lines)
    except (json.JSONDecodeError, FileNotFoundError):
        return "No to-dos found or the list is corrupt."

@skill(
    patterns=[r"complete to-do (?P<index>\d+)", r"mark to-do (?P<index>\d+) as done"],
    description="Marks a to-do item as completed by its number."
)
def complete_todo(index: str) -> str:
    """Mark a to-do item as done."""
    if not os.path.exists(TODO_FILE):
        return "No to-dos found."
    try:
        idx = int(index)
        with open(TODO_FILE, 'r') as f:
            todos = json.load(f)
        if 1 <= idx <= len(todos):
            todos[idx-1]["done"] = True
            with open(TODO_FILE, "w") as f:
                json.dump(todos, f, indent=2)
            return f"Completed to-do #{idx}."
        return f"Invalid to-do number: {idx}"
    except (ValueError, json.JSONDecodeError, FileNotFoundError):
        return "Error completing to-do. Please check the index or the to-do file."