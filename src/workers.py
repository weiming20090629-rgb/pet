import os
import requests
from PyQt5.QtCore import QThread, pyqtSignal
from google import genai

API_KEY = os.getenv("GEMINI_API_KEY")

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