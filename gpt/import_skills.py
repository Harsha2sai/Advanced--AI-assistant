# gpt/import_skills.py

def import_common_skills():
    """
    Import all functions from skills/common.py into globals(),
    assuming skills/ is a sibling of this file.
    """
    import importlib
    common = importlib.import_module("gpt.skills.common")
    for attr in dir(common):
        if not attr.startswith("_"):
            globals()[attr] = getattr(common, attr)
# gpt/import_skills.py
def import_all_skills():
    import importlib
    pkg = importlib.import_module("gpt.skills")  # absolute package
    for name in getattr(pkg, "__all__", []):
        globals()[name] = getattr(pkg, name)
