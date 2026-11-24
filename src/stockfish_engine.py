import os
import sys
from pathlib import Path
import chess
import chess.engine
from PyQt5.QtCore import QThread, pyqtSignal


def get_stockfish_path() -> Path:
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    else:
        base = Path(__file__).resolve().parent.parent
    return base / "assets" / "engine" / "stockfish.exe"


class StockfishMoveWorker(QThread):
    move_ready = pyqtSignal(str, str)  # (best_move_uci, eval_summary)
    error_occurred = pyqtSignal(str)

    def __init__(self, fen: str, skill_level: int = 5, think_time: float = 0.4, parent=None):
        super().__init__(parent)
        self.fen = fen
        self.skill_level = max(0, min(20, int(skill_level)))
        self.think_time = think_time

    def run(self):
        engine_path = get_stockfish_path()
        if not engine_path.exists():
            self.error_occurred.emit(f"找不到 Stockfish 引擎：{engine_path}")
            return

        creationflags = getattr(subprocess := __import__("subprocess"), "CREATE_NO_WINDOW", 0x08000000) if os.name == "nt" else 0

        engine = None
        try:
            engine = chess.engine.SimpleEngine.popen_uci(
                str(engine_path),
                creationflags=creationflags,
            )
            engine.configure({"Skill Level": self.skill_level})
            board = chess.Board(self.fen)
            info = engine.analyse(board, chess.engine.Limit(time=self.think_time))
            result = engine.play(board, chess.engine.Limit(time=self.think_time))

            best_move = result.move.uci() if result.move else ""
            score = info.get("score")
            eval_text = ""
            if score is not None:
                pov_score = score.pov(board.turn)
                if pov_score.is_mate():
                    mate_in = pov_score.mate()
                    eval_text = f"將殺倒數 {mate_in} 步"
                else:
                    cp = pov_score.score()
                    if cp is not None:
                        eval_text = f"局勢評分 {cp / 100:+.2f}"

            self.move_ready.emit(best_move, eval_text)
        except Exception as exc:
            self.error_occurred.emit(f"引擎運算失敗：{exc}")
        finally:
            if engine is not None:
                try:
                    engine.quit()
                except Exception:
                    pass