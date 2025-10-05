import winreg
import os

def get_installed_apps():
    """Scan Windows registry to find installed apps and their executable/install paths"""
    apps = {}

    reg_paths = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
    ]

    for base_key in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
        for reg_path in reg_paths:
            try:
                reg_key = winreg.OpenKey(base_key, reg_path)
            except FileNotFoundError:
                continue

            for i in range(winreg.QueryInfoKey(reg_key)[0]):
                try:
                    subkey_name = winreg.EnumKey(reg_key, i)
                    subkey = winreg.OpenKey(reg_key, subkey_name)

                    # Read DisplayName and path info (DisplayIcon or InstallLocation)
                    try:
                        name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                    except FileNotFoundError:
                        continue
                    
                    app_path = ""
                    try:
                        app_path = winreg.QueryValueEx(subkey, "DisplayIcon")[0]
                        # Clean paths (strip quotes and remove command line args)
                        app_path = app_path.split(",")[0].strip('"')
                        app_path = os.path.normpath(app_path)
                    except FileNotFoundError:
                        try:
                            app_path = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                            app_path = os.path.normpath(app_path)
                        except FileNotFoundError:
                            app_path = ""

                    if name not in apps:
                        apps[name] = app_path
                except OSError:
                    continue

    return apps
