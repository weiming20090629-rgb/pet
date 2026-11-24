import sys
from pathlib import Path
import chess
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPainter, QPixmap
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from .stockfish_engine import StockfishMoveWorker
from .styles import DIALOG_STYLE

PIECE_SYMBOLS = {
    "P": "♙", "N": "♘", "B": "♗", "R": "♖", "Q": "♕", "K": "♔",
    "p": "♟", "n": "♞", "b": "♝", "r": "♜", "q": "♛", "k": "♚",
}

PIECE_FILE_MAP = {
    "P": "wp.png",
    "N": "wn.png",
    "B": "wb.png",
    "R": "wr.png",
    "Q": "wq.png",
    "K": "wk.png",
    "p": "bp.png",
    "n": "bn.png",
    "b": "bb.png",
    "r": "br.png",
    "q": "bq.png",
    "k": "bk.png",
}


def get_chess_assets_dir() -> Path:
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    else:
        base = Path(__file__).resolve().parent.parent
    return base / "assets" / "chess"


class BoardCanvas(QWidget):
    """精準置中繪製棋盤、高亮格與棋子的 8x8 畫布"""

    def __init__(self, dialog, board_size: int = 440):
        super().__init__(dialog)
        self.dialog = dialog
        self.board_size = board_size
        self.sq_size = board_size // 8
        self.setFixedSize(board_size, board_size)

        self.board_pixmap = QPixmap()
        self.piece_pixmaps = {}
        self._load_assets()

    def _load_assets(self):
        assets_dir = get_chess_assets_dir()
        board_path = assets_dir / "board.png"
        if board_path.exists():
            pm = QPixmap(str(board_path))
            if not pm.isNull():
                self.board_pixmap = pm.scaled(
                    self.board_size,
                    self.board_size,
                    Qt.IgnoreAspectRatio,
                    Qt.SmoothTransformation,
                )

        for sym, fname in PIECE_FILE_MAP.items():
            img_path = assets_dir / fname
            if img_path.exists():
                pm = QPixmap(str(img_path))
                if not pm.isNull():
                    self.piece_pixmaps[sym] = pm

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        col = int(event.x() // self.sq_size)
        row = int(event.y() // self.sq_size)
        if 0 <= col < 8 and 0 <= row < 8:
            rank = 7 - row
            sq = chess.square(col, rank)
            self.dialog.on_square_clicked(sq)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        board = self.dialog.board
        selected = self.dialog.selected_square
        legal_targets = set()
        if selected is not None:
            for mv in board.legal_moves:
                if mv.from_square == selected:
                    legal_targets.add(mv.to_square)

        has_board_img = not self.board_pixmap.isNull()
        if has_board_img:
            painter.drawPixmap(0, 0, self.board_pixmap)

        piece_box_size = int(self.sq_size * 0.82)

        for row in range(8):
            for col in range(8):
                rank = 7 - row
                sq = chess.square(col, rank)
                x = col * self.sq_size
                y = row * self.sq_size
                is_light = (col + rank) % 2 == 1

                # 1. 底色 / 高亮遮罩
                if has_board_img:
                    if sq == selected:
                        painter.fillRect(x, y, self.sq_size, self.sq_size, QColor(246, 246, 105, 130))
                    elif sq in legal_targets:
                        painter.fillRect(x, y, self.sq_size, self.sq_size, QColor(186, 202, 68, 130))
                else:
                    if sq == selected:
                        bg = QColor("#f6f669")
                    elif sq in legal_targets:
                        bg = QColor("#baca44") if is_light else QColor("#9bb038")
                    else:
                        bg = QColor("#eeeed2") if is_light else QColor("#769656")
                    painter.fillRect(x, y, self.sq_size, self.sq_size, bg)

                # 2. 棋子精準置中繪製
                piece = board.piece_at(sq)
                if piece:
                    sym = piece.symbol()
                    pm = self.piece_pixmaps.get(sym)
                    if pm and not pm.isNull():
                        scaled_pm = pm.scaled(
                            piece_box_size,
                            piece_box_size,
                            Qt.KeepAspectRatio,
                            Qt.SmoothTransformation,
                        )
                        px = x + (self.sq_size - scaled_pm.width()) // 2
                        py = y + (self.sq_size - scaled_pm.height()) // 2
                        painter.drawPixmap(px, py, scaled_pm)
                    else:
                        painter.setPen(QColor("#111111"))
                        font = painter.font()
                        font.setPixelSize(int(self.sq_size * 0.6))
                        painter.setFont(font)
                        painter.drawText(x, y, self.sq_size, self.sq_size, Qt.AlignCenter, PIECE_SYMBOLS.get(sym, ""))

        painter.end()


class ChessGameDialog(QDialog):
    BOARD_SIZE = 440

    def __init__(self, pet, parent=None):
        super().__init__(parent or pet)
        self.pet = pet
        self.board = chess.Board()
        self.selected_square = None
        self.worker = None

        self.setWindowTitle("與桌寵下西洋棋 ♟️")
        self.setStyleSheet(DIALOG_STYLE)
        self.setFixedSize(self.BOARD_SIZE + 24, self.BOARD_SIZE + 80)

        layout = QVBoxLayout(self)

        # 頂部控制列：難度選擇 + 重新開局
        top_bar = QHBoxLayout()
        self.status_label = QLabel("輪到你走（白方）")
        self.skill_combo = QComboBox()
        self.skill_combo.addItem("入門 (Lv.1)", 1)
        self.skill_combo.addItem("普通 (Lv.5)", 5)
        self.skill_combo.addItem("進階 (Lv.10)", 10)
        self.skill_combo.addItem("大師 (Lv.18)", 18)
        self.skill_combo.setCurrentIndex(1)

        reset_btn = QPushButton("新局")
        reset_btn.clicked.connect(self.reset_game)

        top_bar.addWidget(self.status_label, 1)
        top_bar.addWidget(self.skill_combo)
        top_bar.addWidget(reset_btn)
        layout.addLayout(top_bar)

        self.board_canvas = BoardCanvas(self, board_size=self.BOARD_SIZE)
        layout.addWidget(self.board_canvas, alignment=Qt.AlignCenter)
        self.refresh_board()

    def _is_worker_running(self) -> bool:
        if self.worker is None:
            return False
        try:
            return self.worker.isRunning()
        except RuntimeError:
            self.worker = None
            return False

    def reset_game(self):
        if self._is_worker_running():
            return
        self.board.reset()
        self.selected_square = None
        self.status_label.setText("輪到你走（白方）")
        self.refresh_board()

    def refresh_board(self):
        self.board_canvas.update()

    def on_square_clicked(self, sq: int):
        if self.board.is_game_over() or self.board.turn != chess.WHITE:
            return
        if self._is_worker_running():
            return

        if self.selected_square is None:
            piece = self.board.piece_at(sq)
            if piece and piece.color == chess.WHITE:
                self.selected_square = sq
                self.refresh_board()
            return

        if sq == self.selected_square:
            self.selected_square = None
            self.refresh_board()
            return

        move = chess.Move(self.selected_square, sq)
        promo_move = chess.Move(self.selected_square, sq, promotion=chess.QUEEN)
        chosen_move = promo_move if promo_move in self.board.legal_moves else move

        if chosen_move in self.board.legal_moves:
            self.board.push(chosen_move)
            self.selected_square = None
            self.refresh_board()
            if not self._check_game_over():
                self._trigger_pet_turn()
        else:
            piece = self.board.piece_at(sq)
            self.selected_square = sq if (piece and piece.color == chess.WHITE) else None
            self.refresh_board()

    def _trigger_pet_turn(self):
        skill = self.skill_combo.currentData()
        self.status_label.setText("桌寵思考中... ♟️")
        self.pet.show_speech_bubble("讓我想想這步怎麼應對... ♟️")

        worker = StockfishMoveWorker(
            fen=self.board.fen(), skill_level=skill, think_time=0.4, parent=self
        )
        self.worker = worker

        def _on_finished():
            if self.worker is worker:
                self.worker = None
            worker.deleteLater()

        worker.move_ready.connect(self._on_pet_move)
        worker.error_occurred.connect(self._on_engine_error)
        worker.finished.connect(_on_finished)
        worker.start()

    def _on_pet_move(self, move_uci: str, eval_text: str):
        if move_uci:
            mv = chess.Move.from_uci(move_uci)
            if mv in self.board.legal_moves:
                self.board.push(mv)
        self.refresh_board()
        if not self._check_game_over():
            hint = f"（{eval_text}）" if eval_text else ""
            self.status_label.setText(f"輪到你走 {hint}")
            self.pet.show_speech_bubble(f"我走 {move_uci}！輪到你囉～")

    def _on_engine_error(self, err_msg: str):
        self.status_label.setText("引擎發生錯誤")
        self.pet.show_speech_bubble(err_msg)

    def _check_game_over(self) -> bool:
        if not self.board.is_game_over():
            return False
        outcome = self.board.outcome()
        if outcome is None or outcome.winner is None:
            text = "和局！這盤棋勢均力敵呢 🤝"
        elif outcome.winner == chess.WHITE:
            text = "你贏了！太強了吧 🎉"
            self.pet.favorability = min(getattr(self.pet, "favorability", 0) + 5, 100)
            self.pet.save_data()
        else:
            text = "我贏啦！再來挑戰一局嗎？😎"
        self.status_label.setText(text)
        self.pet.show_speech_bubble(text)
        return True