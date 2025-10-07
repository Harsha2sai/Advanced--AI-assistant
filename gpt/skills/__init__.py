# main/skills/__init__.py

from .common import *            # tell_joke, calculate, current_time, etc.
from .system_skills import *     # get_volume, set_volume, launch_app, ...
from .web_services import (      # import new web functions
    search_web, get_weather, get_news,
    get_twitter_posts, get_reddit_posts,
    get_github_trending, get_forex_news,
    search_wikipedia, get_crypto_prices
)
from .advanced_system_skills import ( # import advanced system functions
    start_screen_recording, stop_screen_recording,
    blank_screen, wake_screen, lock_screen,
    shutdown_system, restart_system, sleep_system,
    hibernate_system, cancel_power_task
)

__all__ = [
    # common
    "tell_joke","calculate","current_time","current_date",
    "capture_screenshot","play_music","pause_music","stop_music",
    "set_timer","add_todo","list_todos","complete_todo",
    # system_skills
    "get_volume","set_volume","increase_volume","decrease_volume",
    "mute_volume","unmute_volume","launch_app","take_screenshot",
    "get_brightness","set_brightness","increase_brightness","decrease_brightness",
    "system_info",
    # web_services
    "search_web","get_weather","get_news",
    "get_twitter_posts","get_reddit_posts","get_github_trending",
    "get_forex_news","search_wikipedia","get_crypto_prices",
    # advanced_system_skills
    "start_screen_recording", "stop_screen_recording",
    "blank_screen", "wake_screen", "lock_screen",
    "shutdown_system", "restart_system", "sleep_system",
    "hibernate_system", "cancel_power_task"
]
