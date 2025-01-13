import json
import os
import ctypes
import sys

CACHE_FILE = "cache.json"

# Load cached processes
def load_cached_processes():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as file:
            data = json.load(file)
            return data.get("selected_processes", [])
    return []

# Save selected processes to cache
def save_cached_processes(process_list):
    with open(CACHE_FILE, 'w') as file:
        json.dump({"selected_processes": process_list}, file)

# Check for admin rights
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# Run as admin
def run_as_admin():
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{sys.argv[0]}"', None, 1)
        sys.exit()