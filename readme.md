# 🐾 桌面寵物專案 (Desktop Pet)

一個基於 Python PyQt5 開發的高自由度互動式桌面寵物專案。支援 AI 對話、打工賺錢、模擬股票交易、金幣商店餵食、好感度與飽食度養成，以及動態視窗安全防護機制。

---

## ✨ 核心特色

- **動態視覺動畫**：支援多幀走路、閒置、拖曳以及專屬打工狀態動畫，自動處理方向翻轉與滾輪縮放。
- **AI 智慧對話**：整合 Google Gemini API，雙擊即可開啟視窗進行自然語言互動。
- **打工與模擬股市**：提供多種打工型態，並內建支援即時報價（台股/美股）、5MA/20MA 均線與成交量 K 線圖的專業股票交易室。
- **養成與金幣商店**：具備好感度與隨時間消耗的飽食度系統，可至金幣商店購買珍珠奶茶、甜點或功能道具（如黑化免死金牌、投資幸運符）。
- **好感度與黑化制裁**：根據互動增減好感度；好感度歸零時觸發安全的視窗清理機制（持有免死金牌可自動抵銷）。
- **系統監控與語音**：內建 CPU/RAM 資源監控、即時天氣查詢、Discord 狀態連動與可調音量的語音朗讀 (gTTS + miniaudio)。

---

## 📂 專案檔案結構

```text
你的桌寵專案資料夾/
│
├── src/                          # 核心 Python 程式碼模組
│   ├── pet_window.py             # 主視窗中樞、存檔讀寫與移動控制
│   ├── pet_animation.py          # 圖像載入、動畫更新與方向縮放處理
│   ├── pet_mouse_handler.py      # 滑鼠事件 (拖曳、雙擊對話、滾輪縮放)
│   ├── pet_menu.py               # 右鍵選單建構、音量/透明度滑桿與動作分派
│   ├── pet_actions.py            # 打工系統、猜拳小遊戲、待辦提醒與錢包狀態
│   ├── pet_shop.py               # 金幣商店視窗 (餵食加飽食與好感、功能道具)
│   ├── pet_stock.py              # 專業股票交易室 (即時報價、K線圖、持股與紀錄)
│   ├── pet_monitors.py           # 飽食度定時扣減、冷落檢查、系統監控與 Discord RPC
│   ├── pet_voice.py              # gTTS 語音合成與 miniaudio 音量播放
│   ├── punishment.py             # 黑化懲罰與系統視窗安全排除機制
│   ├── workers.py                # 背景執行緒 (Gemini AI、天氣 API)
│   └── styles.py                 # 統一管理 QSS 介面視覺樣式
│
├── assets/                       # 圖片資源
├── main.py                       # 專案啟動入口
├── .env                          # 環境變數設定檔
├── pet_save.json                 # 本機玩家存檔 (金幣/好感/飽食度/持股/道具)
├── .gitignore                    # Git 版本控制排除規則
└── README.md                     # 說明文件
```

---

## 🛠️ Environment Setup

### 系統與 Python 版本
- **OS**: Windows 10 / 11
- **Python**: 3.9+ (建議 3.12+)

### 安裝依賴套件
在終端機執行以下指令安裝所有必要套件：
```bash
pip install PyQt5 miniaudio google-genai pypresence gTTS python-dotenv psutil requests pywin32 yfinance
```

---

## 🔑 環境變數設定 (.env)

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

## 🚀 執行程式 (Run)

在專案目錄下執行：

```bash
python main.py
```

---