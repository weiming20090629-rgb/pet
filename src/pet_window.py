import random
import os
import time
import json
from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtWidgets import QApplication, QLabel, QWidget
from PyQt5.QtGui import QCursor

from .styles import SPEECH_BUBBLE_STYLE
from .workers import WeatherWorker
from .pet_animation import PetAnimationManager
from .pet_mouse_handler import PetMouseHandler
from .pet_voice import PetVoiceManager
from .pet_monitors import PetMonitorManager

script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(script_dir, "pet_save.json")
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "1566775719961427970")


class DesktopPet(QWidget):
    def _clamp_satiety(self, value):
        try:
            num = int(value)
        except (TypeError, ValueError):
            num = 80
        return max(0, min(100, num))

    def load_data(self):
        default_inv = {"shield": 0, "charm": 0}
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.favorability = data.get("favorability", 50)
                    self.coins = data.get("coins", 0)
                    self.satiety = self._clamp_satiety(data.get("satiety", 80))
                    self.portfolio = data.get("portfolio", {})
                    self.watchlist = data.get("watchlist", ["2330", "0050", "NVDA", "AAPL"])
                    self.trade_history = data.get("trade_history", [])
                    self.inventory = data.get("inventory", default_inv)
            except Exception:
                self.favorability = 50
                self.coins = 0
                self.satiety = 80
                self.portfolio = {}
                self.watchlist = ["2330", "0050", "NVDA", "AAPL"]
                self.trade_history = []
                self.inventory = default_inv
        else:
            self.favorability = 50
            self.coins = 0
            self.satiety = 80
            self.portfolio = {}
            self.watchlist = ["2330", "0050", "NVDA", "AAPL"]
            self.trade_history = []
            self.inventory = default_inv

    def save_data(self):
        try:
            data = {
                "favorability": self.favorability,
                "coins": self.coins,
                "satiety": self._clamp_satiety(getattr(self, "satiety", 80)),
                "portfolio": getattr(self, "portfolio", {}),
                "watchlist": getattr(self, "watchlist", ["2330", "0050", "NVDA", "AAPL"]),
                "trade_history": getattr(self, "trade_history", []),
                "inventory": getattr(self, "inventory", {"shield": 0, "charm": 0}),
            }
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"存檔失敗: {e}")

    def speak_text(self, text):
        PetVoiceManager.speak(self, text)

    def update_discord_status(self, state_text):
        PetMonitorManager.update_discord_status(self, state_text)

    def __init__(self):
        super().__init__()
        self.voice_volume = 0.8
        self.load_data()
        self.voice_enabled = True
        self.last_interaction_time = time.time()
        self.todo_list = []
        self.is_working = False
        self.is_reporting_work = False

        self.initUI()

        self.setMouseTracking(True)
        self.setCursor(QCursor(Qt.PointingHandCursor))

        if PetAnimationManager.init_animations(self, script_dir):
            self.update_image()
            self.timer = QTimer(self)
            self.timer.timeout.connect(lambda: PetAnimationManager.next_frame(self))
            self.timer.start(150)

        self.initMovement()
        self.initRandomSpeaking()
        PetMonitorManager.init_neglect_timer(self)
        PetMonitorManager.init_satiety_timer(self)
        PetMonitorManager.init_discord_rpc(self, DISCORD_CLIENT_ID)
        PetMonitorManager.init_system_monitor(self)
        PetMonitorManager.init_punishment_timer(self)

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
                    "快點跟我道歉！否則通通關掉！",
                ]
            elif self.favorability >= 90:
                quotes = [
                    f"目前有 {self.coins} 個金幣呢！主人要買什麼給我？💕",
                    "最喜歡跟主人在一起了！啾咪~ 💕",
                    "主人看我一眼嘛，我好無聊喔~ ✨",
                ]
            else:
                quotes = [
                    f"現在存了 {self.coins} 金幣，打工賺錢好累喔~ 💰",
                    "你在忙嗎？不要累壞囉~",
                    "發呆中... 💤",
                ]

            text = random.choice(quotes)
            self.show_speech_bubble(text)
            self.speak_text(text)

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

        if hasattr(self, "bubble_timer"):
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
        PetMonitorManager.close_discord_rpc(self)
        self.bubble_widget.close()
        event.accept()