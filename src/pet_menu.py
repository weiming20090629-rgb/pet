import time
import winsound
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)
from .pet_actions import PetActionHandler
from .styles import CONTEXT_MENU_STYLE, DIALOG_STYLE, VOLUME_SLIDER_STYLE
from .pet_stock import StockDialog
from .pet_shop import PetShopDialog


class PetMenuManager:
    """管理桌寵右鍵選單、音量/透明度滑桿與選單動作執行"""

    @staticmethod
    def _build_slider_action(menu, label_prefix, initial_pct, min_val, max_val, on_change_callback):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(25, 4, 15, 4)
        layout.setSpacing(8)

        val_label = QLabel(f"{label_prefix}: {initial_pct}%")
        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(initial_pct)
        slider.setFixedWidth(110)
        slider.setStyleSheet(VOLUME_SLIDER_STYLE)

        def handle_val(val):
            val_label.setText(f"{label_prefix}: {val}%")
            on_change_callback(val)

        slider.valueChanged.connect(handle_val)
        layout.addWidget(val_label)
        layout.addWidget(slider)

        action = QWidgetAction(menu)
        action.setDefaultWidget(container)
        menu.addAction(action)
        return action

    @staticmethod
    def open_opacity_dialog(pet):
        dlg = QDialog(pet)
        dlg.setWindowTitle("調整桌寵透明度")
        dlg.setWindowFlags(dlg.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        dlg.setStyleSheet(DIALOG_STYLE)
        layout = QVBoxLayout(dlg)

        current_pct = int(pet.windowOpacity() * 100)
        label = QLabel(f"目前透明度：{current_pct}%")

        slider = QSlider(Qt.Horizontal)
        slider.setRange(20, 100)
        slider.setValue(current_pct)
        slider.setStyleSheet(VOLUME_SLIDER_STYLE)

        def on_change(val):
            pet.setWindowOpacity(val / 100.0)
            label.setText(f"目前透明度：{val}%")

        slider.valueChanged.connect(on_change)

        btn_row = QHBoxLayout()
        reset_btn = QPushButton("重設 100%")
        reset_btn.clicked.connect(lambda: slider.setValue(100))
        ok_btn = QPushButton("確定")
        ok_btn.clicked.connect(dlg.accept)
        btn_row.addWidget(reset_btn)
        btn_row.addWidget(ok_btn)

        layout.addWidget(label)
        layout.addWidget(slider)
        layout.addLayout(btn_row)
        dlg.exec_()

    @staticmethod
    def show_context_menu(pet, pos):
        menu = QMenu(pet)
        menu.setStyleSheet(CONTEXT_MENU_STYLE)
        menu.setWindowFlags(menu.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        menu.setAttribute(Qt.WA_TranslucentBackground, True)

        if pet.favorability >= 80:
            status_text = f"❤️ 好感度: 很高 | 💰 金幣: {pet.coins}"
        elif pet.favorability >= 50:
            status_text = f"💛 好感度: 普通 | 💰 金幣: {pet.coins}"
        elif pet.favorability > 0:
            status_text = f"💢 好感度: 偏低 (快歸零囉) | 💰 金幣: {pet.coins}"
        else:
            status_text = f"🔥 好感度: 歸零 (黑化制裁中) | 💰 金幣: {pet.coins}"

        favor_action = menu.addAction(status_text)
        favor_action.setEnabled(False)

        menu.addSeparator()

        pet_action = menu.addAction("摸摸頭 (增加好感)")
        punch_action = menu.addAction("💥 打她一拳 (減少好感)")
        job_action = menu.addAction("💼 打工賺錢")
        wallet_action = menu.addAction("👛 查看錢包與狀態")
        shop_action = menu.addAction("🛍️ 金幣商店 / 送禮")
        rps_action = menu.addAction("🎮 玩猜拳小遊戲")
        weather_action = menu.addAction("🌤️ 查詢目前天氣")
        stock_action = menu.addAction("📈 股票交易室")

        todo_menu = menu.addMenu("📝 待辦事項與提醒")
        add_todo_action = todo_menu.addAction("➕ 新增待辦提醒")
        view_todo_action = todo_menu.addAction("📋 查看待辦清單")

        voice_status_text = "🔊 語音朗讀：開啟" if pet.voice_enabled else "🔇 語音朗讀：關閉"
        voice_action = menu.addAction(voice_status_text)

        current_vol = getattr(pet, "voice_volume", 0.8)
        volume_action = PetMenuManager._build_slider_action(
            menu,
            "🔉 音量",
            int(current_vol * 100),
            0,
            100,
            lambda val: setattr(pet, "voice_volume", val / 100.0),
        )

        current_opacity = int(pet.windowOpacity() * 100)
        opacity_action = PetMenuManager._build_slider_action(
            menu,
            "🪟 透明度",
            current_opacity,
            20,
            100,
            lambda val: pet.setWindowOpacity(val / 100.0),
        )

        menu.addSeparator()
        exit_action = menu.addAction("退出桌寵")

        action = menu.exec_(pos)
        pet.last_interaction_time = time.time()

        if action == pet_action:
            pet.favorability = min(pet.favorability + 5, 100)
            pet.save_data()
            msg = f"哼哼~被摸頭了，好感度上升！(目前: {pet.favorability})"
            pet.show_speech_bubble(msg)
            pet.speak_text("哼哼，感覺還不錯嘛！")
            pet.update_discord_status(f"好感度 {pet.favorability} 🐾")
        elif action == punch_action:
            pet.favorability = max(pet.favorability - 5, 0)
            pet.save_data()
            msg = f"好痛！你幹嘛打我... (目前好感度: {pet.favorability})"
            pet.show_speech_bubble(msg)
            pet.speak_text("好痛！你為什麼要打我，太過分了！")
            try:
                winsound.Beep(300, 200)
            except Exception:
                pass
            pet.update_discord_status(f"被打了一拳，好感度 {pet.favorability} 💢")
        elif action == job_action:
            PetActionHandler.start_part_time_job(pet)
        elif action == wallet_action:
            PetActionHandler.show_wallet(pet)
        elif action == shop_action:
            dialog = PetShopDialog(pet)
            dialog.exec_()
        elif action == rps_action:
            PetActionHandler.play_rps_game(pet)
        elif action == weather_action:
            pet.manual_check_weather()
        elif action == stock_action:
            dialog = StockDialog(pet)
            dialog.exec_()
        elif action == add_todo_action:
            PetActionHandler.add_todo_item(pet)
        elif action == view_todo_action:
            PetActionHandler.show_todo_list(pet)
        elif action == voice_action:
            pet.voice_enabled = not pet.voice_enabled
            state_str = "開啟" if pet.voice_enabled else "關閉"
            pet.show_speech_bubble(f"語音功能已{state_str}囉！")
        elif action == opacity_action:
            PetMenuManager.open_opacity_dialog(pet)
        elif action == exit_action:
            try:
                if hasattr(pet, "RPC"):
                    pet.RPC.close()
            except Exception:
                pass
            pet.bubble_widget.close()
            QApplication.quit()

        _ = volume_action