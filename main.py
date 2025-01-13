from utils import is_admin, run_as_admin
from gui import run_app

if __name__ == "__main__":
    if not is_admin():
        run_as_admin()
    else:
        run_app()
