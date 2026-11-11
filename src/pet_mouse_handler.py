import time
import winsound
from .styles import CONTEXT_MENU_STYLE
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtGui import QPixmap, QCursor
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import QMenu, QApplication, QInputDialog

from .pet_actions import PetActionHandler
from .workers import AIWorker

class PetMouseHandler:
    @staticmethod
    def handle_mouse_press(pet, event):
        if event.button() == Qt.LeftButton:
            pet.dragging = True
            pet.offset = event.globalPos() - pet.pos()
            pet.update_image()
            pet.last_interaction_time = time.time()
            
            try:
                winsound.Beep(800, 100)
            except:
                pass

            if pet.bubble_widget.isVisible():
                pet.update_bubble_position()
            event.accept()
        elif event.button() == Qt.RightButton:
            PetMouseHandler.show_context_menu(pet, event.globalPos())

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
        text, ok = QInputDialog.getText(pet, "與桌寵對話", "你想對桌寵說什麼？")
        if ok and text:
            pet.show_speech_bubble("思考中...")
            pet.update_discord_status("正在跟主人聊天 💬")
            pet.favorability = min(pet.favorability + 1, 100)
            pet.save_data()
            
            pet.ai_worker = AIWorker(text)
            pet.ai_worker.finished.connect(pet.handle_ai_response)
            pet.ai_worker.start()

    @staticmethod
    def show_context_menu(pet, pos):
        menu = QMenu(pet)
        menu.setStyleSheet(CONTEXT_MENU_STYLE)
        menu.setWindowFlags(menu.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        menu.setAttribute(Qt.WA_TranslucentBackground, True)

        if pet.favorability >= 80:
            status_text = f"❤️ 好感度: 很高 | 💰 金幣: {pet.coins}"
        elif pet.favorability >= 50:
            status_text = f"💛 好感度: 普通 | 💰 金幣: {pet.coins}"
        elif pet.favorability > 0:
            status_text = f"💢 好感度: 偏低 (快歸零囉) | 💰 金幣: {pet.coins}"
        else:
            status_text = f"🔥 好感度: 歸零 (黑化制裁中) | 💰 金幣: {pet.coins}"

        favor_action = menu.addAction(status_text)
        favor_action.setEnabled(False)
        
        menu.addSeparator()
        
        pet_action = menu.addAction("摸摸頭 (增加好感)")
        punch_action = menu.addAction("💥 打她一拳 (減少好感)")
        job_action = menu.addAction("💼 打工賺錢")          
        wallet_action = menu.addAction("👛 查看錢包與狀態")  
        rps_action = menu.addAction("🎮 玩猜拳小遊戲")
        alarm_action = menu.addAction("⏰ 設定休息鬧鐘")  
        weather_action = menu.addAction("🌤️ 查詢目前天氣")
        
        todo_menu = menu.addMenu("📝 待辦事項與提醒")
        add_todo_action = todo_menu.addAction("➕ 新增待辦提醒")
        view_todo_action = todo_menu.addAction("📋 查看待辦清單")
        
        screenshot_action = menu.addAction("📸 桌面截圖小幫手")
        
        voice_status_text = "🔊 語音朗讀：開啟" if pet.voice_enabled else "🔇 語音朗讀：關閉"
        voice_action = menu.addAction(voice_status_text)
        
        opacity_menu = menu.addMenu("調整透明度")
        action_100 = opacity_menu.addAction("完全不透明 (1.0)")
        action_80 = opacity_menu.addAction("半透明 (0.8)")
        action_50 = opacity_menu.addAction("高透明 (0.5)")
        
        menu.addSeparator()
        exit_action = menu.addAction("退出桌寵")
        
        action = menu.exec_(pos)
        pet.last_interaction_time = time.time()
        
        if action == pet_action:
            pet.favorability = min(pet.favorability + 5, 100)
            pet.save_data()
            msg = f"哼哼~被摸頭了，好感度上升！(目前: {pet.favorability})"
            pet.show_speech_bubble(msg)
            pet.speak_text("哼哼，感覺還不錯嘛！")
            pet.update_discord_status(f"好感度 {pet.favorability} 🐾")
        elif action == punch_action:
            pet.favorability = max(pet.favorability - 5, 0)
            pet.save_data()
            msg = f"好痛！你幹嘛打我... (目前好感度: {pet.favorability})"
            pet.show_speech_bubble(msg)
            pet.speak_text("好痛！你為什麼要打我，太過分了！")
            try:
                winsound.Beep(300, 200)
            except:
                pass
            pet.update_discord_status(f"被打了一拳，好感度 {pet.favorability} 💢")
        elif action == job_action:
            PetActionHandler.start_part_time_job(pet)
        elif action == wallet_action:
            PetActionHandler.show_wallet(pet)
        elif action == rps_action:
            PetActionHandler.play_rps_game(pet)
        elif action == alarm_action:
            pet.set_pomodoro_timer()
        elif action == weather_action:
            pet.manual_check_weather()
        elif action == add_todo_action:
            PetActionHandler.add_todo_item(pet)
        elif action == view_todo_action:
            PetActionHandler.show_todo_list(pet)
        elif action == screenshot_action:
            pet.take_screenshot()
        elif action == voice_action:
            pet.voice_enabled = not pet.voice_enabled
            state_str = "開啟" if pet.voice_enabled else "關閉"
            pet.show_speech_bubble(f"語音功能已{state_str}囉！")
        elif action == action_100:
            pet.setWindowOpacity(1.0)
        elif action == action_80:
            pet.setWindowOpacity(0.8)
        elif action == action_50:
            pet.setWindowOpacity(0.5)
        elif action == exit_action:
            try:
                if hasattr(pet, 'RPC'):
                    pet.RPC.close()
            except:
                pass
            pet.bubble_widget.close()
            QApplication.quit()
            