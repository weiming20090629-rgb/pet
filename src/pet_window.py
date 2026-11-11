import sys
import random
import os
import time
import json
import psutil
from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QInputDialog
from PyQt5.QtGui import QCursor
from pypresence import Presence
import winsound
from gtts import gTTS
import tempfile
import threading

from .styles import CONTEXT_MENU_STYLE, SPEECH_BUBBLE_STYLE
from .workers import WeatherWorker
from .punishment import PunishmentManager
from .pet_animation import PetAnimationManager
from .pet_mouse_handler import PetMouseHandler

script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(script_dir, "pet_save.json")
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "1566775719961427970")

class DesktopPet(QWidget):
    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.favorability = data.get("favorability", 50)
                    self.coins = data.get("coins", 0)
            except:
                self.favorability = 50
                self.coins = 0
        else:
            self.favorability = 50
            self.coins = 0

    def save_data(self):
        try:
            data = {
                "favorability": self.favorability,
                "coins": self.coins
            }
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"存檔失敗: {e}")

    def speak_text(self, text):
        if not self.voice_enabled:
            return

        def run_tts():
            temp_filename = None
            try:
                tts = gTTS(text=text, lang='zh-TW', slow=False)
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
                    temp_filename = fp.name
                tts.save(temp_filename)
                
                from playsound import playsound
                playsound(temp_filename)
            except Exception as e:
                print(f"語音播放失敗: {e}")
            finally:
                if temp_filename and os.path.exists(temp_filename):
                    try:
                        time.sleep(0.5)
                        os.remove(temp_filename)
                    except:
                        pass

        threading.Thread(target=run_tts, daemon=True).start()

    def __init__(self):
        super().__init__()
        self.load_data()  
        self.voice_enabled = True     
        self.last_interaction_time = time.time()  
        self.todo_list = []  
        self.is_working = False  
        self.is_reporting_work = False  
        
        self.initUI()
        
        # ⬇️【加在這裡】讓滑鼠移到桌寵上時變成手形游標
        self.setMouseTracking(True)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        
        if PetAnimationManager.init_animations(self, script_dir):
            self.update_image()
            self.timer = QTimer(self)
            self.timer.timeout.connect(lambda: PetAnimationManager.next_frame(self))
            self.timer.start(150)

        self.initMovement()
        self.initRandomSpeaking()    
        self.initNeglectTimer()     
        self.initDiscordRPC()        
        self.initSystemMonitor()     
        self.initPunishmentTimer()   
        
        QTimer.singleShot(2000, self.check_weather_and_greet)

    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)  
        
        self.bubble_widget = QWidget(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
        self.bubble_widget.setAttribute(Qt.WA_TranslucentBackground, True)
        
        self.bubble_label = QLabel(self.bubble_widget)
        self.bubble_label.setStyleSheet(SPEECH_BUBBLE_STYLE)
        self.bubble_widget.hide()
        
        self.dragging = False
        self.offset = QPoint()
        self.direction = 1
        self.scale_factor = 1.0
        self.is_walking = True

    def initDiscordRPC(self):
        try:
            self.RPC = Presence(DISCORD_CLIENT_ID)
            self.RPC.connect()
            self.start_time = time.time()
            self.RPC.update(
                state=f"金幣: {self.coins} 💰 | 好感度: {self.favorability}",
                details="桌面生活秘書與打工養成中",
                start=self.start_time,
                large_image="pet_idle",
                large_text="桌面寵物"
            )
        except Exception:
            pass

    def update_discord_status(self, state_text):
        try:
            if hasattr(self, 'RPC'):
                self.RPC.update(
                    state=state_text,
                    details=f"金幣: {self.coins} 💰 | 好感度: {self.favorability}",
                    start=self.start_time,
                    large_image="pet_idle",
                    large_text="桌面寵物"
                )
        except:
            pass

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
        if self.dragging or self.bubble_widget.isVisible() or self.is_working or self.is_reporting_work:
            return

        if random.random() < 0.3:
            if self.favorability <= 0:
                quotes = [
                    "氣死我了！好感度歸零，準備接受制裁吧！🔥",
                    "哼！不把我安撫好，我要把所有視窗通關囉！💢",
                    "快點跟我道歉！否則通通關掉！"
                ]
            elif self.favorability >= 90:
                quotes = [
                    f"目前有 {self.coins} 個金幣呢！主人要買什麼給我？💕",
                    "最喜歡跟主人在一起了！啾咪~ 💕",
                    "主人看我一眼嘛，我好無聊喔~ ✨"
                ]
            else:
                quotes = [
                    f"現在存了 {self.coins} 金幣，打工賺錢好累喔~ 💰",
                    "你在忙嗎？不要累壞囉~", 
                    "發呆中... 💤"
                ]

            text = random.choice(quotes)
            self.show_speech_bubble(text)
            self.speak_text(text)

    def initNeglectTimer(self):
        self.neglect_timer = QTimer(self)
        self.neglect_timer.timeout.connect(self.check_neglect)
        self.neglect_timer.start(30000)

    def check_neglect(self):
        if self.dragging or self.bubble_widget.isVisible() or self.is_working or self.is_reporting_work or self.favorability <= 0:
            return

        current_time = time.time()
        if current_time - self.last_interaction_time > 60:
            self.favorability = max(self.favorability - 5, 0)
            self.save_data()
            text = "哼，都都不理我..."
            self.show_speech_bubble(text)
            self.speak_text(text)
            self.update_discord_status(f"好感度下降 ({self.favorability}) 💢")
            self.last_interaction_time = current_time

    def initPunishmentTimer(self):
        self.punishment_timer = QTimer(self)
        self.punishment_timer.timeout.connect(self.execute_punishment_loop)
        self.punishment_timer.start(10000)  

    def execute_punishment_loop(self):
        if self.favorability <= 0:
            warning_text = "💢 好感度歸零！本小姐要發飆關閉所有視窗囉！"
            self.show_speech_bubble(warning_text)
            self.speak_text("好感度歸零！我要把所有視窗通通關掉！")
            QTimer.singleShot(3000, lambda: PunishmentManager.close_all_other_windows(self, self.bubble_widget))

    def initSystemMonitor(self):
        self.system_alert_cooldown = 0  
        self.monitor_timer = QTimer(self)
        self.monitor_timer.timeout.connect(self.check_system_resources)
        self.monitor_timer.start(10000)  

    def check_system_resources(self):
        if self.bubble_widget.isVisible() or self.dragging:
            return

        try:
            cpu_usage = psutil.cpu_percent(interval=None)
            ram_info = psutil.virtual_memory()
            ram_usage = ram_info.percent  
            current_time = time.time()

            if (cpu_usage > 85 or ram_usage > 85) and current_time - self.system_alert_cooldown > 180:
                if cpu_usage > 85 and ram_usage > 85:
                    text = f"⚠️ 電腦負荷過重！CPU: {cpu_usage:.0f}% | RAM: {ram_usage:.0f}% 主人小心當機！"
                    speech = "哇！CPU跟記憶體都快爆掉囉，主人注意一下！"
                elif cpu_usage > 85:
                    text = f"⚠️ CPU 正在燃燒！(使用率 {cpu_usage:.0f}%) 主人小心當機喔！"
                    speech = "哇！電腦好燙，CPU 負荷太高囉！"
                else:
                    text = f"⚠️ 記憶體快滿啦！(RAM 使用率 {ram_usage:.0f}%) 記得清理背景程式喔！"
                    speech = "記憶體快被塞滿囉，主人要不要關掉一些分頁？"

                self.show_speech_bubble(text)
                self.speak_text(speech)
                self.system_alert_cooldown = current_time
        except Exception as e:
            print(f"系統監控錯誤: {e}")

    def restore_normal_clothes(self):
        self.is_reporting_work = False
        self.update_image()

    def update_image(self):
        PetAnimationManager.update_image(self)

    def check_weather_and_greet(self):
        self.weather_worker = WeatherWorker()
        self.weather_worker.finished.connect(self.handle_initial_weather)
        self.weather_worker.start()

    def handle_initial_weather(self, weather):
        if weather:
            greeting = f"主人早安/午安！外面氣象顯示：{weather} 唷！目前金幣 {self.coins} 枚~ 🌤️"
        else:
            greeting = f"哈囉主人！今天也要元氣滿滿地賺金幣喔！(目前金幣: {self.coins}) ✨"
        self.show_speech_bubble(greeting)
        self.speak_text(greeting)

    def manual_check_weather(self):
        self.last_interaction_time = time.time()
        self.show_speech_bubble("正在查詢外面的天氣狀況... 🛰️")
        
        self.weather_worker = WeatherWorker()
        self.weather_worker.finished.connect(self.handle_manual_weather)
        self.weather_worker.start()

    def handle_manual_weather(self, weather):
        if weather:
            msg = f"報告主人！目前外面天氣：{weather} ⛅"
        else:
            msg = "哎呀，連線氣象衛星失敗了，不過今天心情好就是好天氣！"
        self.show_speech_bubble(msg)
        self.speak_text(msg)
        self.update_discord_status("查詢天氣中 ⛅")

    def take_screenshot(self):
        self.last_interaction_time = time.time()
        self.hide()  
        QTimer.singleShot(300, self._capture_screen_process)

    def _capture_screen_process(self):
        try:
            screen = QApplication.primaryScreen()
            screenshot = screen.grabWindow(0)
            
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            if not os.path.exists(desktop_path):
                desktop_path = script_dir
                
            filename = f"DesktopPet_Screenshot_{int(time.time())}.png"
            full_path = os.path.join(desktop_path, filename)
            
            screenshot.save(full_path, "png")
            
            self.show()  
            try:
                winsound.Beep(1200, 150)
            except:
                pass
                
            msg = "喀擦！畫面已經截圖並存到桌面囉！📸"
            self.show_speech_bubble(msg)
            self.speak_text("截圖成功！已經幫主人存到桌面上囉！")
            self.update_discord_status("截圖小幫手運作中 📸")
        except Exception as e:
            self.show()
            print(f"截圖失敗: {e}")

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
        if self.is_working or self.is_reporting_work:
            return

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
        if self.dragging or self.is_working or self.is_reporting_work:
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

    def wheelEvent(self, event):
        PetMouseHandler.handle_wheel_event(self, event)

    def mouseDoubleClickEvent(self, event):
        PetMouseHandler.handle_double_click(self, event)

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
        PetMouseHandler.handle_mouse_press(self, event)

    def mouseMoveEvent(self, event):
        PetMouseHandler.handle_mouse_move(self, event)

    def mouseReleaseEvent(self, event):
        PetMouseHandler.handle_mouse_release(self, event)

    def closeEvent(self, event):
        try:
            if hasattr(self, 'RPC'):
                self.RPC.close()
        except:
            pass
        self.bubble_widget.close()
        event.accept()