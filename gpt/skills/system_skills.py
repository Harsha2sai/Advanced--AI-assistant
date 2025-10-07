import os
import subprocess
import sys
import logging
from typing import Optional
import platform, subprocess # Moved from inside find_file

# Windows volume control
try:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    PYCAW_AVAILABLE = True
except ImportError:
    PYCAW_AVAILABLE = False

# Screenshot
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

# Brightness control
try:
    import screen_brightness_control as sbc
    SBC_AVAILABLE = True
except ImportError:
    SBC_AVAILABLE = False

logger = logging.getLogger(__name__)

# App launcher mapping for Windows
WINDOWS_APPS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe", 
    "paint": "mspaint.exe",
    "cmd": "cmd.exe",
    "command prompt": "cmd.exe",
    "powershell": "powershell.exe",
    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",
    "my files": "explorer.exe",
    "files": "explorer.exe",
    "task manager": "taskmgr.exe",
    "control panel": "control.exe",
    "settings": "ms-settings:",
    "chrome": "chrome.exe",
    "firefox": "firefox.exe",
    "edge": "msedge.exe",
    "spotify": "spotify.exe",
    "vs code": "code.exe",
    "visual studio code": "code.exe",
    "vscode": "code.exe",
    "discord": "discord.exe",
    "teams": "ms-teams:",
    "word": "winword.exe",
    "excel": "excel.exe",
    "powerpoint": "powerpnt.exe",
    "outlook": "outlook.exe",
}

# Volume Control Functions
def _get_volume_interface():
    """Get Windows volume interface using pycaw"""
    if not PYCAW_AVAILABLE:
        return None
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return cast(interface, POINTER(IAudioEndpointVolume))
    except Exception as e:
        logger.error(f"Failed to get volume interface: {e}")
        return None

def get_volume() -> str:
    """Get current volume level"""
    volume_interface = _get_volume_interface()
    if not volume_interface:
        return "Volume control not available"
    
    try:
        # Get volume as scalar (0.0 to 1.0)
        current_volume = volume_interface.GetMasterVolumeLevelScalar() # type: ignore
        volume_percent = int(round(current_volume * 100))
        logger.info(f"Current volume: {volume_percent}%")
        return f"Volume is {volume_percent}%"
    except Exception as e:
        logger.error(f"Failed to get volume: {e}")
        return f"Failed to get volume: {e}"

def set_volume(volume: int) -> str:
    """Set volume to specific level (0-100)"""
    volume_interface = _get_volume_interface()
    if not volume_interface:
        return "Volume control not available"
    
    try:
        volume = max(0, min(100, int(volume)))
        volume_scalar = volume / 100.0
        volume_interface.SetMasterVolumeLevelScalar(volume_scalar, None) # type: ignore
        logger.info(f"Volume set to {volume}%")
        return f"Volume set to {volume}%"
    except Exception as e:
        logger.error(f"Failed to set volume: {e}")
        return f"Failed to set volume: {e}"

def increase_volume(amount: int = 10) -> str:
    """Increase volume by specified amount"""
    volume_interface = _get_volume_interface()
    if not volume_interface:
        return "Volume control not available"
    
    try:
        current_volume = volume_interface.GetMasterVolumeLevelScalar() # type: ignore
        current_percent = int(round(current_volume * 100))
        new_percent = min(100, current_percent + amount)
        volume_interface.SetMasterVolumeLevelScalar(new_percent / 100.0, None) # type: ignore
        logger.info(f"Volume increased from {current_percent}% to {new_percent}%")
        return f"Volume increased to {new_percent}%"
    except Exception as e:
        logger.error(f"Failed to increase volume: {e}")
        return f"Failed to increase volume: {e}"

def decrease_volume(amount: int = 10) -> str:
    """Decrease volume by specified amount"""
    volume_interface = _get_volume_interface()
    if not volume_interface:
        return "Volume control not available"
    
    try:
        current_volume = volume_interface.GetMasterVolumeLevelScalar() # type: ignore
        current_percent = int(round(current_volume * 100))
        new_percent = max(0, current_percent - amount)
        volume_interface.SetMasterVolumeLevelScalar(new_percent / 100.0, None) # type: ignore
        logger.info(f"Volume decreased from {current_percent}% to {new_percent}%")
        return f"Volume decreased to {new_percent}%"
    except Exception as e:
        logger.error(f"Failed to decrease volume: {e}")
        return f"Failed to decrease volume: {e}"

