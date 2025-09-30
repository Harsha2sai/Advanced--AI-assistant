# gpt/skills/system_skills.py
# Windows-focused implementations. Requires:
# pip install psutil pyautogui pyperclip screen-brightness-control comtypes pycaw pillow

import os
import subprocess
import shutil
import json
from typing import List, Optional, Dict, Any

import psutil
import pyautogui
import pyperclip

# Brightness
try:
    import screen_brightness_control as sbc
except Exception:
    sbc = None

# Volume via Windows Core Audio (pycaw)
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

def launch_app(name_or_path: str) -> str:
    """
    Launch an application by friendly name or absolute path.
    Returns a human-readable status string.
    """
    # Known app map
    key = name_or_path.lower().strip()
    target = KNOWN_APPS.get(key, name_or_path)

    target = expand_env(target)

    # If it looks like a path and exists, run it directly
    if os.path.exists(target):
        try:
            subprocess.Popen([target], shell=True)
            return f"Launched {target}"
        except Exception as e:
            return f"Failed to launch: {e}"

    # Try to resolve via PATH or shell command
    try:
        subprocess.Popen([name_or_path], shell=True)
        return f"Launched {name_or_path}"
    except Exception:
        return f"App not found: {name_or_path}"

def open_website(url: str) -> str:
    try:
        subprocess.Popen(f'start "" "{url}"', shell=True)
        return f"Opened {url}"
    except Exception as e:
        return f"Failed to open website: {e}"

# -----------------------
# Brightness Control
# -----------------------
def set_brightness(percent: int) -> str:
    """
    Set brightness 0-100. Requires screen-brightness-control and supported hardware.
    """
    if sbc is None:
        return "Brightness control not available (library missing)."
    percent = max(0, min(100, int(percent)))
    try:
        sbc.set_brightness(percent)
        return f"Brightness set to {percent}%"
    except Exception as e:
        return f"Failed to set brightness: {e}"

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
def clipboard_copy(text: str) -> str:
    try:
        pyperclip.copy(text)
        return "Copied to clipboard."
    except Exception as e:
        return f"Clipboard copy failed: {e}"

def clipboard_paste() -> str:
    try:
        return pyperclip.paste()
    except Exception as e:
        return f"Clipboard paste failed: {e}"

# -----------------------
# File Manager (basic)
# -----------------------
def list_dir(path: str) -> List[str]:
    try:
        return os.listdir(path)
    except Exception as e:
        return [f"Error: {e}"]

def create_folder(path: str) -> str:
    try:
        os.makedirs(path, exist_ok=True)
        return f"Folder ensured at {path}"
    except Exception as e:
        return f"Create folder failed: {e}"

def create_file(path: str, content: str = "") -> str:
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File created: {path}"
    except Exception as e:
        return f"Create file failed: {e}"

def delete_path(path: str) -> str:
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
            return f"Folder deleted: {path}"
        elif os.path.isfile(path):
            os.remove(path)
            return f"File deleted: {path}"
        return "Path not found."
    except Exception as e:
        return f"Delete failed: {e}"

def open_file_explorer(path: str) -> str:
    try:
        subprocess.Popen(f'explorer "{path}"')
        return f"Opened Explorer at {path}"
    except Exception as e:
        return f"Open Explorer failed: {e}"

# -----------------------
# Volume Control (Windows)
# -----------------------
def _get_endpoint_volume():
    if not (AudioUtilities and IAudioEndpointVolume and CLSCTX_ALL and cast and POINTER):
        return None
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    return volume

def set_volume(percent: int) -> str:
    """
    Set master volume 0-100 using pycaw.
    """
    vol = _get_endpoint_volume()
    if vol is None:
        return "Volume control not available."
    percent = max(0, min(100, int(percent)))
    # pycaw uses scalar 0.0 - 1.0
    try:
        # pycaw's IAudioEndpointVolume pointer exposes methods via _methods_ attribute
        if not hasattr(vol, "SetMasterVolumeLevelScalar"):
            return "Volume control not available (SetMasterVolumeLevelScalar missing)."
        # Sometimes the method is available via __getattr__
        set_scalar = getattr(vol, "SetMasterVolumeLevelScalar", None)
        if set_scalar is None:
            return "Volume control not available (SetMasterVolumeLevelScalar missing)."
        set_scalar(percent / 100.0, None)
        return f"Volume set to {percent}%"
    except Exception as e:
        return f"Volume set failed: {e}"

def get_volume() -> str:
    vol = _get_endpoint_volume()
    if vol is None:
        return "Volume info not available."
    try:
        get_scalar = getattr(vol, "GetMasterVolumeLevelScalar", None)
        if get_scalar is None:
            return "Volume info not available (GetMasterVolumeLevelScalar missing)."
        scalar = get_scalar()
        return f"Volume is {int(round(scalar * 100))}%"
    except Exception as e:
        return f"Volume read failed: {e}"

def mute() -> str:
    vol = _get_endpoint_volume()
    if vol is None:
        return "Mute not available."
    try:
        set_mute = getattr(vol, "SetMute", None)
        if set_mute is None:
            return "Mute not available (SetMute missing)."
        set_mute(1, None)
        return "Muted."
    except Exception as e:
        return f"Mute failed: {e}"

def unmute() -> str:
    vol = _get_endpoint_volume()
    if vol is None:
        return "Unmute not available."
    try:
        set_mute = getattr(vol, "SetMute", None)
        if set_mute is None:
            return "Unmute not available (SetMute missing)."
        set_mute(0, None)
        return "Unmuted."
    except Exception as e:
        return f"Unmute failed: {e}"

# -----------------------
# System Info
# -----------------------
def system_info() -> Dict[str, Any]:
    try:
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        batt = None
        try:
            batt = psutil.sensors_battery()
        except Exception:
            batt = None
        net = psutil.net_if_stats()
        return {
            "cpu_percent": cpu,
            "memory_percent": mem.percent,
            "total_memory_gb": round(mem.total / (1024**3), 2),
            "battery_percent": getattr(batt, "percent", None),
            "plugged": getattr(batt, "power_plugged", None) if batt else None,
            "network": {k: v.isup for k, v in net.items()},
        }
    except Exception as e:
        return {"error": str(e)}

# -----------------------
# Screenshots
# -----------------------
def screenshot(path: str) -> str:
    """
    Save a screenshot PNG to path using pyautogui.
    """
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        img = pyautogui.screenshot()
        img.save(path)
        return f"Screenshot saved to {path}"
    except Exception as e:
        return f"Screenshot failed: {e}"
