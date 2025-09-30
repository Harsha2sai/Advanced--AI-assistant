# gpt/import_skills.py

import os
import importlib
import pkgutil

def import_all_skills():
    """
    Dynamically imports all modules from the 'gpt.skills' package.

    This function scans the 'gpt/skills' directory, identifies all Python
    modules, and imports them. The act of importing executes the @skill
    decorators within those modules, which populates the global skill registry.
    This ensures that all skills are automatically discovered and made
    available at startup without needing manual registration.
    """
    import gpt.skills

    # The path to the skills package
    package_path = os.path.dirname(gpt.skills.__file__)
    package_name = gpt.skills.__name__

    print(f"🔎 Loading skills from: {package_path}")

    # Iterate over all modules in the skills package
    for _, module_name, _ in pkgutil.iter_modules([package_path]):
        if not module_name.startswith('_'):  # Skip private modules like __init__
            try:
                # Construct the full module path (e.g., 'gpt.skills.common')
                full_module_path = f"{package_name}.{module_name}"
                # Import the module
                importlib.import_module(full_module_path)
                print(f"  ✅ Loaded skill module: {module_name}")
            except Exception as e:
                print(f"  ❌ Failed to load skill module {module_name}: {e}")

# Example of how to use it (this file is not meant to be run directly)
if __name__ == '__main__':
    print("This script is intended to be imported, not run directly.")
    print("Demonstrating skill import process:")
    import_all_skills()

    # To see the registered skills, you would do this in your main app:
    # from gpt.skill_registry import registry
    # print("\nRegistered skills:")
    # for skill_name, skill_info in registry.skills.items():
    #     print(f"- {skill_name}: {skill_info.get('description', 'No description')}")