def mute_volume() -> str:
    """Mute system volume"""
    volume_interface = _get_volume_interface()
    if not volume_interface:
        return "Volume control not available"
    
    try:
        volume_interface.SetMute(1, None) # type: ignore
        logger.info("Volume muted")
        return "Volume muted"
    except Exception as e:
        logger.error(f"Failed to mute: {e}")
        return f"Failed to mute: {e}"

def unmute_volume() -> str:
    """Unmute system volume"""
    volume_interface = _get_volume_interface()
    if not volume_interface:
        return "Volume control not available"
    
    try:
        volume_interface.SetMute(0, None) # type: ignore
        logger.info("Volume unmuted")
        return "Volume unmuted"
    except Exception as e:
        logger.error(f"Failed to unmute: {e}")
        return f"Failed to unmute: {e}"

# App Launcher
def launch_app(app_name: str, app_path: str) -> str:
    """Launch Windows application using a provided path"""
    if not app_path:
        return f"Sorry, I could not find an installed app matching '{app_name}'."
    
    # Add a return statement for the case where the app_path is not found
    # This addresses the Pylance error: "Function with declared return type 'str' must return value on all code paths"
    # The original code already had a return statement here, so no change is needed.
    # I will proceed to check the rest of the function for missing return statements.

    logger.info(f"Attempting to launch '{app_name}' from path: '{app_path}'")

    try:
        if sys.platform.startswith("win"):
            if os.path.isdir(app_path):
                os.startfile(app_path)
                logger.info(f"Opened folder for {app_name}: {app_path}")
                return f"Opened folder for {app_name}"
            elif os.path.isfile(app_path):
                subprocess.Popen([app_path])
                logger.info(f"Launched {app_name}: {app_path}")
                return f"Launched {app_name}"
            else:
                logger.warning(f"Found application path, but can't launch '{app_name}': Unknown path type for {app_path}")
                return f"Found application path, but can't launch '{app_name}'."
        elif sys.platform.startswith("darwin"):  # macOS
            subprocess.run(["open", app_path], check=True)
            logger.info(f"Launched {app_name} on macOS: {app_path}")
            return f"Launched {app_name}"
        elif sys.platform.startswith("linux"):  # Linux
            subprocess.run(["xdg-open", app_path], check=True)
            logger.info(f"Launched {app_name} on Linux: {app_path}")
            return f"Launched {app_name}"
        else:
            return "Cross-platform app launching not supported on this OS."
    except Exception as e:
        logger.error(f"Failed to launch '{app_name}' from '{app_path}': {str(e)}")
        return f"Failed to launch '{app_name}': {str(e)}"

# Screenshot
def take_screenshot(filename: Optional[str] = None) -> str:
    """Take a screenshot"""
    if not PYAUTOGUI_AVAILABLE:
        return "Screenshot functionality not available (pyautogui not installed)"
    
    try:
        if not filename:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else ".", exist_ok=True)
        
        # Take screenshot
        screenshot = pyautogui.screenshot()
        screenshot.save(filename)
        
        logger.info(f"Screenshot saved: {filename}")
        return f"Screenshot saved as {filename}"
        
    except Exception as e:
        logger.error(f"Screenshot failed: {e}")
        return f"Screenshot failed: {e}"

# Brightness Control  
def get_brightness() -> str:
    """Get current brightness level with guarded SBC/DDC/CI logic"""
    if not SBC_AVAILABLE:
        return "Brightness control not available on this device"
    try:
        mons = sbc.list_monitors()
        if not mons:
            return "Brightness control not supported on this display"
        brightness = sbc.get_brightness(display=0)
        if isinstance(brightness, list) and brightness:
            brightness = brightness[0]
        logger.info(f"Current brightness: {brightness}%")
        return f"Brightness is {brightness}%"
    except Exception as e:
        logger.warning(f"Brightness control not available: {e}")
        return "Brightness control not available on this device"

