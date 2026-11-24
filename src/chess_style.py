from .styles import DIALOG_STYLE

CHESS_EXTRA_STYLE = """
QDialog {
    background-color: #1e2028;
    color: #f3f4f6;
}
QFrame#ChessTopCard {
    background-color: #2a2d3a;
    border: 1px solid #3c4154;
    border-radius: 12px;
}
QLabel#ChessStatusLabel {
    color: #f9fafb;
    font-size: 14px;
    font-weight: 600;
}
QComboBox#ChessSkillCombo {
    background-color: #353949;
    color: #f3f4f6;
    border: 1px solid #4b5168;
    border-radius: 8px;
    padding: 5px 10px;
    font-size: 13px;
}
QComboBox#ChessSkillCombo:hover {
    border-color: #8b9cf7;
}
QPushButton#ChessResetBtn {
    background-color: #4f6ef7;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 6px 14px;
    font-size: 13px;
    font-weight: 600;
}
QPushButton#ChessResetBtn:hover {
    background-color: #637ff9;
}
QPushButton#ChessResetBtn:pressed {
    background-color: #3c58d6;
}
QFrame#ChessBoardFrame {
    background-color: #252834;
    border: 2px solid #43485c;
    border-radius: 12px;
}
"""

CHESS_DIALOG_STYLE = DIALOG_STYLE + "\n" + CHESS_EXTRA_STYLE