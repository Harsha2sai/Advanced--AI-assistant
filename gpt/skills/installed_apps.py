import winreg
import os
import logging
import difflib
import glob
import subprocess
import json

SYNONYMS = {
    "adobe reader": ["adobe acrobat", "acrobat reader", "adobe acrobat reader"],
    "microsoft store": ["store", "windows store"],
    "whatsapp": ["whatsapp desktop", "whatsapp app"],
    "spotify": ["spotify music"]
}

def normalize(s: str) -> str:
    s = s.lower().strip()
    for prefix in ("open ", "launch ", "start ", "run ", "the ", "a ", "an "):
        if s.startswith(prefix):
            s = s[len(prefix):]
    return " ".join(s.split())

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

    logging.info(f"Discovered {len(apps)} installed applications")
    return apps

def resolve_executable(path_or_dir: str) -> str | None:
    if os.path.isfile(path_or_dir):
        return path_or_dir
    if os.path.isdir(path_or_dir):
        for pattern in ("*.exe", "app\\*.exe", "application\\*.exe"):
            hits = glob.glob(os.path.join(path_or_dir, pattern))
            if hits:
                hits.sort(key=lambda p: os.path.getsize(p) if os.path.isfile(p) else 0, reverse=True)
                return hits[0]
    return None

def get_uwp_aumid_map() -> dict[str,str]:
    ps = r'''
Get-StartApps | ForEach-Object {
  [PSCustomObject]@{ Name = $_.Name; AUMID = $_.AppID }
} | ConvertTo-Json
'''
    p = subprocess.run(["powershell","-NoProfile","-ExecutionPolicy","Bypass","-Command", ps],
                       capture_output=True, text=True)
    if p.returncode != 0 or not p.stdout.strip():
        return {}
    try:
        arr = json.loads(p.stdout)
        if isinstance(arr, dict): arr = [arr]
        result = { i.get("Name",""): i.get("AUMID","") for i in arr if isinstance(i, dict) }
        logging.info(f"Loaded UWP AppUserModelID map with {len(result)} entries")
        return result
    except Exception:
        return {}

def launch_uwp_by_name(name: str, aumids: dict[str,str]) -> bool:
    real = None
    nname = normalize(name)
    for disp, aumid in aumids.items():
        if normalize(disp) == nname or nname in normalize(disp):
            real = aumid
            break
    if not real:
        return False
    subprocess.Popen(["explorer.exe", f"shell:AppsFolder\\{real}"])
    logging.info(f"Launched UWP app '{name}' via AppUserModelID: {real}")
    return True

def best_match_app(apps: dict[str,str], query: str) -> tuple[str,str] | tuple[None,None]:
    q = normalize(query)
    candidates = {q}
    for canon, alts in SYNONYMS.items():
        if q == canon or q in alts:
            candidates.add(canon)
            candidates.update(alts)
    names = list(apps.keys())
    norm_map = {normalize(n): n for n in names}
    search_space = list(norm_map.keys())
    for c in list(candidates):
        for nm in search_space:
            if c in nm or nm in c:
                real = norm_map[nm]
                return real, apps[real]
    all_targets = list(candidates) + search_space
    matches = difflib.get_close_matches(q, search_space, n=1, cutoff=0.6)
    if matches:
        real = norm_map[matches[0]]
        return real, apps[real]
    return None, None