def set_brightness(brightness: int) -> str:
    """Set brightness level (0-100) with guarded SBC/DDC/CI logic"""
    if not SBC_AVAILABLE:
        return "Brightness control not available on this device"
    try:
        mons = sbc.list_monitors()
        if not mons:
            return "Brightness control not supported on this display"
        brightness = max(0, min(100, int(brightness)))
        sbc.set_brightness(brightness, display=0)
        logger.info(f"Brightness set to {brightness}%")
        return f"Brightness set to {brightness}%"
    except Exception as e:
        logger.warning(f"Brightness control not available: {e}")
        return "Brightness control not available on this device"

def increase_brightness() -> str:
    """Increase brightness by 10% with guarded SBC/DDC/CI logic"""
    if not SBC_AVAILABLE:
        return "Brightness control not available on this device"
    try:
        mons = sbc.list_monitors()
        if not mons:
            return "Brightness control not supported on this display"
        current = sbc.get_brightness(display=0)
        if isinstance(current, list) and current:
            current_val = int(current[0])
        elif isinstance(current, (int, float)):
            current_val = int(current)
        else:
            logger.error(f"Unexpected brightness type: {type(current)}")
            return "Failed to get brightness: Unexpected type"
        new_val = min(100, current_val + 10)
        sbc.set_brightness(new_val, display=0)
        logger.info(f"Brightness increased to {new_val}%")
        return f"Brightness increased to {new_val}%"
    except Exception as e:
        logger.warning(f"Brightness control not available: {e}")
        return "Brightness control not available on this device"

def decrease_brightness() -> str:
    """Decrease brightness by 10% with guarded SBC/DDC/CI logic"""
    if not SBC_AVAILABLE:
        return "Brightness control not available on this device"
    try:
        mons = sbc.list_monitors()
        if not mons:
            return "Brightness control not supported on this display"
        current = sbc.get_brightness(display=0)
        if isinstance(current, list) and current:
            current_val = int(current[0])
        elif isinstance(current, (int, float)):
            current_val = int(current)
        else:
            logger.error(f"Unexpected brightness type: {type(current)}")
            return "Failed to get brightness: Unexpected type"
        new_val = max(0, current_val - 10)
        sbc.set_brightness(new_val, display=0)
        logger.info(f"Brightness decreased to {new_val}%")
        return f"Brightness decreased to {new_val}%"
    except Exception as e:
        logger.warning(f"Brightness control not available: {e}")
        return "Brightness control not available on this device"

def find_file(name: str, folder: str) -> str:
    import os, fnmatch, pathlib # pathlib is not used, can be removed if not needed elsewhere
    known = {
        "downloads": os.path.join(os.path.expanduser("~"), "Downloads"),
        "download": os.path.join(os.path.expanduser("~"), "Downloads"),
        "documents": os.path.join(os.path.expanduser("~"), "Documents"),
        "desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
    }
    root = known.get(folder.lower(), os.path.expanduser("~"))
    if not os.path.isdir(root):
        return f"Folder not found: {root}"
    
    hits = []
    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            if name.lower() in f.lower() or fnmatch.fnmatch(f.lower(), f"*{name.lower()}*"):
                hits.append(os.path.join(dirpath, f))
                break # Stop after finding the first match in this directory

    if not hits:
        return f"No files matching '{name}' in {folder} ({root})"
    
    try:
        # Open the directory containing the first found file
        path_to_open = os.path.dirname(hits[0])
        system = platform.system()
        if system == "Windows":
            os.startfile(path_to_open)
        elif system == "Darwin": # macOS
            subprocess.Popen(["open", path_to_open])
        else: # Linux
            subprocess.Popen(["xdg-open", path_to_open])
        logger.info(f"Opened folder for '{name}': {path_to_open}")
        return f"Found '{name}' in {folder}. Opened folder: {path_to_open}"
    except Exception as e:
        logger.error(f"Failed to open folder for '{name}': {str(e)}")
        return f"Found '{name}' in {folder}, but failed to open its folder: {str(e)}"

# System Info
def system_info() -> str:
    """Get basic system information"""
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        return f"CPU usage: {cpu_percent}%, Memory usage: {memory.percent}%"
    except ImportError:
        return "System info not available (psutil not installed)"
    except Exception as e:
        return f"Failed to get system info: {e}"
