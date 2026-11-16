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

VOLUME_SLIDER_STYLE = """
    QSlider::groove:horizontal {
        height: 5px;
        background: #e0e0e0;
        border-radius: 2px;
    }
    QSlider::sub-page:horizontal {
        background: #4a90e2;
        border-radius: 2px;
    }
    QSlider::handle:horizontal {
        background: #ffffff;
        border: 1px solid #4a90e2;
        width: 12px;
        height: 12px;
        margin: -4px 0;
        border-radius: 6px;
    }
"""

DIALOG_STYLE = """
    QDialog, QMessageBox, QInputDialog {
        background-color: #ffffff;
        color: #2c3e50;
        font-size: 13px;
    }
    QLabel {
        color: #2c3e50;
        font-size: 13px;
    }
    QLineEdit, QSpinBox {
        background-color: #f8fafc;
        color: #2c3e50;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        padding: 6px 10px;
        min-height: 22px;
    }
    QLineEdit:focus, QSpinBox:focus {
        border: 1px solid #4a90e2;
        background-color: #ffffff;
    }
    QComboBox {
        background-color: #f8fafc;
        color: #2c3e50;
        border: 1.5px solid #4a90e2;
        border-radius: 6px;
        padding: 6px 12px;
        min-height: 24px;
        min-width: 280px;
    }
    QComboBox:focus, QComboBox:on {
        border: 1.5px solid #4a90e2;
        background-color: #ffffff;
    }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 26px;
        border: none;
        background-color: transparent;
    }
    QComboBox QAbstractItemView {
        background-color: #ffffff;
        color: #2c3e50;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 6px;
        min-width: 280px;
        selection-background-color: #4a90e2;
        selection-color: #ffffff;
        outline: none;
    }
    QComboBox QAbstractItemView::item {
        padding: 8px 14px;
        margin: 2px 0px;
        min-height: 26px;
        border-radius: 4px;
    }
    QComboBox QAbstractItemView::item:hover {
        background-color: #e8f1fc;
        color: #1e3a5f;
    }
    QComboBox QAbstractItemView::item:selected {
        background-color: #4a90e2;
        color: #ffffff;
    }
    QPushButton {
        background-color: #4a90e2;
        color: #ffffff;
        border: none;
        border-radius: 6px;
        padding: 6px 16px;
        font-weight: bold;
        min-width: 64px;
    }
    QPushButton:hover {
        background-color: #357abd;
    }
    QPushButton:pressed {
        background-color: #2b639b;
    }
"""