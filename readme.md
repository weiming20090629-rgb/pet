# 🐾 Desktop Pet - Quick Setup

極簡專案環境設定指南。

---

## 🛠️ 1. 環境需求與套件安裝 (Environment Setup)

### 系統與 Python 版本
- **OS**: Windows 10 / 11
- **Python**: 3.12+

### 安裝依賴套件
在終端機執行以下指令安裝所有必要套件：

```bash
pip install PyQt5 google-genai pypresence gTTS "playsound<1.3.0" python-dotenv
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

---

## 🚀 3. 執行程式 (Run)

```bash
python pet.py
```