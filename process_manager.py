import psutil
import json
import subprocess

# Load whitelist for safety
with open('process_whitelist.json') as f:
    WHITELIST = json.load(f)["critical_processes"]

def is_system_process(proc):
    try:
        is_system_user = proc.username() in ["SYSTEM", "Local Service", "Network Service"]
        is_system_path = "c:\\windows\\system32" in proc.exe().lower()
        return is_system_user or is_system_path
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False

def safe_kill(pid, force=False):
    try:
        process = psutil.Process(pid)
        process_name = process.name().lower()

        if process_name in WHITELIST:
            return False  # Prevent killing critical processes

        if force:
            # Attempt to stop the service first
            subprocess.run(["sc", "stop", process_name], shell=True)
            # Force kill the process and its children
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], shell=True)
            return True

        process.terminate()
        process.wait(timeout=3)
        return True

    except subprocess.CalledProcessError:
        print(f"Failed to force kill {process_name}")
        return False
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return False


def list_processes():
    for proc in psutil.process_iter():
        try:
            proc.cpu_percent(interval=None)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    processes = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            cpu_usage = proc.cpu_percent(interval=None)
            name = proc.name() + ' (SYSTEM)' if is_system_process(proc) else proc.name()
            processes.append({
                'pid': proc.pid,
                'name': name,
                'cpu_percent': cpu_usage
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return processes