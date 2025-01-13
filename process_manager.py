import json
import os
import psutil
import subprocess
import ctypes
from PyQt5 import QtWidgets

# GPU monitoring (optional)
try:
    import GPUtil
    HAS_GPU = True
except ImportError:
    HAS_GPU = False

from utils import log_kill_action, load_json_file
from PyQt5.QtWidgets import QMessageBox

# Load system-level whitelist
with open('process_whitelist.json') as f:
    SYSTEM_WHITELIST = json.load(f)["critical_processes"]

def load_user_whitelist():
    return load_json_file("user_whitelist.json", "user_defined_whitelist")

def load_user_blacklist():
    return load_json_file("user_blacklist.json", "user_defined_blacklist")

def is_system_process(proc):
    """Check if a process is a system-level process."""
    try:
        is_system_user = proc.username() in ["SYSTEM", "Local Service", "Network Service"]
        is_system_path = "c:\\windows\\system32" in proc.exe().lower()
        return is_system_user or is_system_path
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False

def is_process_whitelisted(process_name):
    """Check if process is in system or user-defined whitelist."""
    process_name_lower = process_name.lower()
    user_whitelist = [p.lower() for p in load_user_whitelist()]
    # Combine system + user whitelist
    combined_whitelist = [p.lower() for p in SYSTEM_WHITELIST] + user_whitelist
    return process_name_lower in combined_whitelist

def is_process_blacklisted(process_name):
    """Check if process is in user-defined blacklist."""
    user_blacklist = [p.lower() for p in load_user_blacklist()]
    return process_name.lower() in user_blacklist


def force_kill(pid):
    """Forcefully kill a process using taskkill and PowerShell."""
    # Method 1: taskkill
    result = subprocess.run(
        ["taskkill", "/F", "/T", "/PID", str(pid)],
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    if result.returncode == 0:
        return True  # Successfully killed

    # Method 2: PowerShell fallback
    powershell_cmd = f'powershell.exe -Command "Stop-Process -Id {pid} -Force"'
    result = subprocess.run(
        powershell_cmd,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return result.returncode == 0

def is_admin():
    """Check if the app has admin rights."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def safe_kill(pid, parent_window=None):
    """Gracefully kill a process, prompt to force kill if needed."""
    try:
        process = psutil.Process(pid)
        process_name = process.name()

        # Ensure admin rights
        if not is_admin():
            if parent_window:
                QtWidgets.QMessageBox.warning(
                    parent_window,
                    "Permission Denied",
                    "Administrator privileges are required to kill this process."
                )
            return False

        # Attempt graceful termination
        process.terminate()
        try:
            process.wait(timeout=3)
            return True  # Graceful kill worked
        except psutil.TimeoutExpired:
            pass  # Proceed to force kill prompt

        # Prompt user for force kill
        if parent_window:
            response = QtWidgets.QMessageBox.question(
                parent_window,
                "Force Kill?",
                f"Failed to terminate {process_name} (PID: {pid}).\nWould you like to force kill it?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            if response == QtWidgets.QMessageBox.No:
                return False

        # Force kill if the user agrees
        return force_kill(pid)

    except psutil.NoSuchProcess:
        return True  # Process already gone

    except psutil.AccessDenied:
        if parent_window:
            QtWidgets.QMessageBox.warning(
                parent_window,
                "Access Denied",
                "Access denied while trying to kill this process. Try running as Administrator."
            )
        return False

    except Exception as e:
        print(f"Error killing process {pid}: {e}")
        return False

def list_processes():
    """Return a list of processes with CPU, Memory, GPU usage (if available)."""
    # Prime CPU usage to get immediate stats
    for proc in psutil.process_iter():
        try:
            proc.cpu_percent(interval=None)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    processes = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            cpu_usage = proc.cpu_percent(interval=None)
            mem_usage = proc.memory_percent()
            name = proc.name()
            pid = proc.pid

            # Mark if it's a system process
            if is_system_process(proc):
                name += " (SYSTEM)"

            # GPU usage: If we have the GPUtil library, try to get the usage for the matching PID
            gpu_usage = 0.0
            if HAS_GPU:
                for gpu_proc in GPUtil.getGPUs():
                    for p in gpu_proc.processes:
                        if p['pid'] == pid:
                            gpu_usage = p['gpu_util']
                            break

            processes.append({
                'pid': pid,
                'name': name,
                'cpu_percent': cpu_usage,
                'memory_percent': mem_usage,
                'gpu_percent': gpu_usage
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return processes
