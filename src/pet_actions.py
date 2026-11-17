import random
import time
import winsound
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QInputDialog, QMessageBox, QComboBox, QListView
from .styles import DIALOG_STYLE


class PetActionHandler:
    @staticmethod
    def _style_combo_dialog(dialog):
        dialog.setStyleSheet(DIALOG_STYLE)
        combo = dialog.findChild(QComboBox)
        if combo:
            view = QListView()
            combo.setView(view)
            view.window().setWindowFlags(
                Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint
            )
            view.window().setAttribute(Qt.WA_TranslucentBackground)
            combo.setStyleSheet(DIALOG_STYLE)

    @staticmethod
    def _styled_info_box(pet, title, text):
        box = QMessageBox(pet)
        box.setWindowTitle(title)
        box.setText(text)
        box.setStyleSheet(DIALOG_STYLE)
        box.exec_()

    @staticmethod
    def start_part_time_job(pet):
        if pet.is_working or pet.is_reporting_work:
            pet.show_speech_bubble("我正在打工賺錢中耶，別打擾我！💼")
            return

        pet.last_interaction_time = time.time()
        job_types = [
            ("超商打工 (輕鬆)", "work1", 1, 10, 30),
            ("sukiya端盤子 (一般)", "work2", 3, 35, 60),
            ("招搖撞騙 (高薪)", "work3", 5, 70, 100),
        ]

        items = [f"{j[0]} - 耗時 {j[1]} 分鐘 (賺取 {j[2]} 金幣)" for j in job_types]
        dialog = QInputDialog(pet)
        dialog.setWindowTitle("選擇打工類型")
        dialog.setLabelText("請選擇要進行的工作：")
        dialog.setComboBoxItems(items)
        dialog.setComboBoxEditable(False)
        PetActionHandler._style_combo_dialog(dialog)

        ok = dialog.exec_() == QInputDialog.Accepted
        choice = dialog.textValue()

        if ok and choice:
            selected_job = next((j for j in job_types if j[0] in choice), None)
            if selected_job:
                name, job_key, duration_min, reward_coins, reward_favor = selected_job
                pet.is_working = True
                pet.current_job_type = job_key
                pet.current_work_loop_frame = 0
                pet.update_image()

                msg = f"出發去【{name}】囉！大約 {duration_min} 分鐘後回來賺錢！💰"
                pet.show_speech_bubble(msg)
                pet.speak_text("我去打工賺錢囉，等我回來！")
                pet.update_discord_status(f"正在進行 {name} 💼")

                ms = duration_min * 60 * 1000
                QTimer.singleShot(
                    ms,
                    lambda: PetActionHandler.finish_part_time_job(
                        pet, reward_coins, reward_favor, name
                    ),
                )

    @staticmethod
    def finish_part_time_job(pet, reward_coins, reward_favor, job_name):
        pet.is_working = False
        pet.is_reporting_work = True
        pet.update_image()

        pet.coins += reward_coins
        pet.favorability = min(pet.favorability + reward_favor, 100)
        pet.save_data()

        msg = f"打工結束！完成【{job_name}】，獲得了 {reward_coins} 金幣與好感度！🎉"
        pet.show_speech_bubble(msg)
        pet.speak_text("打工回來啦！賺到了好多的金幣呢！")
        try:
            winsound.Beep(1000, 200)
            winsound.Beep(1400, 200)
        except Exception:
            pass
        pet.update_discord_status(f"金幣: {pet.coins} 💰")

        QTimer.singleShot(4000, pet.restore_normal_clothes)

    @staticmethod
    def show_wallet(pet):
        pet.last_interaction_time = time.time()
        satiety = getattr(pet, "satiety", 80)
        msg = (
            f"💰 目前擁有金幣：{pet.coins} 枚\n"
            f"🍽️ 目前飽食度：{satiety} / 100\n"
            f"❤️ 目前好感度：{pet.favorability} 點\n\n"
            f"到「金幣商店 / 送禮」買珍珠奶茶或點心，可同時提升飽食度與好感度喔！"
        )
        PetActionHandler._styled_info_box(pet, "錢包與狀態", msg)

    @staticmethod
    def play_rps_game(pet):
        pet.last_interaction_time = time.time()
        items = ["剪刀", "石頭", "布"]
        dialog = QInputDialog(pet)
        dialog.setWindowTitle("猜拳小遊戲")
        dialog.setLabelText("請選擇你的出拳：")
        dialog.setComboBoxItems(items)
        dialog.setComboBoxEditable(False)
        PetActionHandler._style_combo_dialog(dialog)

        ok = dialog.exec_() == QInputDialog.Accepted
        user_choice = dialog.textValue()

        if ok and user_choice:
            pet_choice = random.choice(items)

            if user_choice == pet_choice:
                result_text = f"我出【{pet_choice}】。平手耶！"
                pet.speak_text("我們平手呢！")
            elif (
                (user_choice == "剪刀" and pet_choice == "布")
                or (user_choice == "石頭" and pet_choice == "剪刀")
                or (user_choice == "布" and pet_choice == "石頭")
            ):
                result_text = f"我出【{pet_choice}】。你贏了！好厲害～"
                pet.speak_text("哼，算你厲害，讓你贏一次！")
                pet.favorability = min(pet.favorability + 3, 100)
            else:
                result_text = f"我出【{pet_choice}】。我贏啦！哈哈～"
                pet.speak_text("耶！我贏了，再來一次嗎？")
                pet.favorability = max(pet.favorability - 2, 0)

            pet.save_data()
            pet.show_speech_bubble(result_text)
            pet.update_discord_status("正在玩猜拳遊戲 🎮")

    @staticmethod
    def add_todo_item(pet):
        pet.last_interaction_time = time.time()
        text_dialog = QInputDialog(pet)
        text_dialog.setWindowTitle("新增待辦事項")
        text_dialog.setLabelText("請輸入代辦內容：")
        text_dialog.setStyleSheet(DIALOG_STYLE)
        ok1 = text_dialog.exec_() == QInputDialog.Accepted
        task = text_dialog.textValue()

        if ok1 and task:
            num_dialog = QInputDialog(pet)
            num_dialog.setWindowTitle("設定提醒時間")
            num_dialog.setLabelText(f"幾分鐘後提醒你執行【{task}】？")
            num_dialog.setInputMode(QInputDialog.IntInput)
            num_dialog.setIntRange(1, 300)
            num_dialog.setIntValue(10)
            num_dialog.setIntStep(1)
            num_dialog.setStyleSheet(DIALOG_STYLE)
            ok2 = num_dialog.exec_() == QInputDialog.Accepted
            minutes = num_dialog.intValue()

            if ok2 and minutes:
                ms = minutes * 60 * 1000
                pet.todo_list.append(task)

                timer = QTimer(pet)
                timer.setSingleShot(True)
                timer.timeout.connect(
                    lambda t=timer, item=task: PetActionHandler.trigger_todo_alarm(pet, item, t)
                )
                timer.start(ms)

                msg = f"已記下！會在 {minutes} 分鐘後提醒你：{task} 📝"
                pet.show_speech_bubble(msg)
                pet.speak_text(f"好滴，我會記得提醒你做：{task}")
                pet.update_discord_status(f"待辦事項：{task} 📝")

    @staticmethod
    def trigger_todo_alarm(pet, task, timer=None):
        if task in pet.todo_list:
            pet.todo_list.remove(task)
        if timer is not None:
            timer.deleteLater()

        msg = f"叮咚！時間到囉！該處理這件事了：【{task}】💪"
        pet.show_speech_bubble(msg)
        pet.speak_text(f"主人！時間到了，快去處理：{task}")
        try:
            winsound.Beep(900, 400)
            winsound.Beep(1100, 400)
        except Exception:
            pass
        pet.update_discord_status(f"提醒完成事項：{task} 🔔")

    @staticmethod
    def show_todo_list(pet):
        pet.last_interaction_time = time.time()
        if not pet.todo_list:
            msg = "目前沒有任何待辦事項喔！過得很輕鬆呢~ ✨"
        else:
            msg = "目前的待辦清單：\n" + "\n".join([f"• {t}" for t in pet.todo_list])
        PetActionHandler._styled_info_box(pet, "待辦事項總覽", msg)