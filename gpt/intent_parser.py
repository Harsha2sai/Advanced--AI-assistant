# gpt/intent_parser.py

from gpt.skill_registry import registry
from typing import Callable, Dict, Any, Tuple

def parse_intent(text: str) -> Tuple[Callable, Dict[str, Any]]:
    """
    Parses user input text to find a matching skill and extract parameters.

    This function delegates the search to the global SkillRegistry.
    """
    # The registry's find_skill method now returns the function and params directly.
    skill_func, params = registry.find_skill(text)
    return skill_func, params