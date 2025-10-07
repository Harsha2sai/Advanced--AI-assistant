# gpt/import_skills.py

import sys
from pathlib import Path

def ensure_gpt_on_sys_path():
    # Ensure the 'gpt' directory (parent of this file) is on sys.path
    here = Path(__file__).resolve().parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))
