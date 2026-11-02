import sys
import random
import os
import time
import psutil
import requests  # 👈 【新增】用於抓取天氣資訊
from google import genai
from PyQt5.QtCore import Qt, QPoint, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QTransform
from PyQt5.QtWidgets import QApplication, QLabel, QMenu, QWidget, QInputDialog
from pypresence import Presence
import winsound
from gtts import gTTS
import tempfile
import threading

from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
script_dir = os.path.dirname(os.path.abspath(__file__))


class AIWorker(QThread):
    finished = pyqtSignal(str)

    def __init__(self, prompt):
        super().__init__()
        self.prompt = prompt

    def run(self):
        try:
            if not API_KEY:
                self.finished.emit("哎呀，你還沒在 .env 中填入 API 金鑰喔！")
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
        if not self.voice_enabled:
            return

        def run_tts():
            try:
                tts = gTTS(text=text, lang='zh-TW', slow=False)
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
                    temp_filename = fp.name
                tts.save(temp_filename)
                
                playsound_path = temp_filename
                from playsound import playsound
                playsound(playsound_path)
                try:
                    os.remove(temp_filename)
                except:
                    pass
            except Exception as e:
                print(f"語音播放失敗: {e}")

        threading.Thread(target=run_tts, daemon=True).start()

    def __init__(self):
        super().__init__()
        self.favorability = 50       
        self.voice_enabled = True     
        self.last_interaction_time = time.time()  
        
        self.initUI()
        self.initAnimation()
        self.initMovement()
        self.initRandomSpeaking()    
        self.initNeglectTimer()      
        self.initDiscordRPC()        
        self.initSystemMonitor()     
        
        # 👈 【新增】啟動後自動播報天氣問候
        QTimer.singleShot(2000, self.check_weather_and_greet)

    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)  
        
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
            print(f"Discord RPC 連線提示: {e}")

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

    def initRandomSpeaking(self):
        self.random_speak_timer = QTimer(self)
        self.random_speak_timer.timeout.connect(self.try_random_speak)
        self.random_speak_timer.start(15000)

    def try_random_speak(self):
        if self.dragging or self.bubble_widget.isVisible():
            return

        if random.random() < 0.3:
            if self.favorability >= 90:
                quotes = [
                    "最喜歡跟主人在一起了！啾咪~ 💕",
                    "主人看我一眼嘛，我好無聊喔~ ✨",
                    "只要能陪著主人，去哪裡都可以！",
                    "抱抱~ 主人今天有沒有想我呀？🥰"
                ]
            elif self.favorability >= 80:
                quotes = [
                    "主人主人，今天心情很好耶！✨",
                    "一直在這裡陪著你喔~",
                    "工作辛苦了！摸摸我休息一下吧💕",
                    "有我在幫你打氣，今天一定沒問題的！"
                ]
            elif self.favorability >= 50:
                quotes = [
                    "你在忙嗎？不要累壞囉~", 
                    "好想吃點好吃的喔 🍖", 
                    "發呆中... 💤",
                    "伸個懶腰~ 唔哇..."
                ]
            else:
                quotes = [
                    "哼...才沒有一直偷看你呢！", 
                    "好無聊喔，來陪我聊天啦！", 
                    "有點餓了，要不要餵我一下？",
                    "哼，你都不理人家..."
                ]

            text = random.choice(quotes)
            self.show_speech_bubble(text)
            self.speak_text(text)

    def initNeglectTimer(self):
        self.neglect_timer = QTimer(self)
        self.neglect_timer.timeout.connect(self.check_neglect)
        self.neglect_timer.start(30000)

    def check_neglect(self):
        if self.dragging or self.bubble_widget.isVisible() or self.favorability <= 0:
            return

        current_time = time.time()
        if current_time - self.last_interaction_time > 60:
            self.favorability = max(self.favorability - 5, 0)
            text = "哼，都都不理我..."
            self.show_speech_bubble(text)
            self.speak_text(text)
            self.update_discord_status(f"好感度下降了 ({self.favorability}) 💢")
            self.last_interaction_time = current_time

    def initSystemMonitor(self):
        self.cpu_alert_cooldown = 0  
        self.monitor_timer = QTimer(self)
        self.monitor_timer.timeout.connect(self.check_system_resources)
        self.monitor_timer.start(10000)  

    def check_system_resources(self):
        if self.bubble_widget.isVisible() or self.dragging:
            return

        try:
            cpu_usage = psutil.cpu_percent(interval=None)
            current_time = time.time()

            if cpu_usage > 85 and current_time - self.cpu_alert_cooldown > 180:
                text = f"⚠️ CPU 正在燃燒！(使用率 {cpu_usage:.0f}%) 主人小心當機喔！"
                self.show_speech_bubble(text)
                self.speak_text("哇！電腦好燙，CPU 負荷太高囉！")
                self.cpu_alert_cooldown = current_time
        except Exception as e:
            print(f"系統監控錯誤: {e}")

    # 👈 【新增】取得天氣與問候邏輯
    def get_weather_info(self):
        try:
            # 利用 wttr.in 取得目前IP所在地的簡短天氣 (format: 天氣狀況 氣溫)
            response = requests.get("https://wttr.in/?format=%C+%t", timeout=3)
            if response.status_code == 200:
                weather_text = response.text.strip()
                return weather_text
        except:
            pass
        return None

    def check_weather_and_greet(self):
        weather = self.get_weather_info()
        if weather:
            greeting = f"主人早安/午安！外面氣象顯示：{weather} 唷！氣候變化大要注意身體喔~ 🌤️"
        else:
            greeting = "哈囉主人！今天也要元氣滿滿地一起加油喔！✨"
        
        self.show_speech_bubble(greeting)
        self.speak_text(greeting)

    def manual_check_weather(self):
        self.last_interaction_time = time.time()
        self.show_speech_bubble("正在查詢外面的天氣狀況... 🛰️")
        
        def fetch_async():
            weather = self.get_weather_info()
            if weather:
                msg = f"報告主人！目前外面天氣：{weather} ⛅"
            else:
                msg = "哎呀，連線氣象衛星失敗了，不過今天心情好就是好天氣！"
            self.show_speech_bubble(msg)
            self.speak_text(msg)
            self.update_discord_status("查詢天氣中 ⛅")

        threading.Thread(target=fetch_async, daemon=True).start()

    def set_pomodoro_timer(self):
        self.last_interaction_time = time.time()
        minutes, ok = QInputDialog.getInt(self, "設定休息鬧鐘", "請輸入幾分鐘後提醒你休息：", 25, 1, 180, 1)
        if ok and minutes:
            ms = minutes * 60 * 1000
            if hasattr(self, 'pomodoro_qtimer'):
                self.pomodoro_qtimer.stop()
            
            self.pomodoro_qtimer = QTimer(self)
            self.pomodoro_qtimer.setSingleShot(True)
            self.pomodoro_qtimer.timeout.connect(self.alarm_triggered)
            self.pomodoro_qtimer.start(ms)
            
            text = f"好滴！已設定 {minutes} 分鐘後提醒你休息喔！⏰"
            self.show_speech_bubble(text)
            self.speak_text(text)
            self.update_discord_status(f"設定了 {minutes} 分鐘鬧鐘 ⏰")

    def alarm_triggered(self):
        text = "叮咚！時間到囉！快起來走動、喝個水休息一下吧！🌟"
        self.show_speech_bubble(text)
        self.speak_text("主人主人！鬧鐘響囉，快起來休息！")
        try:
            winsound.Beep(1000, 500)
            winsound.Beep(1200, 500)
        except:
            pass
        self.update_discord_status("鬧鐘響起提醒休息中 🔔")

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
        
        padding = 10
        w = scaled_pixmap.width() + padding
        h = scaled_pixmap.height() + padding

        self.resize(w, h)
        self.label.resize(w, h)
        self.label.setPixmap(scaled_pixmap)

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
            self.last_interaction_time = time.time()
            self.open_ai_chat()
            event.accept()

    def open_ai_chat(self):
        text, ok = QInputDialog.getText(self, "與桌寵對話", "你想對桌寵說什麼？")
        if ok and text:
            self.show_speech_bubble("思考中...")
            self.update_discord_status("正在跟主人聊天 💬")
            self.favorability = min(self.favorability + 1, 100)
            
            self.ai_worker = AIWorker(text)
            self.ai_worker.finished.connect(self.handle_ai_response)
            self.ai_worker.start()

    def handle_ai_response(self, reply_text):
        self.show_speech_bubble(reply_text)
        self.update_discord_status("正在跟主人聊天 💬")
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
            self.last_interaction_time = time.time()
            
            try:
                winsound.Beep(800, 100)
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

    def play_rps_game(self):
        self.last_interaction_time = time.time()
        items = ["剪刀", "石頭", "布"]
        user_choice, ok = QInputDialog.getItem(self, "猜拳小遊戲", "請選擇你的出拳：", items, 0, False)
        
        if ok and user_choice:
            pet_choice = random.choice(items)
            
            if user_choice == pet_choice:
                result_text = f"我出【{pet_choice}】。平手耶！"
                self.speak_text("我們平手呢！")
            elif (
                (user_choice == "剪刀" and pet_choice == "布") or
                (user_choice == "石頭" and pet_choice == "剪刀") or
                (user_choice == "布" and pet_choice == "石頭")
            ):
                result_text = f"我出【{pet_choice}】。你贏了！好厲害～"
                self.speak_text("哼，算你厲害，讓你贏一次！")
                self.favorability = min(self.favorability + 3, 100)
            else:
                result_text = f"我出【{pet_choice}】。我贏啦！哈哈～"
                self.speak_text("耶！我贏了，再來一次嗎？")
                self.favorability = max(self.favorability - 2, 0)
                
            self.show_speech_bubble(result_text)
            self.update_discord_status("正在玩猜拳遊戲 🎮")

    def show_context_menu(self, pos):
        menu = QMenu(self)
        
        if self.favorability >= 80:
            status_text = "❤️ 好感度: 很高 (非常黏你)"
        elif self.favorability >= 50:
            status_text = "💛 好感度: 普通 (相處融洽)"
        else:
            status_text = "💢 好感度: 偏低 (有點傲嬌)"

        favor_action = menu.addAction(status_text)
        favor_action.setEnabled(False)
        
        menu.addSeparator()
        
        pet_action = menu.addAction("摸摸頭 (增加好感)")
        punch_action = menu.addAction("💥 打她一拳 (減少好感)")
        rps_action = menu.addAction("🎮 玩猜拳小遊戲")
        alarm_action = menu.addAction("⏰ 設定休息鬧鐘")  
        weather_action = menu.addAction("🌤️ 查詢目前天氣")  # 👈 【新增】右鍵天氣查詢選項
        
        voice_status_text = "🔊 語音朗讀：開啟" if self.voice_enabled else "🔇 語音朗讀：關閉"
        voice_action = menu.addAction(voice_status_text)
        
        opacity_menu = menu.addMenu("調整透明度")
        action_100 = opacity_menu.addAction("完全不透明 (1.0)")
        action_80 = opacity_menu.addAction("半透明 (0.8)")
        action_50 = opacity_menu.addAction("高透明 (0.5)")
        
        menu.addSeparator()
        exit_action = menu.addAction("退出桌寵")
        
        action = menu.exec_(pos)
        self.last_interaction_time = time.time()
        
        if action == pet_action:
            self.favorability = min(self.favorability + 5, 100)
            msg = f"哼哼~被摸頭了，好感度上升！(目前: {self.favorability})"
            self.show_speech_bubble(msg)
            self.speak_text("哼哼，感覺還不錯嘛！")
            self.update_discord_status(f"好感度 {self.favorability} 🐾")
        elif action == punch_action:
            self.favorability = max(self.favorability - 5, 0)
            msg = f"好痛！你幹嘛打我... (目前好感度: {self.favorability})"
            self.show_speech_bubble(msg)
            self.speak_text("好痛！你為什麼要打我，太過分了！")
            try:
                winsound.Beep(300, 200)
            except:
                pass
            self.update_discord_status(f"被打了一拳，好感度 {self.favorability} 💢")
        elif action == rps_action:
            self.play_rps_game()
        elif action == alarm_action:
            self.set_pomodoro_timer()
        elif action == weather_action:  # 👈 【新增】處理天氣點擊
            self.manual_check_weather()
        elif action == voice_action:
            self.voice_enabled = not self.voice_enabled
            state_str = "開啟" if self.voice_enabled else "關閉"
            self.show_speech_bubble(f"語音功能已{state_str}囉！")
        elif action == action_100:
            self.setWindowOpacity(1.0)
        elif action == action_80:
            self.setWindowOpacity(0.8)
        elif action == action_50:
            self.setWindowOpacity(0.5)
        elif action == exit_action:
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