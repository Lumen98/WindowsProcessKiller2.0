import sys
import ctypes
from utils import is_admin, run_as_admin
from gui import run_app

def hide_console():
    """Hide the console window (Windows only)."""
    if sys.platform == "win32":
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

if __name__ == "__main__":
    # Hide the console window before running the app
    hide_console()

    # Check for admin rights
    if not is_admin():
        run_as_admin()
    else:
        run_app()
