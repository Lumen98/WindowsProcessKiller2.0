import json
import os
import ctypes
import sys
from datetime import datetime

CACHE_FILE = "cache.json"
LOG_FILE = "kill_log.txt"
USER_WHITELIST_FILE = "user_whitelist.json"
USER_BLACKLIST_FILE = "user_blacklist.json"

def load_cached_processes():
    """Load the list of selected processes from a cache file."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as file:
            data = json.load(file)
            return data.get("selected_processes", [])
    return []

def save_cached_processes(process_list):
    """Save the list of selected processes to a cache file."""
    with open(CACHE_FILE, 'w') as file:
        json.dump({"selected_processes": process_list}, file)

def load_json_file(filepath, key):
    """Generic function to load JSON data from a file under a key."""
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as file:
                data = json.load(file)
                return data.get(key, [])
        except json.JSONDecodeError:
            return []
    return []

def save_json_file(filepath, key, process_list):
    """Generic function to save a list to a JSON file under a key."""
    data = {}
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as file:
                data = json.load(file)
        except json.JSONDecodeError:
            pass
    data[key] = process_list
    with open(filepath, 'w') as file:
        json.dump(data, file, indent=4)

def log_kill_action(process_name, pid, status):
    """Log the results of a kill action to a text file."""
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{datetime.now().isoformat()}] Killed: {process_name} (PID: {pid}) - Status: {status}\n")

def is_admin():
    """Check if the user is running as admin (Windows-only)."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Re-run the current script as admin."""
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            sys.executable,
            f'"{sys.argv[0]}"',
            None,
            1
        )
        sys.exit()
