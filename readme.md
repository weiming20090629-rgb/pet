# 🐾 PyQt5 桌面互動寵物 (Desktop Pet)

一個基於 PyQt5 與 Google Gemini API 開發的跨平台桌面小寵物！除了能在螢幕上隨機漫遊、隨滾輪自由縮放外，還具備完整的 Gemini AI 語音對話、好感度養成系統、閒置傲嬌提醒、猜拳小遊戲、CPU/RAM 系統監控、氣象問候以及 Discord Rich Presence 狀態顯示。

---

## ✨ 功能亮點

- **🤖 Gemini AI 智慧對話**：雙擊寵物即可開啟對話視窗，由 Gemini 2.5 Flash 模型進行俏皮回應。
- **🗣️ 語音朗讀 (gTTS)**：整合 `gTTS` 與背景執行緒，自動將 AI 回覆與氣泡對話朗讀出來（支援右鍵語音開關）。
- **❤️ 好感度與互動機制**：
  - **摸摸頭**：右鍵選單進行撫摸，提升好感度。
  - **💥 打她一拳**：扣除好感度並觸發生氣語音與提示音。
  - **🎮 猜拳小遊戲**：與桌寵進行剪刀石頭布，贏了可增加好感度！
  - **💢 閒置傲嬌提醒**：若超過 60 秒未互動，會自動扣除好感度並傲嬌抱怨。
- **💬 隨機主動發言**：每隔一段時間根據當前好感度（90+ 超甜、80+ 溫馨、50+ 普通、<50 傲嬌）主動對話。
- **💻 電腦資源監控 (CPU/RAM 小管家)**：即時監控系統負載，當 CPU 使用率過高時跳出提醒。
- **🌤️ 天氣與問候小精靈**：開機與手動點擊時自動查詢當地天氣並給予溫馨提示。
- **⏰ 番茄鐘 / 休息鬧鐘**：可設定定時提醒，時間到會用語音與音效提醒主人休息。
- **🔍 視窗優化與防裁切**：
  - 支援滑鼠滾輪（WheelEvent）動態縮放尺寸。
  - 自動 Padding 與置中對齊，防止縮放邊緣被切割。
  - 右鍵提供多段透明度調整（1.0 / 0.8 / 0.5）。
- **🎮 Discord Rich Presence**：即時在 Discord 個人資料上同步寵物的動態與好感度狀態。

---

## 🛠️ 1. 環境需求與套件安裝 (Environment Setup)

### 系統與 Python 版本
- **OS**: Windows 10 / 11
- **Python**: 3.9+ (建議 3.12+)

### 安裝依賴套件
在終端機執行以下指令安裝所有必要套件：

```bash
pip install PyQt5 google-genai pypresence gTTS "playsound<1.3.0" python-dotenv psutil requests pywin32
```

---

## 🔑 2. 環境變數設定 (.env)

專案根目錄下需包含 `.env` 檔案以讀取 API 金鑰與設定檔。

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

> ⚠️ **注意**：請勿將 `.env` 檔案推送到公共儲存庫。本專案已在 `.gitignore` 中設定排除 `.env`。

---

## 🚀 3. 執行程式 (Run)

在專案目錄下執行：

```bash
python pet.py
```

---

## 🎮 操作指南

| 操作 | 功能說明 |
| :--- | :--- |
| **左鍵拖曳** | 移動桌寵在螢幕上的位置 |
| **左鍵雙擊** | 開啟 Gemini AI 對話視窗 |
| **滾輪上下** | 放大 / 縮小桌寵顯示尺寸 |
| **右鍵點擊** | 開啟功能選單（查看好感度、摸摸頭、打一拳、猜拳遊戲、設定鬧鐘、查詢天氣、切換語音/透明度、退出） |

---

## 📁 專案架構

```text
├── pet.py               # 主程式碼 (PyQt5 介面、動畫、AI、監控與事件處理)
├── .env                 # API Key 與 Discord Client ID 本地設定檔
├── .gitignore           # Git 忽略檔案設定
├── README.md            # 專案說明文件
├── 1.png ~ 8.png        # 走路動畫幀圖片
├── pet_drag.png         # 拖曳時顯示之圖片
└── pet_idle.png         # 發呆時顯示之圖片
```