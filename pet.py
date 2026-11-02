import sys
import random
import os
import time
from google import genai
from PyQt5.QtCore import Qt, QPoint, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QTransform
from PyQt5.QtWidgets import QApplication, QLabel, QMenu, QWidget, QInputDialog
from pypresence import Presence
import winsound
from gtts import gTTS
import tempfile
import threading

# ==========================================
# 🔑 請直接把你的 Gemini API 金鑰填在下方引號中
# ==========================================
import os
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

# 取得目前程式碼所在的資料夾絕對路徑
script_dir = os.path.dirname(os.path.abspath(__file__))


# 獨立執行緒處理 AI 請求（避免視窗卡死）
class AIWorker(QThread):
    finished = pyqtSignal(str)

    def __init__(self, prompt):
        super().__init__()
        self.prompt = prompt

    def run(self):
        try:
            if not API_KEY:
                self.finished.emit("哎呀，你還沒在程式碼上方填入 API 金鑰喔！")
                return

            client = genai.Client(api_key=API_KEY)
            system_instruction = "你是一個可愛的桌面小桌寵，講話語氣要溫柔、俏皮，每次回答請控制在 30 個字以內。"
            
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=self.prompt,
                config={
                    'system_instruction': system_instruction,
                }
            )
            self.finished.emit(response.text)
        except Exception as e:
            self.finished.emit(f"哎呀，連線失敗：{str(e)}")


