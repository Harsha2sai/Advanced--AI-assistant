# gpt/skills/system_skills.py
# Windows-focused implementations. Requires:
# pip install psutil pyautogui pyperclip screen-brightness-control comtypes pycaw pillow

import os
import sys
import subprocess
import shutil
from typing import List, Dict, Any

import psutil
from gpt.skill_registry import skill

# --- Graceful GUI/OS-dependent imports ---
# These will be set to None if they fail to import, allowing the module
# to load in headless environments and non-Windows OS.

try:
    import pyautogui
except Exception:
    pyautogui = None

try:
    import pyperclip
except Exception:
    pyperclip = None

try:
    import screen_brightness_control as sbc
except Exception:
    sbc = None

try:
    from ctypes import POINTER, cast
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
except Exception:
    AudioUtilities = None
    IAudioEndpointVolume = None
    CLSCTX_ALL = None
    cast = None
    POINTER = None

# --- End Graceful Imports ---


# -----------------------
# App Launcher
# -----------------------
KNOWN_APPS = {
    # Add more mappings as needed
    "notepad": r"C:\Windows\System32\notepad.exe",
    "calculator": r"C:\Windows\System32\calc.exe",
    "paint": r"C:\Windows\System32\mspaint.exe",
    "cmd": r"C:\Windows\System32\cmd.exe",
    "powershell": r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
    "vscode": r"C:\Users\%USERNAME%\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
}

def expand_env(path: str) -> str:
    return os.path.expandvars(path)

@skill(
    patterns=[r"launch (?P<name_or_path>.+)", r"open (?P<name_or_path>.+)"],
    description="Launches an application by its name (e.g., 'notepad') or full path."
)
def launch_app(name_or_path: str) -> str:
    """
    Launch an application by friendly name or absolute path.
    Returns a human-readable status string.
    """
    # This is highly OS-dependent and likely won't work in a sandbox
    # but the logic is here for a user's machine.
    key = name_or_path.lower().strip()
    target = KNOWN_APPS.get(key, name_or_path)
    target = expand_env(target)

    try:
        # Use a more cross-platform friendly way to open things
        if sys.platform == "win32":
            os.startfile(target)
        elif sys.platform == "darwin": # macOS
            subprocess.Popen(["open", target])
        else: # Linux
            subprocess.Popen(["xdg-open", target])
        return f"Attempted to launch {name_or_path}"
    except Exception as e:
        return f"Failed to launch {name_or_path}: {e}"


@skill(
    patterns=[r"open website (?P<url>.+)"],
    description="Opens a website in the default browser."
)
def open_website(url: str) -> str:
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        if sys.platform == "win32":
            subprocess.Popen(f'start "" "{url}"', shell=True)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", url])
        else:
            subprocess.Popen(["xdg-open", url])
        return f"Attempted to open {url}"
    except Exception as e:
        return f"Failed to open website: {e}"

# -----------------------
# Brightness Control
# -----------------------
@skill(
    patterns=[r"set brightness to (?P<percent>\d+)%?"],
    description="Sets the screen brightness to a percentage (0-100)."
)
def set_brightness(percent: str) -> str:
    if sbc is None:
        return "Brightness control not available (library missing or unsupported OS)."
    try:
        level = max(0, min(100, int(percent)))
        sbc.set_brightness(level)
        return f"Brightness set to {level}%"
    except Exception as e:
        return f"Failed to set brightness: {e}"

@skill(
    patterns=[r"what is the brightness", r"get brightness"],
    description="Gets the current screen brightness level."
)
def get_brightness() -> str:
    if sbc is None:
        return "Brightness info not available."
    try:
        val = sbc.get_brightness(display=0)
        if isinstance(val, list) and val:
            val = val[0]
        return f"Brightness is {val}%"
    except Exception as e:
        return f"Failed to read brightness: {e}"

# -----------------------
# Clipboard
# -----------------------
@skill(
    patterns=[r"copy to clipboard (?P<text>.+)"],
    description="Copies the given text to the clipboard."
)
def clipboard_copy(text: str) -> str:
    if pyperclip is None:
        return "Clipboard functionality not available in this environment."
    try:
        pyperclip.copy(text)
        return "Copied to clipboard."
    except Exception as e:
        return f"Clipboard copy failed: {e}"

@skill(
    patterns=[r"what is on the clipboard", r"paste from clipboard"],
    description="Retrieves the current text from the clipboard."
)
def clipboard_paste() -> str:
    if pyperclip is None:
        return "Clipboard functionality not available in this environment."
    try:
        return pyperclip.paste()
    except Exception as e:
        return f"Clipboard paste failed: {e}"

# -----------------------
# File Manager (basic)
# -----------------------
@skill(
    patterns=[r"list files in (?P<path>.+)"],
    description="Lists all files and folders in a given directory path."
)
def list_dir(path: str) -> str:
    try:
        files = os.listdir(path)
        if not files:
            return f"The directory '{path}' is empty."
        return f"Contents of '{path}':\n" + "\n".join(files)
    except Exception as e:
        return f"Error listing directory: {e}"

