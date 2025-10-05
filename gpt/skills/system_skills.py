import os
import subprocess
import logging
from typing import Optional

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

    logger.info(f"Attempting to launch '{app_name}' from path: '{app_path}'")

    try:
        if os.path.isdir(app_path):
            # If directory, try to find executable inside common folders or just open folder
            # For now open folder
            os.startfile(app_path)
            logger.info(f"Opened folder for {app_name}: {app_path}")
            return f"Opened folder for {app_name}"
        elif os.path.isfile(app_path):
            # Launch executable file
            subprocess.Popen([app_path], shell=True)
            logger.info(f"Launched {app_name}: {app_path}")
            return f"Launched {app_name}"
        else:
            # Unknown path type
            logger.warning(f"Found application path, but can't launch '{app_name}': Unknown path type for {app_path}")
            return f"Found application path, but can't launch '{app_name}'."
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
    """Get current brightness level"""
    if not SBC_AVAILABLE:
        return "Brightness control not available"
    
    try:
        brightness = sbc.get_brightness(display=0)
        if isinstance(brightness, list) and brightness:
            brightness = brightness[0]
        logger.info(f"Current brightness: {brightness}%")
        return f"Brightness is {brightness}%"
    except Exception as e:
        logger.error(f"Failed to get brightness: {e}")
        return f"Failed to get brightness: {e}"

def set_brightness(brightness: int) -> str:
    """Set brightness level (0-100)"""
    if not SBC_AVAILABLE:
        return "Brightness control not available"
    
    try:
        brightness = max(0, min(100, int(brightness)))
        sbc.set_brightness(brightness, display=0)
        logger.info(f"Brightness set to {brightness}%")
        return f"Brightness set to {brightness}%"
    except Exception as e:
        logger.error(f"Failed to set brightness: {e}")
        return f"Failed to set brightness: {e}"

def increase_brightness() -> str:
    """Increase brightness by 10%"""
    if not SBC_AVAILABLE:
        return "Brightness control not available"
    
    try:
        current_raw = sbc.get_brightness(display=0)
        current_val: int
        if isinstance(current_raw, list) and current_raw:
            current_val = int(current_raw[0])
        elif isinstance(current_raw, (int, float)):
            current_val = int(current_raw)
        else:
            # Fallback or error handling if brightness is neither int, float, nor list
            logger.error(f"Unexpected brightness type: {type(current_raw)}")
            return "Failed to get brightness: Unexpected type"

        new_brightness = min(100, current_val + 10)
        sbc.set_brightness(new_brightness, display=0)
        logger.info(f"Brightness increased to {new_brightness}%")
        return f"Brightness increased to {new_brightness}%"
    except Exception as e:
        logger.error(f"Failed to increase brightness: {e}")
        return f"Failed to increase brightness: {e}"

def decrease_brightness() -> str:
    """Decrease brightness by 10%"""  
    if not SBC_AVAILABLE:
        return "Brightness control not available"
    
    try:
        current_raw = sbc.get_brightness(display=0)
        current_val: int
        if isinstance(current_raw, list) and current_raw:
            current_val = int(current_raw[0])
        elif isinstance(current_raw, (int, float)):
            current_val = int(current_raw)
        else:
            # Fallback or error handling if brightness is neither int, float, nor list
            logger.error(f"Unexpected brightness type: {type(current_raw)}")
            return "Failed to get brightness: Unexpected type"
        new_brightness = max(0, current_val - 10)
        sbc.set_brightness(new_brightness, display=0)
        logger.info(f"Brightness decreased to {new_brightness}%")
        return f"Brightness decreased to {new_brightness}%"
    except Exception as e:
        logger.error(f"Failed to decrease brightness: {e}")
        return f"Failed to decrease brightness: {e}"

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