class DesktopPet(QWidget):
    def speak_text(self, text):
        """ 在背景執行緒中將文字轉語音並靜默播放，絕對不跳視窗 """
        def run_tts():
            try:
                from gtts import gTTS
                from playsound import playsound
                import tempfile

                # 將文字轉成語音
                tts = gTTS(text=text, lang='zh-TW', slow=False)
                
                # 建立安全且會自動刪除的暫存音訊檔
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
                    temp_filename = fp.name
                tts.save(temp_filename)
                
                # 在背景安靜播放音訊，播完自動刪除檔案
                playsound(temp_filename)
                try:
                    os.remove(temp_filename)
                except:
                    pass
            except Exception as e:
                print(f"語音播放失敗: {e}")

        # 開啟執行緒播放語音
        threading.Thread(target=run_tts, daemon=True).start()

    def __init__(self):
        super().__init__()
        self.initUI()
        self.initAnimation()
        self.initMovement()
        self.initDiscordRPC()  # 初始化 Discord 狀態顯示

    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.label = QLabel(self)
        
        self.bubble_widget = QWidget(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
        self.bubble_widget.setAttribute(Qt.WA_TranslucentBackground, True)
        
        self.bubble_label = QLabel(self.bubble_widget)
        self.bubble_label.setStyleSheet(
            "background-color: rgba(255, 255, 255, 230); color: black; "
            "border: 2px solid #4a90e2; border-radius: 10px; padding: 8px; "
            "font-size: 13px; font-weight: bold;"
        )
        self.bubble_widget.hide()
        
        self.dragging = False
        self.offset = QPoint()
        self.direction = 1
        self.scale_factor = 1.0
        self.is_walking = True

    def initDiscordRPC(self):
        # ⚠️ 如果你有到 Discord Developer Portal 建立 App，可以把 Client ID 換成你的
        # 如果沒有，可以先用下面這個測試用的公開 Client ID 或是留白測試
        self.RPC_CLIENT_ID = "1566775719961427970" 
        try:
            self.RPC = Presence(self.RPC_CLIENT_ID)
            self.RPC.connect()
            self.start_time = time.time()
            self.RPC.update(
                state="正在桌面上漫步 🐾",
                details="與桌面小桌寵互動中",
                start=self.start_time,
                large_image="pet_idle",
                large_text="桌面寵物"
            )
        except Exception as e:
            print(f"Discord RPC 連線提示（未開 Discord 或 ID 錯誤可忽略）: {e}")

    def update_discord_status(self, state_text):
        try:
            if hasattr(self, 'RPC'):
                self.RPC.update(
                    state=state_text,
                    details="與桌面小桌寵互動中",
                    start=self.start_time,
                    large_image="pet_idle",
                    large_text="桌面寵物"
                )
        except:
            pass

    def initAnimation(self):
        self.frame_files = ['1.png', '2.png', '3.png', '4.png', '5.png', '6.png', '7.png', '8.png']
        self.frames = []
        
        for file in self.frame_files:
            file_path = os.path.join(script_dir, file)
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                self.frames.append(pixmap)
        
        drag_path = os.path.join(script_dir, 'pet_drag.png')
        self.drag_pixmap = QPixmap(drag_path)

        idle_path = os.path.join(script_dir, 'pet_idle.png')
        self.idle_pixmap = QPixmap(idle_path)

        if not self.frames:
            self.label.setText("🐾 找不到圖片")
            self.label.setStyleSheet(
                "color: white; background-color: rgba(0, 0, 0, 160); "
                "font-size: 14px; border-radius: 8px; padding: 10px;"
            )
            self.resize(200, 60)
            return

        self.current_frame = 0
        self.update_image()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_frame)
        self.timer.start(150)

    def initMovement(self):
        self.move_timer = QTimer(self)
        self.move_timer.timeout.connect(self.update_position)
        self.move_timer.start(50)

        self.change_dir_timer = QTimer(self)
        self.change_dir_timer.timeout.connect(self.decide_new_direction)
        self.change_dir_timer.start(3000)

        self.is_walking = True

    def decide_new_direction(self):
        choice = random.choice([-1, 0, 1])
        if choice == 0:
            self.is_walking = False
            self.update_discord_status("正在發呆放空 💤")
        else:
            self.is_walking = True
            self.direction = choice
            self.update_discord_status("正在桌面上漫步 🐾")
        
        self.update_image()

    def update_position(self):
        if self.dragging:
            return

        if self.is_walking:
            pos = self.pos()
            new_x = pos.x() + self.direction * 2
            
            screen = QApplication.primaryScreen().geometry()
            if new_x < 0:
                new_x = 0
                self.direction = 1
            elif new_x > screen.width() - self.width():
                new_x = screen.width() - self.width()
                self.direction = -1

            self.move(new_x, pos.y())
            if self.bubble_widget.isVisible():
                self.update_bubble_position()

    def update_image(self):
        if not self.frames:
            return

        if self.dragging:
            pixmap = self.drag_pixmap if not self.drag_pixmap.isNull() else self.frames[0]
        elif not self.is_walking and not self.idle_pixmap.isNull():
            pixmap = self.idle_pixmap
        else:
            pixmap = self.frames[self.current_frame]

        transform = QTransform()
        if self.direction == -1 and not self.dragging:
            transform.scale(-1 * self.scale_factor, self.scale_factor)
        else:
            transform.scale(self.scale_factor, self.scale_factor)

        scaled_pixmap = pixmap.transformed(transform, Qt.SmoothTransformation)
        self.label.setPixmap(scaled_pixmap)
        self.resize(scaled_pixmap.width(), scaled_pixmap.height())

    def next_frame(self):
        if not self.frames:
            return
        if self.is_walking and not self.dragging:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.update_image()

    def wheelEvent(self, event):
        angle = event.angleDelta().y()
        if angle > 0:
            self.scale_factor = min(self.scale_factor + 0.1, 2.5)
        else:
            self.scale_factor = max(self.scale_factor - 0.1, 0.4)
        
        self.update_image()
        if self.bubble_widget.isVisible():
            self.update_bubble_position()
        event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.open_ai_chat()
            event.accept()

    def open_ai_chat(self):
        text, ok = QInputDialog.getText(self, "與桌寵對話", "你想對桌寵說什麼？")
        if ok and text:
            self.show_speech_bubble("思考中...")
            self.update_discord_status("正在跟主人聊天 💬")
            
            self.ai_worker = AIWorker(text)
            self.ai_worker.finished.connect(self.handle_ai_response)
            self.ai_worker.start()

    def handle_ai_response(self, reply_text):
        self.show_speech_bubble(reply_text)
        self.update_discord_status("正在跟主人聊天 💬")
        
        # 【新增】呼叫語音朗讀 AI 的回覆內容
        self.speak_text(reply_text)

    def show_speech_bubble(self, text):
        self.bubble_label.setText(text)
        self.bubble_label.adjustSize()
        self.bubble_widget.resize(self.bubble_label.size())
        
        self.update_bubble_position()
        self.bubble_widget.show()
        
        if hasattr(self, 'bubble_timer'):
            self.bubble_timer.stop()
        self.bubble_timer = QTimer(self)
        self.bubble_timer.setSingleShot(True)
        self.bubble_timer.timeout.connect(self.bubble_widget.hide)
        self.bubble_timer.start(6000)

    def update_bubble_position(self):
        pet_global_pos = self.mapToGlobal(QPoint(0, 0))
        bubble_x = pet_global_pos.x() + (self.width() - self.bubble_widget.width()) // 2
        bubble_y = pet_global_pos.y() - self.bubble_widget.height() - 10
        self.bubble_widget.move(bubble_x, bubble_y)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.globalPos() - self.pos()
            self.update_image()
            
            # 【新增】點擊音效 (使用 Windows 內建提示音，或你可以改成播放音效檔)
            try:
                winsound.Beep(800, 100) # 頻率 800Hz，持續 100 毫秒
            except:
                pass

            if self.bubble_widget.isVisible():
                self.update_bubble_position()
            event.accept()
        elif event.button() == Qt.RightButton:
            self.show_context_menu(event.globalPos())

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.offset)
            if self.bubble_widget.isVisible():
                self.update_bubble_position()
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.update_image()
            if self.bubble_widget.isVisible():
                self.update_bubble_position()
            event.accept()

    def closeEvent(self, event):
        try:
            if hasattr(self, 'RPC'):
                self.RPC.close()
        except:
            pass
        self.bubble_widget.close()
        event.accept()

    def show_context_menu(self, pos):
        menu = QMenu(self)
        exit_action = menu.addAction("退出桌寵")
        action = menu.exec_(pos)
        if action == exit_action:
            try:
                if hasattr(self, 'RPC'):
                    self.RPC.close()
            except:
                pass
            self.bubble_widget.close()
            QApplication.quit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    pet = DesktopPet()
    pet.show()
    sys.exit(app.exec_())