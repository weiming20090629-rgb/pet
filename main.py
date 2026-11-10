import sys
import os
from PyQt5.QtWidgets import QApplication
from dotenv import load_dotenv

load_dotenv()

# 將 src 目錄加入系統路徑，方便內部模組互相引用
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.pet_window import DesktopPet

if __name__ == '__main__':
    app = QApplication(sys.argv)
    pet = DesktopPet()
    pet.show()
    sys.exit(app.exec_())