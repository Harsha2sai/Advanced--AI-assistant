import re
from typing import Tuple, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class IntentParser:
    def __init__(self):
        # Order matters: more specific patterns first
        self.patterns = [
            # More flexible screen control patterns
            (re.compile(r'\b(make|turn)\s+(?:the\s+)?screen\s+(black|blank|dark|off)\b', re.I), 
             'blank_screen', lambda m: {}),
            (re.compile(r'\b(blank|turn\s+off|black|power\s+off)\s+(?:the\s+)?screen\b', re.I), 
             'blank_screen', lambda m: {}),
            (re.compile(r'\bpower\s+off\s+(?:the\s+)?screen\b', re.I), 
             'blank_screen', lambda m: {}),
            (re.compile(r'\benter\s+screen\s+saver\s+mode\b', re.I), 
             'blank_screen', lambda m: {}),
            (re.compile(r'\bscreen\s+saver\b', re.I), 
             'blank_screen', lambda m: {}),
            (re.compile(r'\bdisplay\s+saving\b', re.I), 
             'blank_screen', lambda m: {}),
            (re.compile(r'\bsave\s+power\s+display\b', re.I), 
             'blank_screen', lambda m: {}),
            # Wake screen patterns
            (re.compile(r'\b(wake|turn\s+on|activate)\s+(?:the\s+)?screen\b', re.I), 
             'wake_screen', lambda m: {}),
            # Lock screen patterns
            (re.compile(r'\block\s+(?:the\s+)?screen\b', re.I), 
             'lock_screen', lambda m: {}),
            # Screen recording patterns
            (re.compile(r'\b(start|begin)\s+screen\s+recording\b', re.I), 
             'start_screen_recording', lambda m: {}),
            (re.compile(r'\brecord\s+screen\s+for\s+(\d+)\s+(minutes?|seconds?)\b', re.I), 
             'start_screen_recording', lambda m: {'duration_seconds': int(m.group(1)) * (60 if 'minute' in m.group(2) else 1)}),
            (re.compile(r'\b(stop|end)\s+screen\s+recording\b', re.I), 
             'stop_screen_recording', lambda m: {}),
            # Power management patterns
            (re.compile(r'\bshutdown\s+in\s+(\d+)\s+(minutes?|seconds?)\b', re.I), 
             'shutdown_system', lambda m: {'duration_seconds': int(m.group(1)) * (60 if 'minute' in m.group(2) else 1)}),
            (re.compile(r'\brestart\s+in\s+(\d+)\s+(minutes?|seconds?)\b', re.I), 
             'restart_system', lambda m: {'duration_seconds': int(m.group(1)) * (60 if 'minute' in m.group(2) else 1)}),
            (re.compile(r'\bsleep\s+in\s+(\d+)\s+(minutes?|seconds?)\b', re.I), 
             'sleep_system', lambda m: {'duration_seconds': int(m.group(1)) * (60 if 'minute' in m.group(2) else 1)}),
            (re.compile(r'\bhibernate\s+in\s+(\d+)\s+(minutes?|seconds?)\b', re.I), 
             'hibernate_system', lambda m: {'duration_seconds': int(m.group(1)) * (60 if 'minute' in m.group(2) else 1)}),
            # Immediate power actions
            (re.compile(r'\bshutdown\s+now\b', re.I), 
             'shutdown_system', lambda m: {}),
            (re.compile(r'\brestart\s+now\b', re.I), 
             'restart_system', lambda m: {}),
            (re.compile(r'\bsleep\s+now\b', re.I), 
             'sleep_system', lambda m: {}),
            (re.compile(r'\bhibernate\s+now\b', re.I), 
             'hibernate_system', lambda m: {}),
            # Volume controls - must be first to catch all variants
            (re.compile(r'\b(?:set|change)\s+(?:the\s+)?volume\s+to\s+(\d+)(?:%|percent)?\b', re.I),
             "set_volume", lambda m: {"volume": int(m.group(1))}),
            (re.compile(r'\b(?:increase|raise|turn\s+up|up)\s+(?:the\s+)?volume(?:\s+to\s+(\d+)(?:%|percent)?)?\b', re.I),
             "increase_volume", lambda m: {"amount": int(m.group(1)) if m.group(1) else 10}),
            (re.compile(r'\b(?:decrease|lower|turn\s+down|down)\s+(?:the\s+)?volume(?:\s+to\s+(\d+)(?:%|percent)?)?\b', re.I),
             "decrease_volume", lambda m: {"amount": int(m.group(1)) if m.group(1) else 10}),
            (re.compile(r'\b(?:get|what.{0,5}|current|check)\s+(?:the\s+)?volume\b', re.I), 
             "get_volume", lambda m: {}),
            (re.compile(r'\bmute(?:\s+volume)?\b', re.I), "mute_volume", lambda m: {}),
            (re.compile(r'\bunmute(?:\s+volume)?\b', re.I), "unmute_volume", lambda m: {}),
            
            # Brightness controls  
            (re.compile(r'\b(?:set|change)\s+(?:the\s+)?brightness\s+to\s+(\d+)(?:%|percent)?\b', re.I),
             "set_brightness", lambda m: {"brightness": int(m.group(1))}),
            (re.compile(r'\b(?:increase|raise|turn\s+up|up)\s+(?:the\s+)?brightness\b', re.I),
             "increase_brightness", lambda m: {}),
            (re.compile(r'\b(?:decrease|lower|turn\s+down|down)\s+(?:the\s+)?brightness\b', re.I),
             "decrease_brightness", lambda m: {}),
            (re.compile(r'\b(?:get|what.{0,5}|current|check)\s+(?:the\s+)?brightness\b', re.I), 
             "get_brightness", lambda m: {}),
            
            # Time/Date
            (re.compile(r'\b(?:what.{0,10}time|current\s+time|tell.{0,10}time)\b', re.I), 
             "get_time", lambda m: {}),
            (re.compile(r'\b(?:what.{0,10}date|current\s+date|today.{0,10}date)\b', re.I), 
             "get_date", lambda m: {}),
            
            # Calculator
            (re.compile(r'\bcalculate\s+(.+)', re.I), 
             "calculate", lambda m: {"expression": m.group(1)}),
            
            # Screenshots
            (re.compile(r'\b(?:take|capture)\s+(?:a\s+)?screenshot\b', re.I), 
             "take_screenshot", lambda m: {}),
            
            # App launching - comprehensive patterns
            (re.compile(r'\b(?:open|launch|start|run)\s+(.+)', re.I), 
             "launch_app", lambda m: {"app": m.group(1).strip().lower()}),

            # File search in folders
            (re.compile(r'\bfind\s+(.+?)\s+in\s+(downloads?|documents?|desktop)\b', re.I),
             "find_file", lambda m: {"name": m.group(1), "folder": m.group(2)}),

            # Twitter intent (improved)
            (re.compile(r'\b(twitter|tweets?)\s+(?:about\s+)?(.+)', re.I), 
             "get_twitter", lambda m: {"query": m.group(2)}),
             
            # Spotify/Music
            (re.compile(r'\bplay\s+(?:song|music|track)\s+(.+)', re.I), 
             "play_song", lambda m: {"song": m.group(1)}),
            (re.compile(r'\b(?:pause|stop)\s+(?:music|song|track|spotify|player)\b', re.I), 
             "pause_music", lambda m: {}),
            (re.compile(r'\b(?:resume|continue|unpause)\s+(?:music|song|track|spotify|player)\b', re.I), 
             "resume_music", lambda m: {}),
            
            # System info
            (re.compile(r'\bsystem\s+(?:info|information|status)\b', re.I), 
             "system_info", lambda m: {}),
            
            # Jokes
            (re.compile(r'\btell\s+(?:me\s+)?(?:a\s+)?joke\b', re.I), 
             "tell_joke", lambda m: {}),
            
            # News patterns - more specific
            (re.compile(r'\b(?:latest|top|breaking)\s+news\b', re.I), 
             "get_news", lambda m: {"query": "latest"}),
            (re.compile(r'\bnews\s+(?:about\s+)?(.+)', re.I), 
             "get_news", lambda m: {"query": m.group(1)}),
            (re.compile(r'\b(?:HD|get|fetch|show)\s+news\s+from\s+(.+)', re.I), 
             "get_news", lambda m: {"query": m.group(1)}),

            # Web search patterns - more specific
            (re.compile(r'\bsearch\s+(?:for\s+)?(.+)', re.I), 
             "web_search", lambda m: {"query": m.group(1)}),

            # Weather patterns
            (re.compile(r'\bweather(?:\s+in\s+(.+))?\b', re.I), 
             "get_weather", lambda m: {"location": m.group(1)} if m.group(1) else {}),

            # Forex specific
            (re.compile(r'\bforex\s+(?:factory\s+)?news\b', re.I), 
             "get_forex_news", lambda m: {}),

            # Wikipedia
            (re.compile(r'\bwikipedia\s+(.+)', re.I), 
             "search_wikipedia", lambda m: {"topic": m.group(1)}),

            # Crypto prices
            (re.compile(r'\bcrypto\s+price(?:s)?(?:\s+(.+))?\b', re.I), 
             "get_crypto_prices", lambda m: {"symbols": m.group(1)} if m.group(1) else {"symbols": "bitcoin"}),

            # Placeholder patterns for other services
            (re.compile(r'\btwitter\s+(.+)', re.I), 
             "get_twitter", lambda m: {"query": m.group(1)}),
            (re.compile(r'\breddit\s+r\/(\w+)', re.I), 
             "get_reddit", lambda m: {"subreddit": m.group(1)}),
            (re.compile(r'\bgithub\s+trending(?:\s+(\w+))?\b', re.I), 
             "get_github_trending", lambda m: {"language": m.group(1)} if m.group(1) else {})
        ]
        
        logger.info(f"Intent parser initialized with {len(self.patterns)} patterns")
    
    def parse(self, text: str) -> Tuple[Optional[str], Dict[str, Any]]:
        """Parse text for intents using rule-based patterns"""
        if not text:
            return None, {}
            
        text = text.strip()
        logger.debug(f"Parsing text: '{text}'")
        
        for i, (pattern, intent, param_func) in enumerate(self.patterns):
            match = pattern.search(text)
            if match:
                try:
                    params = param_func(match)
                    logger.info(f"✅ Matched pattern {i}: '{intent}' with params: {params}")
                    return intent, params
                except Exception as e:
                    logger.error(f"Error extracting params for pattern {i}: {e}")
                    continue
        
        logger.debug(f"❌ No intent matched for: '{text}'")
        return None, {}
