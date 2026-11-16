import time
from datetime import datetime
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QRectF, QPointF
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QPainterPath
from PyQt5.QtWidgets import (
    QDialog,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
import yfinance as yf
from .styles import DIALOG_STYLE

COIN_RATE = 10.0  # 1 單位股價折合 10 桌寵金幣


class CandlestickWidget(QWidget):
    """進階 K 線圖元件：紅漲綠跌 + 5MA/20MA + 成交量 + 成本線 + 滑鼠十字線明細"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.candles = []
        self.symbol = ""
        self.timeframe_label = "日K"
        self.avg_cost = None
        self.hover_idx = -1
        self.hover_pos = None

        self.setMinimumHeight(270)
        self.setMouseTracking(True)

    def set_data(self, symbol: str, candles: list, timeframe_label: str = "日K", avg_cost=None):
        self.symbol = symbol
        self.candles = candles
        self.timeframe_label = timeframe_label
        self.avg_cost = avg_cost
        self.hover_idx = -1
        self.update()

    def set_avg_cost(self, avg_cost):
        self.avg_cost = avg_cost
        self.update()

    def mouseMoveEvent(self, event):
        if not self.candles:
            return
        self.hover_pos = event.pos()
        left_pad = 12
        right_pad = 64
        plot_w = self.width() - left_pad - right_pad
        if plot_w <= 0:
            return

        rel_x = event.x() - left_pad
        if 0 <= rel_x <= plot_w:
            step = plot_w / len(self.candles)
            idx = int(rel_x // step)
            idx = max(0, min(idx, len(self.candles) - 1))
            self.hover_idx = idx
        else:
            self.hover_idx = -1
        self.update()

    def leaveEvent(self, event):
        self.hover_idx = -1
        self.hover_pos = None
        self.update()

    def _calc_ma(self, closes: list, period: int) -> list:
        ma = []
        for i in range(len(closes)):
            if i + 1 < period:
                ma.append(None)
            else:
                ma.append(sum(closes[i - period + 1 : i + 1]) / period)
        return ma

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        painter.fillRect(rect, QColor("#181e29"))
        painter.setPen(QPen(QColor("#334155"), 1))
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 8, 8)

        if not self.candles:
            painter.setPen(QColor("#94a3b8"))
            painter.setFont(QFont("Microsoft JhengHei", 10))
            painter.drawText(rect, Qt.AlignCenter, "輸入代號或點擊上方自選股，即可載入 K 線與技術指標")
            return

        left_pad = 12
        right_pad = 64
        top_pad = 28
        bottom_pad = 22
        gap_between = 8

        total_w = rect.width() - left_pad - right_pad
        total_h = rect.height() - top_pad - bottom_pad
        if total_w <= 10 or total_h <= 20:
            return

        # 上方 76% 畫 K 線與均線，下方 24% 畫成交量
        price_h = (total_h - gap_between) * 0.76
        vol_top = top_pad + price_h + gap_between
        vol_h = (total_h - gap_between) * 0.24

        highs = [c["high"] for c in self.candles]
        lows = [c["low"] for c in self.candles]
        closes = [c["close"] for c in self.candles]
        vols = [c.get("volume", 0) for c in self.candles]

        ma5 = self._calc_ma(closes, 5)
        ma20 = self._calc_ma(closes, 20)

        all_prices = highs + lows
        if self.avg_cost and self.avg_cost > 0:
            all_prices.append(self.avg_cost)

        max_p = max(all_prices)
        min_p = min(all_prices)
        if max_p == min_p:
            max_p += 1.0
            min_p -= 1.0
        span = max_p - min_p
        max_vol = max(vols) if vols and max(vols) > 0 else 1.0

        def price_to_y(price: float) -> float:
            return top_pad + (max_p - price) / span * price_h

        # 標題與均線圖例
        painter.setFont(QFont("Microsoft JhengHei", 9, QFont.Bold))
        painter.setPen(QColor("#f1f5f9"))
        painter.drawText(left_pad, 4, 210, 20, Qt.AlignLeft | Qt.AlignVCenter, f"{self.symbol} [{self.timeframe_label}]")

        painter.setFont(QFont("Consolas", 8))
        painter.setPen(QColor("#facc15"))
        painter.drawText(left_pad + 150, 4, 60, 20, Qt.AlignLeft | Qt.AlignVCenter, "— 5MA")
        painter.setPen(QColor("#c084fc"))
        painter.drawText(left_pad + 205, 4, 65, 20, Qt.AlignLeft | Qt.AlignVCenter, "— 20MA")
        if self.avg_cost and self.avg_cost > 0:
            painter.setPen(QColor("#38bdf8"))
            painter.drawText(left_pad + 268, 4, 110, 20, Qt.AlignLeft | Qt.AlignVCenter, f"--- 成本 {self.avg_cost:.2f}")

        # 價格水平網格與右側刻度
        for ratio in (0.0, 0.5, 1.0):
            y = top_pad + ratio * price_h
            p_val = max_p - ratio * span
            painter.setPen(QPen(QColor("#263042"), 1, Qt.DashLine))
            painter.drawLine(int(left_pad), int(y), int(left_pad + total_w), int(y))

            painter.setPen(QColor("#94a3b8"))
            painter.drawText(
                int(left_pad + total_w + 5), int(y - 8), right_pad - 6, 16,
                Qt.AlignLeft | Qt.AlignVCenter, f"{p_val:.2f}"
            )

        # 成交量區分隔線與標籤
        painter.setPen(QPen(QColor("#2d3748"), 1))
        painter.drawLine(int(left_pad), int(vol_top - 3), int(left_pad + total_w), int(vol_top - 3))
        painter.setPen(QColor("#64748b"))
        painter.drawText(int(left_pad + total_w + 5), int(vol_top), right_pad - 6, 16, Qt.AlignLeft, "VOL")

        n = len(self.candles)
        step = total_w / max(n, 1)
        body_w = max(2.5, min(step * 0.65, 13.0))

        up_color = QColor("#ef4444")    # 紅漲
        down_color = QColor("#22c55e")  # 綠跌

        # 畫 K 棒與成交量柱
        for i, c in enumerate(self.candles):
            cx = left_pad + (i + 0.5) * step
            y_open = price_to_y(c["open"])
            y_close = price_to_y(c["close"])
            y_high = price_to_y(c["high"])
            y_low = price_to_y(c["low"])

            color = up_color if c["close"] >= c["open"] else down_color
            painter.setPen(QPen(color, 1.2))
            painter.setBrush(color)

            # 影線與實體
            painter.drawLine(int(cx), int(y_high), int(cx), int(y_low))
            top_y = min(y_open, y_close)
            body_h = max(abs(y_close - y_open), 1.5)
            painter.drawRect(QRectF(cx - body_w / 2, top_y, body_w, body_h))

            # 成交量柱
            v = c.get("volume", 0)
            if v > 0:
                vh = (v / max_vol) * vol_h
                painter.drawRect(QRectF(cx - body_w / 2, vol_top + vol_h - vh, body_w, vh))

        # 畫 5MA / 20MA 折線
        def draw_ma_line(ma_vals, hex_color):
            path = QPainterPath()
            started = False
            for i, val in enumerate(ma_vals):
                if val is None:
                    continue
                cx = left_pad + (i + 0.5) * step
                cy = price_to_y(val)
                if not started:
                    path.moveTo(cx, cy)
                    started = True
                else:
                    path.lineTo(cx, cy)
            if started:
                painter.setPen(QPen(QColor(hex_color), 1.4))
                painter.setBrush(Qt.NoBrush)
                painter.drawPath(path)

        draw_ma_line(ma5, "#facc15")
        draw_ma_line(ma20, "#c084fc")

        # 持股平均成本線
        if self.avg_cost and min_p <= self.avg_cost <= max_p:
            cost_y = price_to_y(self.avg_cost)
            painter.setPen(QPen(QColor("#38bdf8"), 1.3, Qt.DashLine))
            painter.drawLine(int(left_pad), int(cost_y), int(left_pad + total_w), int(cost_y))

        # 底部起訖日期
        painter.setPen(QColor("#94a3b8"))
        painter.setFont(QFont("Consolas", 8))
        painter.drawText(left_pad, rect.height() - bottom_pad + 3, 120, 18, Qt.AlignLeft, self.candles[0]["date"])
        painter.drawText(
            int(left_pad + total_w - 120), rect.height() - bottom_pad + 3, 120, 18,
            Qt.AlignRight, self.candles[-1]["date"]
        )

        # 滑鼠懸停十字準星與明細框
        if 0 <= self.hover_idx < n:
            c = self.candles[self.hover_idx]
            cx = left_pad + (self.hover_idx + 0.5) * step
            cy = price_to_y(c["close"])

            painter.setPen(QPen(QColor("#cbd5e1"), 1, Qt.DotLine))
            painter.drawLine(int(cx), int(top_pad), int(cx), int(vol_top + vol_h))
            painter.drawLine(int(left_pad), int(cy), int(left_pad + total_w), int(cy))

            prev_close = self.candles[self.hover_idx - 1]["close"] if self.hover_idx > 0 else c["open"]
            chg_pct = ((c["close"] - prev_close) / prev_close * 100) if prev_close else 0.0
            sign = "+" if chg_pct >= 0 else ""
            vol_k = c.get("volume", 0) / 1000.0

            info_text = (
                f"{c['date']}  開:{c['open']:.2f}  高:{c['high']:.2f}  "
                f"低:{c['low']:.2f}  收:{c['close']:.2f} ({sign}{chg_pct:.2f}%)  量:{vol_k:.0f}K"
            )
            box_rect = QRectF(left_pad + 4, top_pad + 4, total_w - 8, 22)
            painter.fillRect(box_rect, QColor(15, 23, 42, 220))
            painter.setPen(QPen(QColor("#475569"), 1))
            painter.drawRect(box_rect)
            painter.setPen(QColor("#f8fafc"))
            painter.setFont(QFont("Microsoft JhengHei", 8))
            painter.drawText(box_rect.adjusted(6, 0, -6, 0), Qt.AlignVCenter | Qt.AlignLeft, info_text)


def normalize_ticker(raw: str) -> str:
    s = raw.strip().upper()
    if s.isdigit() and 4 <= len(s) <= 6:
        return f"{s}.TW"
    return s


class StockPriceWorker(QThread):
    """背景抓真實股價與歷史 K 線資料"""

    price_loaded = pyqtSignal(str, float, list, str, str)  # symbol, price, candles, tf_label, err

    TIMEFRAME_MAP = {
        "1d": ("3mo", "1d", 40, "日K"),
        "1wk": ("1y", "1wk", 40, "週K"),
        "5m": ("5d", "5m", 48, "5分K"),
    }

    def __init__(self, symbol: str, interval_key: str = "1d"):
        super().__init__()
        self.symbol = normalize_ticker(symbol)
        self.interval_key = interval_key

    def run(self):
        period, interval, limit, tf_label = self.TIMEFRAME_MAP.get(
            self.interval_key, ("3mo", "1d", 40, "日K")
        )
        try:
            ticker = yf.Ticker(self.symbol)
            hist = ticker.history(period=period, interval=interval)

            candles = []
            if not hist.empty:
                hist = hist.dropna(subset=["Open", "High", "Low", "Close"]).tail(limit)
                date_fmt = "%m/%d %H:%M" if interval == "5m" else "%m/%d"
                for idx, row in hist.iterrows():
                    candles.append({
                        "date": idx.strftime(date_fmt),
                        "open": float(row["Open"]),
                        "high": float(row["High"]),
                        "low": float(row["Low"]),
                        "close": float(row["Close"]),
                        "volume": float(row.get("Volume", 0) or 0),
                    })

            price = None
            fast_info = getattr(ticker, "fast_info", None)
            if fast_info:
                price = fast_info.get("lastPrice") or fast_info.get("regularMarketPrice")

            if price is None and candles:
                price = candles[-1]["close"]

            if price is None or float(price) <= 0:
                self.price_loaded.emit(self.symbol, 0.0, [], tf_label, f"找不到「{self.symbol}」的有效報價")
                return

            self.price_loaded.emit(self.symbol, float(price), candles, tf_label, "")
        except Exception as e:
            self.price_loaded.emit(self.symbol, 0.0, [], tf_label, f"查詢失敗：{e}")


class PortfolioRefreshWorker(QThread):
    """背景一次更新所有持股的最新市價"""

    all_loaded = pyqtSignal(dict)  # {symbol: latest_price}

    def __init__(self, symbols: list):
        super().__init__()
        self.symbols = list(symbols)

    def run(self):
        prices = {}
        for sym in self.symbols:
            try:
                ticker = yf.Ticker(sym)
                p = None
                fast_info = getattr(ticker, "fast_info", None)
                if fast_info:
                    p = fast_info.get("lastPrice") or fast_info.get("regularMarketPrice")
                if p is None:
                    hist = ticker.history(period="5d")
                    if not hist.empty:
                        p = float(hist["Close"].dropna().iloc[-1])
                if p and float(p) > 0:
                    prices[sym] = float(p)
            except Exception:
                pass
        self.all_loaded.emit(prices)


class StockDialog(QDialog):
    """進階股票交易室：K線技術圖 + 自選股 + 比例下單 + 投資組合總覽與歷史紀錄"""

    def __init__(self, pet):
        super().__init__(pet)
        self.pet = pet
        self.current_symbol = ""
        self.current_price = 0.0
        self.current_interval = "1d"
        self.latest_prices = {}  # 快取各檔最新市價
        self.worker = None
        self.refresh_worker = None

        if not hasattr(self.pet, "portfolio") or not isinstance(self.pet.portfolio, dict):
            self.pet.portfolio = {}
        if not hasattr(self.pet, "trade_history") or not isinstance(self.pet, list):
            self.pet.trade_history = []
        if not hasattr(self.pet, "watchlist") or not isinstance(self.pet, list):
            self.pet.watchlist = ["2330", "0050", "NVDA", "AAPL"]

        self.setWindowTitle("📈 桌寵專業股票交易室")
        self.setMinimumWidth(620)
        self.setStyleSheet(DIALOG_STYLE)
        self._init_ui()
        self._refresh_portfolio_view()
        self._refresh_history_view()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # 頂部錢包資訊
        self.wallet_label = QLabel()
        layout.addWidget(self.wallet_label)

        # 自選股快捷列
        self.watchlist_layout = QHBoxLayout()
        self.watchlist_layout.setSpacing(6)
        layout.addLayout(self.watchlist_layout)
        self._rebuild_watchlist_bar()

        # 查價與週期切換列
        search_row = QHBoxLayout()
        self.symbol_input = QLineEdit()
        self.symbol_input.setPlaceholderText("輸入代號，如 AAPL、NVDA、2330 或 2330.TW")
        self.symbol_input.returnPressed.connect(self.lookup_price)

        self.search_btn = QPushButton("查價")
        self.search_btn.clicked.connect(self.lookup_price)

        self.add_watch_btn = QPushButton("⭐ 收藏")
        self.add_watch_btn.clicked.connect(self.toggle_watchlist)

        search_row.addWidget(self.symbol_input)
        search_row.addWidget(self.search_btn)
        search_row.addWidget(self.add_watch_btn)
        layout.addLayout(search_row)

        # 報價 + K線週期切換按鈕
        quote_row = QHBoxLayout()
        self.quote_label = QLabel("目前報價：尚未查詢")
        quote_row.addWidget(self.quote_label, stretch=1)

        self.tf_buttons = {}
        for key, label in (("1d", "日K"), ("1wk", "週K"), ("5m", "5分K")):
            btn = QPushButton(label)
            btn.setFixedWidth(54)
            btn.clicked.connect(lambda checked, k=key: self.switch_timeframe(k))
            quote_row.addWidget(btn)
            self.tf_buttons[key] = btn
        self._update_tf_button_styles()
        layout.addLayout(quote_row)

        # K 線圖區
        self.kline_widget = CandlestickWidget(self)
        layout.addWidget(self.kline_widget)

        # 快捷比例下單列
        quick_row = QHBoxLayout()
        quick_row.addWidget(QLabel("快捷下單："))
        for label, ratio in (("買 25%", 0.25), ("買 50%", 0.50), ("All In", 1.0)):
            b = QPushButton(label)
            b.clicked.connect(lambda checked, r=ratio: self.set_buy_ratio(r))
            quick_row.addWidget(b)

        sell_all_btn = QPushButton("全賣出清")
        sell_all_btn.clicked.connect(self.set_sell_all)
        quick_row.addWidget(sell_all_btn)
        layout.addLayout(quick_row)

        # 交易執行列
        trade_row = QHBoxLayout()
        self.shares_spin = QDoubleSpinBox()
        self.shares_spin.setRange(0.01, 100000.0)
        self.shares_spin.setDecimals(2)
        self.shares_spin.setSingleStep(1.0)
        self.shares_spin.setValue(1.0)
        self.shares_spin.valueChanged.connect(self._update_est_cost_label)

        self.est_cost_label = QLabel("預估金額：0 金幣")

        self.buy_btn = QPushButton("買入")
        self.buy_btn.setEnabled(False)
        self.buy_btn.clicked.connect(self.buy_stock)

        self.sell_btn = QPushButton("賣出")
        self.sell_btn.setEnabled(False)
        self.sell_btn.clicked.connect(self.sell_stock)

        trade_row.addWidget(QLabel("股數："))
        trade_row.addWidget(self.shares_spin)
        trade_row.addWidget(self.est_cost_label, stretch=1)
        trade_row.addWidget(self.buy_btn)
        trade_row.addWidget(self.sell_btn)
        layout.addLayout(trade_row)

        # 下方分頁：持股損益 / 交易紀錄
        self.tabs = QTabWidget()

        # 分頁 1：持股與損益
        pos_tab = QWidget()
        pos_layout = QVBoxLayout(pos_tab)
        pos_layout.setContentsMargins(4, 6, 4, 4)
        self.portfolio_box = QTextEdit()
        self.portfolio_box.setReadOnly(True)
        self.portfolio_box.setMinimumHeight(115)
        pos_layout.addWidget(self.portfolio_box)

        self.refresh_all_btn = QPushButton("🔄 刷新全部持股最新市價")
        self.refresh_all_btn.clicked.connect(self.refresh_all_positions)
        pos_layout.addWidget(self.refresh_all_btn)
        self.tabs.addTab(pos_tab, "📊 持股與損益")

        # 分頁 2：歷史成交紀錄
        hist_tab = QWidget()
        hist_layout = QVBoxLayout(hist_tab)
        hist_layout.setContentsMargins(4, 6, 4, 4)
        self.history_box = QTextEdit()
        self.history_box.setReadOnly(True)
        self.history_box.setMinimumHeight(115)
        hist_layout.addWidget(self.history_box)
        self.tabs.addTab(hist_tab, "📜 交易紀錄")

        layout.addWidget(self.tabs)

    def _rebuild_watchlist_bar(self):
        while self.watchlist_layout.count():
            item = self.watchlist_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.watchlist_layout.addWidget(QLabel("自選股："))
        for sym in self.pet.watchlist:
            btn = QPushButton(sym)
            btn.setStyleSheet("padding: 3px 10px; font-size: 12px;")
            btn.clicked.connect(lambda checked, s=sym: self.quick_lookup(s))
            self.watchlist_layout.addWidget(btn)
        self.watchlist_layout.addStretch()

    def toggle_watchlist(self):
        raw = self.symbol_input.text().strip().upper() or self.current_symbol
        if not raw:
            self._show_tip("提示", "請先輸入股票代號。")
            return
        display_sym = raw.replace(".TW", "") if raw.endswith(".TW") and raw[:-3].isdigit() else raw
        if display_sym in self.pet.watchlist:
            self.pet.watchlist.remove(display_sym)
            self._show_tip("自選股", f"已將 {display_sym} 從自選股移除。")
        else:
            if len(self.pet.watchlist) >= 7:
                self.pet.watchlist.pop(0)
            self.pet.watchlist.append(display_sym)
            self._show_tip("自選股", f"已將 {display_sym} 加入自選股！")
        self.pet.save_data()
        self._rebuild_watchlist_bar()

    def quick_lookup(self, sym: str):
        self.symbol_input.setText(sym)
        self.lookup_price()

    def _update_tf_button_styles(self):
        for k, btn in self.tf_buttons.items():
            if k == self.current_interval:
                btn.setStyleSheet("background-color: #1d4ed8; color: white; font-weight: bold;")
            else:
                btn.setStyleSheet("background-color: #94a3b8; color: white;")

    def switch_timeframe(self, interval_key: str):
        self.current_interval = interval_key
        self._update_tf_button_styles()
        if self.symbol_input.text().strip() or self.current_symbol:
            self.lookup_price()

    def _update_est_cost_label(self):
        if self.current_price > 0:
            coins = int(round(self.shares_spin.value() * self.current_price * COIN_RATE))
            self.est_cost_label.setText(f"預估金額：{coins} 金幣")
        else:
            self.est_cost_label.setText("預估金額：0 金幣")

    def set_buy_ratio(self, ratio: float):
        if self.current_price <= 0:
            self._show_tip("提示", "請先查價取得最新股價。")
            return
        cost_per_share = self.current_price * COIN_RATE
        if cost_per_share <= 0:
            return
        max_shares = (self.pet.coins * ratio) / cost_per_share
        shares = round(max(max_shares - 0.01, 0.01), 2) if ratio == 1.0 else round(max_shares, 2)
        self.shares_spin.setValue(max(0.01, shares))

    def set_sell_all(self):
        if not self.current_symbol:
            self._show_tip("提示", "請先查詢要賣出的股票。")
            return
        pos = self.pet.portfolio.get(self.current_symbol)
        if not pos or float(pos.get("shares", 0)) <= 0:
            self._show_tip("提示", f"目前沒有持有 {self.current_symbol}。")
            return
        self.shares_spin.setValue(float(pos["shares"]))

    def _show_tip(self, title: str, text: str):
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setText(text)
        box.setStyleSheet(DIALOG_STYLE)
        box.exec_()

    def lookup_price(self):
        raw = self.symbol_input.text().strip()
        if not raw and self.current_symbol:
            raw = self.current_symbol
        if not raw:
            self._show_tip("提示", "請先輸入股票代號（例如 AAPL 或 2330）。")
            return

        # 若前一次查價執行緒還在跑，先斷開舊信號避免畫面錯亂
        if self.worker is not None and self.worker.isRunning():
            try:
                self.worker.price_loaded.disconnect()
            except Exception:
                pass

        # 查詢期間鎖定查價與交易按鈕，並重置當前報價狀態，防止用舊價格誤下單
        self.current_price = 0.0
        self.search_btn.setEnabled(False)
        self.buy_btn.setEnabled(False)
        self.sell_btn.setEnabled(False)
        self._update_est_cost_label()
        self.quote_label.setText("查詢真實股價與技術圖表中...")

        self.worker = StockPriceWorker(raw, self.current_interval)
        self.worker.price_loaded.connect(self._on_price_loaded)
        self.worker.start()

    def _on_price_loaded(self, symbol: str, price: float, candles: list, tf_label: str, err: str):
        self.search_btn.setEnabled(True)
        if err:
            self.current_symbol = ""
            self.current_price = 0.0
            self.buy_btn.setEnabled(False)
            self.sell_btn.setEnabled(False)
            self.quote_label.setText(err)
            return

        self.current_symbol = symbol
        self.current_price = price
        self.latest_prices[symbol] = price

        # 確認拿到有效新報價後，才解鎖買入與賣出按鈕
        self.buy_btn.setEnabled(True)
        self.sell_btn.setEnabled(True)

        coin_cost_per_share = price * COIN_RATE
        self.quote_label.setText(
            f"📌 {symbol} 最新報價：{price:.2f}（1 股 = {coin_cost_per_share:.1f} 金幣）"
        )

        pos = self.pet.portfolio.get(symbol)
        avg_cost = float(pos["avg_cost"]) if pos else None
        self.kline_widget.set_data(symbol, candles, tf_label, avg_cost)
        self._update_est_cost_label()
        self._refresh_portfolio_view()

    def closeEvent(self, event):
        """關閉視窗時安全斷開並等待背景抓價執行緒，防止視窗銷毀後更新 UI 導致閃退"""
        for w, sig in (
            (self.worker, "price_loaded"),
            (self.refresh_worker, "all_loaded"),
        ):
            if w is not None and w.isRunning():
                try:
                    getattr(w, sig).disconnect()
                except Exception:
                    pass
                w.quit()
                w.wait(1500)
        event.accept()

    def refresh_all_positions(self):
        if not self.pet.portfolio:
            self._show_tip("提示", "目前沒有任何持股需要更新。")
            return
        self.refresh_all_btn.setEnabled(False)
        self.refresh_all_btn.setText("🔄 正在同步全部持股報價...")
        self.refresh_worker = PortfolioRefreshWorker(list(self.pet.portfolio.keys()))
        self.refresh_worker.all_loaded.connect(self._on_all_positions_refreshed)
        self.refresh_worker.start()

    def _on_all_positions_refreshed(self, prices: dict):
        self.refresh_all_btn.setEnabled(True)
        self.refresh_all_btn.setText("🔄 刷新全部持股最新市價")
        self.latest_prices.update(prices)
        if self.current_symbol in prices:
            self.current_price = prices[self.current_symbol]
        self._refresh_portfolio_view()

    def buy_stock(self):
        if not self.current_symbol or self.current_price <= 0:
            self._show_tip("提示", "請先按「查價」取得最新股價再買入。")
            return

        shares = float(self.shares_spin.value())
        total_coins_needed = max(1, int(round(shares * self.current_price * COIN_RATE)))

        if self.pet.coins < total_coins_needed:
            self._show_tip(
                "金幣不足",
                f"買入 {shares:.2f} 股 {self.current_symbol} 需要 {total_coins_needed} 金幣，"
                f"目前只有 {self.pet.coins} 金幣。",
            )
            return

        self.pet.coins -= total_coins_needed
        pos = self.pet.portfolio.get(self.current_symbol, {"shares": 0.0, "avg_cost": 0.0})
        old_shares = float(pos["shares"])
        old_avg = float(pos["avg_cost"])
        new_shares = round(old_shares + shares, 4)
        new_avg = ((old_shares * old_avg) + (shares * self.current_price)) / new_shares

        self.pet.portfolio[self.current_symbol] = {
            "shares": new_shares,
            "avg_cost": round(new_avg, 4),
        }
        self.kline_widget.set_avg_cost(round(new_avg, 4))

        now_str = datetime.now().strftime("%m/%d %H:%M")
        self.pet.trade_history.insert(
            0, f"[{now_str}] 買入 {self.current_symbol} {shares:.2f}股 @ {self.current_price:.2f} (-{total_coins_needed}金幣)"
        )
        self.pet.trade_history = self.pet.trade_history[:50]

        self.pet.last_interaction_time = time.time()
        self.pet.save_data()
        self._refresh_portfolio_view()
        self._refresh_history_view()
        self._show_tip(
            "買入成功",
            f"已買入 {shares:.2f} 股 {self.current_symbol}，花費 {total_coins_needed} 金幣！",
        )

    def sell_stock(self):
        if not self.current_symbol or self.current_price <= 0:
            self._show_tip("提示", "請先按「查價」取得最新股價再賣出。")
            return

        pos = self.pet.portfolio.get(self.current_symbol)
        owned = float(pos["shares"]) if pos else 0.0
        avg_cost = float(pos["avg_cost"]) if pos else 0.0
        shares = float(self.shares_spin.value())

        if owned < shares - 1e-6:
            self._show_tip(
                "持股不足",
                f"你目前只持有 {owned:.2f} 股 {self.current_symbol}，無法賣出 {shares:.2f} 股。",
            )
            return

        earned_coins = int(round(shares * self.current_price * COIN_RATE))
        realized_pnl = int(round((self.current_price - avg_cost) * shares * COIN_RATE))
        bonus_coins = 0
        bonus_note = ""
        inv = getattr(self.pet, "inventory", {})
        if realized_pnl > 0 and inv.get("charm", 0) > 0:
            inv["charm"] -= 1
            bonus_coins = int(round(realized_pnl * 0.5))
            realized_pnl += bonus_coins
            earned_coins += bonus_coins
            bonus_note = f"（🍀幸運符發威，利潤 1.5 倍！額外 +{bonus_coins} 金幣）"
        self.pet.coins += earned_coins

        remaining = round(owned - shares, 4)
        if remaining <= 0.0001:
            self.pet.portfolio.pop(self.current_symbol, None)
            self.kline_widget.set_avg_cost(None)
        else:
            self.pet.portfolio[self.current_symbol]["shares"] = remaining

        pnl_sign = "+" if realized_pnl >= 0 else ""
        now_str = datetime.now().strftime("%m/%d %H:%M")
        self.pet.trade_history.insert(
            0,
            f"[{now_str}] 賣出 {self.current_symbol} {shares:.2f}股 @ {self.current_price:.2f} "
            f"(+{earned_coins}金幣｜實現損益 {pnl_sign}{realized_pnl}){bonus_note}"
        )
        self.pet.trade_history = self.pet.trade_history[:50]

        self.pet.last_interaction_time = time.time()
        self.pet.save_data()
        self._refresh_portfolio_view()
        self._refresh_history_view()
        self._show_tip(
            "賣出成功",
            f"已賣出 {shares:.2f} 股 {self.current_symbol}，獲得 {earned_coins} 金幣！\n"
            f"本次實現損益：{pnl_sign}{realized_pnl} 金幣{bonus_note}",
        )

    def _refresh_portfolio_view(self):
        self.wallet_label.setText(
            f"💰 持有金幣：{self.pet.coins} 枚（匯率：1 股價 = {COIN_RATE:g} 金幣）"
        )
        if not self.pet.portfolio:
            self.portfolio_box.setPlainText("目前沒有任何持股，點擊上方自選股或輸入代號查價後即可買入！")
            return

        lines = []
        total_pnl_coins = 0.0
        total_market_coins = 0.0
        for sym, data in self.pet.portfolio.items():
            shares = float(data.get("shares", 0.0))
            avg_cost = float(data.get("avg_cost", 0.0))
            mark_price = self.latest_prices.get(sym, avg_cost)
            tag = "現價" if sym in self.latest_prices else "均價估算"

            market_val = mark_price * shares * COIN_RATE
            pnl_coins = (mark_price - avg_cost) * shares * COIN_RATE
            pnl_pct = ((mark_price - avg_cost) / avg_cost * 100) if avg_cost > 0 else 0.0

            total_market_coins += market_val
            total_pnl_coins += pnl_coins
            sign = "+" if pnl_coins >= 0 else ""
            lines.append(
                f"• {sym}｜{shares:.2f} 股｜成本 {avg_cost:.2f}｜{tag} {mark_price:.2f}｜"
                f"損益 {sign}{pnl_coins:.1f} 金幣 ({sign}{pnl_pct:.1f}%)"
            )

        total_sign = "+" if total_pnl_coins >= 0 else ""
        lines.append(
            f"\n💼 總持股市值：{total_market_coins:.0f} 金幣｜未實現損益：{total_sign}{total_pnl_coins:.1f} 金幣"
        )
        self.portfolio_box.setPlainText("\n".join(lines))

    def _refresh_history_view(self):
        if not self.pet.trade_history:
            self.history_box.setPlainText("尚無歷史成交紀錄。")
        else:
            self.history_box.setPlainText("\n".join(self.pet.trade_history))