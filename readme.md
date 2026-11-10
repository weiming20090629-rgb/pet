# 🐾 桌面寵物專案 (Desktop Pet)

一個基於 Python PyQt5 開發的高自由度互動式桌面寵物專案。支援 AI 對話、打工賺錢、待辦事項提醒、好感度系統以及動態視窗安全防護機制。

---

## ✨ 核心特色

- **動態視覺動畫**：支援多幀走路、閒置、拖曳以及專屬打工狀態動畫，自動處理方向翻轉與縮放。
- **AI 智慧對話**：整合 Google Gemini API，雙擊即可開啟視窗進行自然語言互動。
- **打工與經濟系統**：提供多種打工型態與結算機制，累積金幣解鎖後續內容。
- **好感度與黑化制裁**：根據互動增減好感度；好感度歸零時觸發安全的視窗清理機制。
- **系統監控與語音**：內建系統資源監控、天氣查詢與語音朗讀 (gTTS) 支援。

---

## 📂 專案檔案結構


```text
你的桌寵專案資料夾/
│
├── src/                          # 核心 Python 程式碼模組
│   ├── pet_window.py             # 主視窗中樞與計時器管理
│   ├── pet_animation.py          # 圖像載入、動畫更新與方向處理
│   ├── pet_actions.py            # 右鍵選單邏輯、打工與小遊戲功能
│   ├── pet_mouse_handler.py      # 滑鼠事件 (拖曳、雙擊對話、滾輪縮放)
│   ├── punishment.py             # 黑化懲罰與系統視窗安全排除機制
│   └── workers.py                # 背景執行緒 (Gemini AI、天氣 API)
│
├── assets/                       # 視覺資源 (圖片檔 1.png ~ 8.png, pet_idle.png 等)
├── main.py                       # 專案啟動入口
├── .env                          # 環境變數設定檔 (已透過 .gitignore 排除)
├── pet_save.json                 # 本機玩家存檔/金幣記錄 (已透過 .gitignore 排除)
├── .gitignore                    # Git 版本控制排除規則
└── README.md                     # 專案說明文件
```
---
##  Environment Setup

### 系統與 Python 版本
- **OS**: Windows 10 / 11
- **Python**: 3.9+ (建議 3.12+)

### 安裝依賴套件
在終端機執行以下指令安裝所有必要套件：
```bash
pip install PyQt5 google-genai pypresence gTTS "playsound<1.3.0" python-dotenv psutil requests pywin32
```

---
##  環境變數設定 (.env)

### PowerShell 快速建立指令：
```powershell
"GEMINI_API_KEY=你的Gemini金鑰" | Set-Content .env
"DISCORD_CLIENT_ID=你的Discord應用程式ID" | Add-Content .env
```

### `.env` 檔案內容格式：
```env
GEMINI_API_KEY=你的Gemini金鑰
DISCORD_CLIENT_ID=你的Discord應用程式ID
```

---

##  執行程式 (Run)

在專案目錄下執行：

```bash
python main.py
```

---
