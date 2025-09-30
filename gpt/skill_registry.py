# gpt/skill_registry.py

import re
from typing import Callable, Any, Dict, List, Tuple

class SkillRegistry:
    """
    A central registry for all skills, using regex for intent matching.
    This class is a singleton.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SkillRegistry, cls).__new__(cls)
            # Skills are stored in a list to maintain registration order.
            # This can be important if some patterns are more specific than others.
            cls._instance.skills = []
        return cls._instance

    def register(self, func: Callable, patterns: List[str], description: str = ""):
        """Register a new skill with a list of regex patterns."""
        self.skills.append({
            "func": func,
            "patterns": [re.compile(p, re.IGNORECASE) for p in patterns],
            "description": description,
        })

    def find_skill(self, text: str) -> Tuple[Callable, Dict[str, Any]]:
        """
        Find the best matching skill for a given text query and extract parameters.

        It iterates through registered skills and their patterns. The first pattern
        that matches the beginning of the text is used.
        """
        text = text.lower().strip()
        for skill_info in self.skills:
            for pattern in skill_info["patterns"]:
                match = pattern.match(text)
                if match:
                    # Parameters are extracted from named capture groups in the regex.
                    params = match.groupdict()
                    return skill_info["func"], params
        return None, {}

# Global instance of the registry
registry = SkillRegistry()

def skill(patterns: List[str], description: str = ""):
    """
    A decorator to register a function as a skill.

    Args:
        patterns: A list of regex strings. The patterns should use named
                  capture groups for any parameters, e.g., r'calculate (?P<expr>.+)'
        description: A brief description of what the skill does.
    """
    def decorator(func: Callable):
        registry.register(func, patterns, description)
        return func
    return decorator