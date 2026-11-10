import sys
import random
import os
import time
import json
import psutil
import requests
from google import genai
from PyQt5.QtCore import Qt, QPoint, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QTransform
from PyQt5.QtWidgets import QApplication, QLabel, QMenu, QWidget, QInputDialog, QMessageBox
from pypresence import Presence
import winsound
from gtts import gTTS
import tempfile
import threading

# 引入 win32 相關套件來實現關閉其他視窗功能
try:
    import win32gui
    import win32process
    import win32con
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "1566775719961427970")

script_dir = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(script_dir, "pet_save.json")


class AIWorker(QThread):
    finished = pyqtSignal(str)

    def __init__(self, prompt):
        super().__init__()
        self.prompt = prompt

    def run(self):
        try:
            if not API_KEY:
                self.finished.emit("哎呀，你還沒在 .env 中填入 GEMINI_API_KEY 金鑰喔！")
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


class WeatherWorker(QThread):
    finished = pyqtSignal(str)

    def run(self):
        try:
            headers = {"User-Agent": "curl/7.68.0"}
            response = requests.get("https://wttr.in/?format=%C+%t", headers=headers, timeout=8)
            
            if response.status_code == 200:
                text = response.text.strip()
                if "<html" in text.lower() or "<div" in text.lower():
                    self.finished.emit("")
                else:
                    self.finished.emit(text)
            else:
                self.finished.emit("")
        except Exception as e:
            print(f"天氣連線錯誤: {e}")
            self.finished.emit("")


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
        self.initAnimation()
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

        work_start_path = os.path.join(script_dir, 'work_start.png')
        self.work_start_pixmap = QPixmap(work_start_path)

        self.work_loop_files = ['work_1.png', 'work_2.png', 'work_3.png']
        self.work_loop_frames = []
        for file in self.work_loop_files:
            file_path = os.path.join(script_dir, file)
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                self.work_loop_frames.append(pixmap)

        if not self.frames:
            self.label.setText("🐾 找不到圖片")
            self.label.setStyleSheet(
                "color: white; background-color: rgba(0, 0, 0, 160); "
                "font-size: 14px; border-radius: 8px; padding: 10px;"
            )
            self.resize(200, 60)
            return

        self.current_frame = 0
        self.current_work_loop_frame = 0
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
            QTimer.singleShot(3000, self.close_all_other_windows)

    # 👈 【核心修改】將隨機關閉改成關閉所有其他合法視窗
    def close_all_other_windows(self):
        if not HAS_WIN32:
            print("未安裝 pywin32，無法執行關閉視窗功能")
            return

        current_hwnd = int(self.winId())  # 桌寵主視窗句柄
        bubble_hwnd = int(self.bubble_widget.winId()) if self.bubble_widget else 0  # 對話框句柄
        current_pid = os.getpid()  # 當前桌寵程式自身的 PID
        target_hwnds = []

        def enum_windows_callback(hwnd, extra):
            nonlocal target_hwnds
            if win32gui.IsWindowVisible(hwnd):
                # 排除桌寵主視窗以及對話框視窗
                if hwnd == current_hwnd or hwnd == bubble_hwnd:
                    return
                
                window_title = win32gui.GetWindowText(hwnd)
                if not window_title or len(window_title.strip()) == 0:
                    return
                
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                
                # 排除自己的 PID
                if pid == current_pid:
                    return

                try:
                    p = psutil.Process(pid)
                    p_name = p.name().lower()
                    
                    # 👈 【核心修正】加入終端機與命令列工具黑名單，絕對不關閉 PowerShell、CMD、終端機或編輯器
                    blacklisted_processes = [
                        "explorer.exe", "dwm.exe", "taskhostw.exe", 
                        "python.exe", "code.exe", 
                        "powershell.exe", "cmd.exe", "windowsterminal.exe", "wt.exe"
                    ]
                    if p_name in blacklisted_processes:
                        return
                except:
                    return

                target_hwnds.append(hwnd)

        try:
            win32gui.EnumWindows(enum_windows_callback, None)
            for hwnd in target_hwnds:
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            print(f"已成功關閉所有其他視窗（共 {len(target_hwnds)} 個）！")
        except Exception as e:
            print(f"執行視窗懲罰失敗: {e}")

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

    def start_part_time_job(self):
        if self.is_working or self.is_reporting_work:
            self.show_speech_bubble("我正在打工賺錢中耶，別打擾我！💼")
            return

        self.last_interaction_time = time.time()
        job_types = [
            ("超商打工 (輕鬆)", 1, 10, 30),      
            ("咖啡廳幫忙 (一般)", 3, 35, 60),
            ("文書外包 (高薪)", 5, 70, 100)
        ]
        
        items = [f"{j[0]} - 耗時 {j[1]} 分鐘 (賺取 {j[2]} 金幣)" for j in job_types]
        choice, ok = QInputDialog.getItem(self, "選擇打工類型", "請選擇要進行的工作：", items, 0, False)
        
        if ok and choice:
            selected_job = None
            for j in job_types:
                if j[0] in choice:
                    selected_job = j
                    break
            
            if selected_job:
                name, duration_min, reward_coins, reward_favor = selected_job
                self.is_working = True
                self.current_work_loop_frame = 0  
                self.update_image() 
                
                msg = f"出發去【{name}】囉！大約 {duration_min} 分鐘後回來賺錢！💰"
                self.show_speech_bubble(msg)
                self.speak_text(f"我去打工賺錢囉，等我回來！")
                self.update_discord_status(f"正在進行 {name} 💼")
                
                ms = duration_min * 60 * 1000
                QTimer.singleShot(ms, lambda: self.finish_part_time_job(reward_coins, reward_favor, name))

    def finish_part_time_job(self, reward_coins, reward_favor, job_name):
        self.is_working = False
        self.is_reporting_work = True 
        self.update_image() 
        
        self.coins += reward_coins
        self.favorability = min(self.favorability + reward_favor, 100)
        self.save_data()
        
        msg = f"打工結束！完成【{job_name}】，獲得了 {reward_coins} 金幣與好感度！🎉"
        self.show_speech_bubble(msg)
        self.speak_text(f"打工回來啦！賺到了好多的金幣呢！")
        try:
            winsound.Beep(1000, 200)
            winsound.Beep(1400, 200)
        except:
            pass
        self.update_discord_status(f"金幣: {self.coins} 💰")
        
        QTimer.singleShot(4000, self.restore_normal_clothes)

    def restore_normal_clothes(self):
        self.is_reporting_work = False
        self.update_image()

    def show_wallet(self):
        self.last_interaction_time = time.time()
        coins_display = self.coins
        msg = f"💰 目前擁有金幣：{coins_display} 枚\n❤️ 目前好感度：{self.favorability} 點\n\n快去右鍵選單讓桌寵去打工賺更多金幣吧！"
        QMessageBox.information(self, "錢包與狀態", msg)

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

    def add_todo_item(self):
        self.last_interaction_time = time.time()
        task, ok1 = QInputDialog.getText(self, "新增待辦事項", "請輸入代辦內容：")
        if ok1 and task:
            minutes, ok2 = QInputDialog.getInt(self, "設定提醒時間", f"幾分鐘後提醒你執行【{task}】？", 10, 1, 300, 1)
            if ok2 and minutes:
                ms = minutes * 60 * 1000
                self.todo_list.append(task)
                
                timer = QTimer(self)
                timer.setSingleShot(True)
                timer.timeout.connect(lambda: self.trigger_todo_alarm(task))
                timer.start(ms)
                
                msg = f"已記下！會在 {minutes} 分鐘後提醒你：{task} 📝"
                self.show_speech_bubble(msg)
                self.speak_text(f"好滴，我會記得提醒你做：{task}")
                self.update_discord_status(f"待辦事項：{task} 📝")

    def trigger_todo_alarm(self, task):
        msg = f"叮咚！時間到囉！該處理這件事了：【{task}】💪"
        self.show_speech_bubble(msg)
        self.speak_text(f"主人！時間到了，快去處理：{task}")
        try:
            winsound.Beep(900, 400)
            winsound.Beep(1100, 400)
        except:
            pass
        self.update_discord_status(f"提醒完成事項：{task} 🔔")

    def show_todo_list(self):
        self.last_interaction_time = time.time()
        if not self.todo_list:
            msg = "目前沒有任何待辦事項喔！過得很輕鬆呢~ ✨"
        else:
            msg = "目前的待辦清單：\n" + "\n".join([f"• {t}" for t in self.todo_list])
        QMessageBox.information(self, "待辦事項總覽", msg)

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

    def update_image(self):
        if not self.frames:
            return

        if self.is_reporting_work:
            pixmap = self.work_start_pixmap if not self.work_start_pixmap.isNull() else self.frames[0]
        elif self.is_working:
            if self.work_loop_frames:
                pixmap = self.work_loop_frames[self.current_work_loop_frame]
            else:
                pixmap = self.work_start_pixmap if not self.work_start_pixmap.isNull() else self.frames[0]
        elif self.dragging:
            pixmap = self.drag_pixmap if not self.drag_pixmap.isNull() else self.frames[0]
        elif not self.is_walking and not self.idle_pixmap.isNull():
            pixmap = self.idle_pixmap
        else:
            pixmap = self.frames[self.current_frame]

        transform = QTransform()
        if self.direction == -1 and not self.dragging and not self.is_working and not self.is_reporting_work:
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
        
        if self.is_working:
            if self.work_loop_frames:
                self.current_work_loop_frame = (self.current_work_loop_frame + 1) % len(self.work_loop_frames)
                self.update_image()
            return

        if self.is_reporting_work:
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
            self.save_data()
            
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
                
            self.save_data()
            self.show_speech_bubble(result_text)
            self.update_discord_status("正在玩猜拳遊戲 🎮")

    def show_context_menu(self, pos):
        menu = QMenu(self)
        
        if self.favorability >= 80:
            status_text = f"❤️ 好感度: 很高 | 💰 金幣: {self.coins}"
        elif self.favorability >= 50:
            status_text = f"💛 好感度: 普通 | 💰 金幣: {self.coins}"
        elif self.favorability > 0:
            status_text = f"💢 好感度: 偏低 (快歸零囉) | 💰 金幣: {self.coins}"
        else:
            status_text = f"🔥 好感度: 歸零 (黑化制裁中) | 💰 金幣: {self.coins}"

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
            self.save_data()
            msg = f"哼哼~被摸頭了，好感度上升！(目前: {self.favorability})"
            self.show_speech_bubble(msg)
            self.speak_text("哼哼，感覺還不錯嘛！")
            self.update_discord_status(f"好感度 {self.favorability} 🐾")
        elif action == punch_action:
            self.favorability = max(self.favorability - 5, 0)
            self.save_data()
            msg = f"好痛！你幹嘛打我... (目前好感度: {self.favorability})"
            self.show_speech_bubble(msg)
            self.speak_text("好痛！你為什麼要打我，太過分了！")
            try:
                winsound.Beep(300, 200)
            except:
                pass
            self.update_discord_status(f"被打了一拳，好感度 {self.favorability} 💢")
        elif action == job_action:
            self.start_part_time_job()
        elif action == wallet_action:
            self.show_wallet()
        elif action == rps_action:
            self.play_rps_game()
        elif action == alarm_action:
            self.set_pomodoro_timer()
        elif action == weather_action:
            self.manual_check_weather()
        elif action == add_todo_action:
            self.add_todo_item()
        elif action == view_todo_action:
            self.show_todo_list()
        elif action == screenshot_action:
            self.take_screenshot()
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