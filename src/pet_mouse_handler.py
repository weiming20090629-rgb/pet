import time
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QInputDialog
from .workers import AIWorker
from .styles import DIALOG_STYLE
from .pet_menu import PetMenuManager


class PetMouseHandler:
    """專注處理滑鼠拖曳、縮放、雙擊與右鍵選單觸發"""

    @staticmethod
    def handle_mouse_press(pet, event):
        if event.button() == Qt.LeftButton:
            pet.dragging = True
            pet.offset = event.globalPos() - pet.pos()
            pet.update_image()
            pet.last_interaction_time = time.time()

            if pet.bubble_widget.isVisible():
                pet.update_bubble_position()
            event.accept()
        elif event.button() == Qt.RightButton:
            PetMenuManager.show_context_menu(pet, event.globalPos())

    @staticmethod
    def handle_mouse_move(pet, event):
        if pet.dragging and event.buttons() == Qt.LeftButton:
            pet.move(event.globalPos() - pet.offset)
            if pet.bubble_widget.isVisible():
                pet.update_bubble_position()
            event.accept()

    @staticmethod
    def handle_mouse_release(pet, event):
        if event.button() == Qt.LeftButton:
            pet.dragging = False
            pet.update_image()
            if pet.bubble_widget.isVisible():
                pet.update_bubble_position()
            event.accept()

    @staticmethod
    def handle_wheel_event(pet, event):
        angle = event.angleDelta().y()
        if angle > 0:
            pet.scale_factor = min(pet.scale_factor + 0.1, 2.5)
        else:
            pet.scale_factor = max(pet.scale_factor - 0.1, 0.4)

        pet.update_image()
        if pet.bubble_widget.isVisible():
            pet.update_bubble_position()
        event.accept()

    @staticmethod
    def handle_double_click(pet, event):
        if event.button() == Qt.LeftButton:
            pet.last_interaction_time = time.time()
            PetMouseHandler.open_ai_chat(pet)
            event.accept()

    @staticmethod
    def open_ai_chat(pet):
        dialog = QInputDialog(pet)
        dialog.setWindowTitle("與桌寵對話")
        dialog.setLabelText("你想對桌寵說什麼？")
        dialog.setStyleSheet(DIALOG_STYLE)
        ok = dialog.exec_() == QInputDialog.Accepted
        text = dialog.textValue()

        if ok and text:
            pet.show_speech_bubble("思考中...")
            pet.update_discord_status("正在跟主人聊天 💬")
            pet.favorability = min(pet.favorability + 1, 100)
            pet.save_data()

            pet.ai_worker = AIWorker(text)
            pet.ai_worker.finished.connect(pet.handle_ai_response)
            pet.ai_worker.start()