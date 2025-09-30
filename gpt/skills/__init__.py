# gpt/skills/__init__.py
"""
Skills package initializer.

Exports skill functions from individual modules so that
import_skills.import_all_skills() can load them into the runtime.
Add new skill modules and update __all__ as you expand.
"""

# Optional: guard imports so missing optional deps don't crash the package
def _safe_import(module_name, names):
    try:
        mod = __import__(module_name, fromlist=names)
        return {name: getattr(mod, name) for name in names if hasattr(mod, name)}
    except Exception:
        return {}

# Common/basic skills (if you created common.py earlier)
_common = _safe_import("gpt.skills.common", [
    "tell_joke", "play_music", "pause_music", "stop_music",
    "calculate", "current_time", "current_date",
    "stopwatch_start", "stopwatch_lap", "stopwatch_stop",
    "set_timer", "cancel_timer",
    "add_todo", "list_todos", "complete_todo",
    "capture_screenshot",
])

# System skills (Windows-focused)
_system = _safe_import("gpt.skills.system_skills", [
    "launch_app", "open_website",
    "set_brightness", "get_brightness",
    "clipboard_copy", "clipboard_paste",
    "list_dir", "create_folder", "create_file", "delete_path", "open_file_explorer",
    "set_volume", "get_volume", "mute", "unmute",
    "system_info", "screenshot",
])

# Email skills (Gmail manager)
_email = _safe_import("gpt.skills.email_manager", [
    "GmailManager",
])

# Merge exports
globals().update(_common)
globals().update(_system)
globals().update(_email)

__all__ = [
    # Common/basic skills
    "tell_joke", "play_music", "pause_music", "stop_music",
    "calculate", "current_time", "current_date",
    "stopwatch_start", "stopwatch_lap", "stopwatch_stop",
    "set_timer", "cancel_timer",
    "add_todo", "list_todos", "complete_todo",
    "capture_screenshot",
    # System skills
    "launch_app", "open_website",
    "set_brightness", "get_brightness",
    "clipboard_copy", "clipboard_paste",
    "list_dir", "create_folder", "create_file", "delete_path", "open_file_explorer",
    "set_volume", "get_volume", "mute", "unmute",
    "system_info", "screenshot",
    # Email skills
    "GmailManager",
]
