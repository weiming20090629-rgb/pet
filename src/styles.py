# ==========================================
# 桌面寵物專案 - 介面樣式定義檔 (QSS)
# ==========================================

# 右鍵選單 (QMenu) 的外觀樣式 - 簡約白底風格
CONTEXT_MENU_STYLE = """
    QMenu {
        background-color: #ffffff;
        color: #333333;
        border: 1px solid #dcdcdc;
        border-radius: 8px;
        padding: 5px;
        background-clip: padding;
    }
    
    QMenu::item {
        padding: 8px 25px;
        border-radius: 4px;
        margin: 2px 0px;
        background: transparent;
    }
    
    QMenu::item:selected {
        background-color: #4a90e2;
        color: #ffffff;
    }
    
    QMenu::separator {
        height: 1px;
        background: #e0e0e0;
        margin: 4px 8px;
    }
"""

# 語音氣泡對話框 (Speech Bubble) 的外觀樣式 - 簡約白底風格
SPEECH_BUBBLE_STYLE = """
    background-color: rgba(255, 255, 255, 235); /* 半透明純白背景 */
    color: #2c3e50;                              /* 深色文字，清晰易讀 */
    border: 2px solid #4a90e2;                   /* 藍色邊框凸顯氣泡感 */
    border-radius: 10px;                         /* 圓角 */
    padding: 8px 14px;                           /* 內距 */
    font-size: 13px;
    font-weight: bold;
"""