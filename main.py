import os
import sys
from dotenv import load_dotenv
from PyQt5.QtWidgets import QApplication
from src.startup_utils import ensure_autostart_on_first_run

load_dotenv()

BASE_DIR = (
    getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    if getattr(sys, "frozen", False)
    else os.path.dirname(os.path.abspath(__file__))
)
SRC_DIR = os.path.join(BASE_DIR, "src")

for p in (BASE_DIR, SRC_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

from src.pet_window import DesktopPet

if __name__ == "__main__":
    ensure_autostart_on_first_run()
    app = QApplication(sys.argv)
    pet = DesktopPet()
    pet.show()
    sys.exit(app.exec_())