@skill(
    patterns=[r"create folder at (?P<path>.+)"],
    description="Creates a new folder at the specified path."
)
def create_folder(path: str) -> str:
    try:
        os.makedirs(path, exist_ok=True)
        return f"Folder ensured at {path}"
    except Exception as e:
        return f"Create folder failed: {e}"

@skill(
    patterns=[r"create file at (?P<path>.+) with content (?P<content>.+)"],
    description="Creates a new file with specified content."
)
def create_file(path: str, content: str = "") -> str:
    try:
        dir_name = os.path.dirname(path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File created: {path}"
    except Exception as e:
        return f"Create file failed: {e}"

@skill(
    patterns=[r"delete (?P<path>.+)"],
    description="Deletes a file or folder at the specified path."
)
def delete_path(path: str) -> str:
    try:
        path = path.strip()
        if os.path.isdir(path):
            shutil.rmtree(path)
            return f"Folder deleted: {path}"
        elif os.path.isfile(path):
            os.remove(path)
            return f"File deleted: {path}"
        return "Path not found."
    except Exception as e:
        return f"Delete failed: {e}"

@skill(
    patterns=[r"open explorer at (?P<path>.+)"],
    description="Opens the File Explorer to a specific path."
)
def open_file_explorer(path: str) -> str:
    try:
        abs_path = os.path.abspath(path)
        if sys.platform == "win32":
            subprocess.Popen(['explorer', abs_path])
        elif sys.platform == "darwin":
            subprocess.Popen(['open', abs_path])
        else:
            subprocess.Popen(['xdg-open', abs_path])
        return f"Opened Explorer at {path}"
    except Exception as e:
        return f"Open Explorer failed: {e}"

# -----------------------
# Volume Control (Windows)
# -----------------------
def _get_endpoint_volume():
    if not (AudioUtilities and IAudioEndpointVolume and CLSCTX_ALL and cast and POINTER):
        return None
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return cast(interface, POINTER(IAudioEndpointVolume))
    except Exception:
        return None

@skill(
    patterns=[r"set volume to (?P<percent>\d+)%?"],
    description="Sets the master system volume to a percentage (0-100)."
)
def set_volume(percent: str) -> str:
    vol = _get_endpoint_volume()
    if vol is None:
        return "Volume control not available (unsupported OS or library missing)."
    try:
        level = max(0, min(100, int(percent)))
        vol.SetMasterVolumeLevelScalar(level / 100.0, None)
        return f"Volume set to {level}%"
    except Exception as e:
        return f"Volume set failed: {e}"

@skill(
    patterns=[r"what is the volume", r"get volume"],
    description="Gets the current master system volume."
)
def get_volume() -> str:
    vol = _get_endpoint_volume()
    if vol is None:
        return "Volume info not available."
    try:
        scalar = vol.GetMasterVolumeLevelScalar()
        return f"Volume is {int(round(scalar * 100))}%"
    except Exception as e:
        return f"Volume read failed: {e}"

@skill(patterns=[r"mute volume", r"mute"], description="Mutes the system volume.")
def mute() -> str:
    vol = _get_endpoint_volume()
    if vol is None: return "Mute not available."
    try:
        vol.SetMute(1, None)
        return "Muted."
    except Exception as e:
        return f"Mute failed: {e}"

@skill(patterns=[r"unmute volume", r"unmute"], description="Unmutes the system volume.")
def unmute() -> str:
    vol = _get_endpoint_volume()
    if vol is None: return "Unmute not available."
    try:
        vol.SetMute(0, None)
        return "Unmuted."
    except Exception as e:
        return f"Unmute failed: {e}"

# -----------------------
# System Info
# -----------------------
@skill(
    patterns=[r"get system info", r"system status"],
    description="Retrieves system information like CPU, memory, and battery."
)
def system_info() -> str:
    try:
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        batt_str = "Not available"
        try:
            batt = psutil.sensors_battery()
            if batt:
                batt_str = f"{batt.percent}%" + (" (Plugged In)" if batt.power_plugged else "")
        except Exception:
            pass

        return f"CPU: {cpu}%, Memory: {mem.percent}%, Battery: {batt_str}"
    except Exception as e:
        return f"Error getting system info: {e}"

# -----------------------
# Screenshots
# -----------------------
@skill(
    patterns=[r"take a screenshot and save to (?P<path>.+)"],
    description="Saves a screenshot to the specified file path."
)
def screenshot(path: str) -> str:
    if pyautogui is None:
        return "Screenshot functionality not available in this environment."
    try:
        dir_name = os.path.dirname(path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        img = pyautogui.screenshot()
        img.save(path)
        return f"Screenshot saved to {path}"
    except Exception as e:
        return f"Screenshot failed: {e}"