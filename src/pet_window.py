import random
import os
import time
import json
from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QSystemTrayIcon, QMenu
from PyQt5.QtGui import QCursor, QIcon

from .styles import SPEECH_BUBBLE_STYLE
from .workers import WeatherWorker
from .pet_animation import PetAnimationManager
from .pet_mouse_handler import PetMouseHandler
from .pet_voice import PetVoiceManager
from .pet_monitors import PetMonitorManager
from .pet_menu import PetMenuManager

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

    def _clamp_float(self, value, min_val, max_val, default):
        try:
            num = float(value)
        except (TypeError, ValueError):
            return default
        return max(min_val, min(max_val, num))

    def load_data(self):
        default_inv = {"shield": 0, "charm": 0}
        default_settings = {
            "voice_enabled": True,
            "voice_volume": 0.8,
            "opacity": 1.0,
            "scale_factor": 1.0,
            "skin": "default",
        }

        self.favorability = 50
        self.coins = 0
        self.satiety = 80
        self.portfolio = {}
        self.watchlist = ["2330", "0050", "NVDA", "AAPL"]
        self.trade_history = []
        self.inventory = dict(default_inv)
        self.settings = dict(default_settings)

        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.favorability = data.get("favorability", 50)
                    self.coins = data.get("coins", 0)
                    self.satiety = self._clamp_satiety(data.get("satiety", 80))
                    self.portfolio = (
                        data.get("portfolio", {})
                        if isinstance(data.get("portfolio"), dict)
                        else {}
                    )
                    self.watchlist = data.get(
                        "watchlist", ["2330", "0050", "NVDA", "AAPL"]
                    )
                    self.trade_history = data.get("trade_history", [])

                    inv = data.get("inventory", {})
                    if isinstance(inv, dict):
                        self.inventory = {
                            "shield": int(inv.get("shield", 0) or 0),
                            "charm": int(inv.get("charm", 0) or 0),
                        }

                    raw_settings = data.get("settings", {})
                    if isinstance(raw_settings, dict):
                        self.settings = {
                            "voice_enabled": bool(
                                raw_settings.get("voice_enabled", True)
                            ),
                            "voice_volume": self._clamp_float(
                                raw_settings.get("voice_volume", 0.8), 0.0, 1.0, 0.8
                            ),
                            "opacity": self._clamp_float(
                                raw_settings.get("opacity", 1.0), 0.2, 1.0, 1.0
                            ),
                            "scale_factor": self._clamp_float(
                                raw_settings.get("scale_factor", 1.0), 0.4, 2.5, 1.0
                            ),
                            "skin": str(raw_settings.get("skin", "default") or "default"),
                        }
            except Exception:
                pass

        self.voice_enabled = self.settings["voice_enabled"]
        self.voice_volume = self.settings["voice_volume"]
        self.scale_factor = self.settings["scale_factor"]
        self.skin = self.settings["skin"]

    def save_data(self):
        try:
            settings_payload = {
                "voice_enabled": bool(getattr(self, "voice_enabled", True)),
                "voice_volume": self._clamp_float(
                    getattr(self, "voice_volume", 0.8), 0.0, 1.0, 0.8
                ),
                "opacity": self._clamp_float(self.windowOpacity(), 0.2, 1.0, 1.0),
                "scale_factor": self._clamp_float(
                    getattr(self, "scale_factor", 1.0), 0.4, 2.5, 1.0
                ),
                "skin": str(getattr(self, "skin", "default") or "default"),
            }
            self.settings = settings_payload

            data = {
                "favorability": self.favorability,
                "coins": self.coins,
                "satiety": self._clamp_satiety(getattr(self, "satiety", 80)),
                "portfolio": getattr(self, "portfolio", {}),
                "watchlist": getattr(
                    self, "watchlist", ["2330", "0050", "NVDA", "AAPL"]
                ),
                "trade_history": getattr(self, "trade_history", []),
                "inventory": getattr(self, "inventory", {"shield": 0, "charm": 0}),
                "settings": settings_payload,
            }
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"存檔失敗: {e}")

    def get_available_skins(self):
        return PetAnimationManager.list_skins(script_dir)

    def change_skin(self, skin_name):
        if PetAnimationManager.switch_skin(self, script_dir, skin_name):
            self.save_data()
            msg = f"已切換為皮膚：【{self.skin}】✨"
            self.show_speech_bubble(msg)
            self.speak_text(f"換上新造型囉，{self.skin} 好看嗎？")
            self.update_discord_status(f"造型：{self.skin} ✨")
            self._update_tray_icon()

    def initSystemTray(self):
        """建立 Windows 右下角系統工作列（系統托盤）圖示與快捷選單"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        self.tray_icon = QSystemTrayIcon(self)
        self._update_tray_icon()
        self.tray_icon.setToolTip(f"桌面寵物 (好感度: {self.favorability} | 金幣: {self.coins})")

        # 建立托盤右鍵選單
        tray_menu = QMenu()

        show_action = tray_menu.addAction("🐾 喚醒 / 移至螢幕中央")
        show_action.triggered.connect(self.bring_to_front)

        status_action = tray_menu.addAction("👛 查看錢包與狀態")
        status_action.triggered.connect(lambda: PetMenuManager.show_context_menu(self, QCursor.pos()))

        tray_menu.addSeparator()

        exit_action = tray_menu.addAction("❌ 退出桌寵")
        exit_action.triggered.connect(self.close)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _update_tray_icon(self):
        """使用桌寵目前的待機圖或第一張動畫圖作為托盤圖示"""
        if not hasattr(self, "tray_icon"):
            return
        pm = getattr(self, "idle_pixmap", None)
        if pm is None or pm.isNull():
            frames = getattr(self, "frames", [])
            if frames:
                pm = frames[0]
        if pm is not None and not pm.isNull():
            self.tray_icon.setIcon(QIcon(pm))

    def _on_tray_activated(self, reason):
        """左鍵點擊或雙擊系統托盤圖示時，把桌寵移回螢幕中央並置頂"""
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.bring_to_front()

    def bring_to_front(self):
        """將桌寵移回主螢幕中央並顯示在最上層"""
        screen = QApplication.primaryScreen().geometry()
        center_x = (screen.width() - self.width()) // 2
        center_y = (screen.height() - self.height()) // 2
        self.move(center_x, center_y)
        self.show()
        self.raise_()
        self.activateWindow()
        self.show_speech_bubble("主人叫我嗎？我在這裡喔！✨")
   
   
    def speak_text(self, text):
        PetVoiceManager.speak(self, text)

    def update_discord_status(self, state_text):
        PetMonitorManager.update_discord_status(self, state_text)

    def __init__(self):
        super().__init__()
        self.load_data()
        self.last_interaction_time = time.time()
        self.todo_list = []
        self.is_working = False
        self.is_reporting_work = False
        self.current_job_type = "default"

        self.initUI()
        self.setWindowOpacity(self.settings.get("opacity", 1.0))

        self.setMouseTracking(True)
        self.setCursor(QCursor(Qt.PointingHandCursor))

        if PetAnimationManager.init_animations(self, script_dir, self.skin):
            self.update_image()
            self.timer = QTimer(self)
            self.timer.timeout.connect(lambda: PetAnimationManager.next_frame(self))
            self.timer.start(150)

        self.initSystemTray()

        self.initMovement()
        self.initRandomSpeaking()
        PetMonitorManager.init_neglect_timer(self)
        PetMonitorManager.init_satiety_timer(self)
        PetMonitorManager.init_discord_rpc(self, DISCORD_CLIENT_ID)
        PetMonitorManager.init_system_monitor(self)
        PetMonitorManager.init_punishment_timer(self)

        QTimer.singleShot(2000, self.check_weather_and_greet)

    def initUI(self):
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)

        self.bubble_widget = QWidget(
            None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow
        )
        self.bubble_widget.setAttribute(Qt.WA_TranslucentBackground, True)

        self.bubble_label = QLabel(self.bubble_widget)
        self.bubble_label.setStyleSheet(SPEECH_BUBBLE_STYLE)
        self.bubble_widget.hide()

        self.dragging = False
        self.offset = QPoint()
        self.direction = 1
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
        if (
            self.dragging
            or self.bubble_widget.isVisible()
            or self.is_working
            or self.is_reporting_work
        ):
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
        # 1. 停止所有定時器，避免關閉過程中又觸發新任務
        timer_names = [
            "timer",
            "move_timer",
            "change_dir_timer",
            "random_speak_timer",
            "neglect_timer",
            "satiety_timer",
            "monitor_timer",
            "punishment_timer",
            "bubble_timer",
        ]
        for t_name in timer_names:
            t = getattr(self, t_name, None)
            if t is not None and t.isActive():
                t.stop()

        # 2. 安全斷開並等待背景 QThread（AI 聊天、天氣查詢）收尾
        for w_name in ("ai_worker", "weather_worker"):
            worker = getattr(self, w_name, None)
            if worker is not None and worker.isRunning():
                try:
                    worker.finished.disconnect()
                except Exception:
                    pass
                worker.quit()
                worker.wait(1500)  # 最多溫和等待 1.5 秒

        # 3. 存檔、關閉 Discord RPC 與氣泡視窗
        self.save_data()
        PetMonitorManager.close_discord_rpc(self)
        if hasattr(self, "bubble_widget") and self.bubble_widget is not None:
            self.bubble_widget.close()
        if hasattr(self, "tray_icon"): self.tray_icon.hide()

        event.accept()
        QApplication.quit()