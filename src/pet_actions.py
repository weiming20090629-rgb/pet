import os
import random
import time
import winsound
from PyQt5.QtWidgets import QInputDialog, QMessageBox

class PetActionHandler:
    @staticmethod
    def start_part_time_job(pet):
        if pet.is_working or pet.is_reporting_work:
            pet.show_speech_bubble("我正在打工賺錢中耶，別打擾我！💼")
            return

        pet.last_interaction_time = time.time()
        job_types = [
            ("超商打工 (輕鬆)", 1, 10, 30),      
            ("咖啡廳幫忙 (一般)", 3, 35, 60),
            ("文書外包 (高薪)", 5, 70, 100)
        ]
        
        items = [f"{j[0]} - 耗時 {j[1]} 分鐘 (賺取 {j[2]} 金幣)" for j in job_types]
        choice, ok = QInputDialog.getItem(pet, "選擇打工類型", "請選擇要進行的工作：", items, 0, False)
        
        if ok and choice:
            selected_job = None
            for j in job_types:
                if j[0] in choice:
                    selected_job = j
                    break
            
            if selected_job:
                name, duration_min, reward_coins, reward_favor = selected_job
                pet.is_working = True
                pet.current_work_loop_frame = 0  
                pet.update_image() 
                
                msg = f"出發去【{name}】囉！大約 {duration_min} 分鐘後回來賺錢！💰"
                pet.show_speech_bubble(msg)
                pet.speak_text(f"我去打工賺錢囉，等我回來！")
                pet.update_discord_status(f"正在進行 {name} 💼")
                
                ms = duration_min * 60 * 1000
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(ms, lambda: PetActionHandler.finish_part_time_job(pet, reward_coins, reward_favor, name))

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
        pet.speak_text(f"打工回來啦！賺到了好多的金幣呢！")
        try:
            winsound.Beep(1000, 200)
            winsound.Beep(1400, 200)
        except:
            pass
        pet.update_discord_status(f"金幣: {pet.coins} 💰")
        
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(4000, pet.restore_normal_clothes)

    @staticmethod
    def show_wallet(pet):
        pet.last_interaction_time = time.time()
        coins_display = pet.coins
        msg = f"💰 目前擁有金幣：{coins_display} 枚\n❤️ 目前好感度：{pet.favorability} 點\n\n快去右鍵選單讓桌寵去打工賺更多金幣吧！"
        QMessageBox.information(pet, "錢包與狀態", msg)

    @staticmethod
    def play_rps_game(pet):
        pet.last_interaction_time = time.time()
        items = ["剪刀", "石頭", "布"]
        user_choice, ok = QInputDialog.getItem(pet, "猜拳小遊戲", "請選擇你的出拳：", items, 0, False)
        
        if ok and user_choice:
            pet_choice = random.choice(items)
            
            if user_choice == pet_choice:
                result_text = f"我出【{pet_choice}】。平手耶！"
                pet.speak_text("我們平手呢！")
            elif (
                (user_choice == "剪刀" and pet_choice == "布") or
                (user_choice == "石頭" and pet_choice == "剪刀") or
                (user_choice == "布" and pet_choice == "石頭")
            ):
                result_text = f"我出【{pet_choice}】。你贏了！好厲害～"
                pet.speak_text("哼s，算你厲害，讓你贏一次！")
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
        task, ok1 = QInputDialog.getText(pet, "新增待辦事項", "請輸入代辦內容：")
        if ok1 and task:
            minutes, ok2 = QInputDialog.getInt(pet, "設定提醒時間", f"幾分鐘後提醒你執行【{task}】？", 10, 1, 300, 1)
            if ok2 and minutes:
                ms = minutes * 60 * 1000
                pet.todo_list.append(task)
                
                from PyQt5.QtCore import QTimer
                timer = QTimer(pet)
                timer.setSingleShot(True)
                timer.timeout.connect(lambda: PetActionHandler.trigger_todo_alarm(pet, task))
                timer.start(ms)
                
                msg = f"已記下！會在 {minutes} 分鐘後提醒你：{task} 📝"
                pet.show_speech_bubble(msg)
                pet.speak_text(f"好滴，我會記得提醒你做：{task}")
                pet.update_discord_status(f"待辦事項：{task} 📝")

    @staticmethod
    def trigger_todo_alarm(pet, task):
        msg = f"叮咚！時間到囉！該處理這件事了：【{task}】💪"
        pet.show_speech_bubble(msg)
        pet.speak_text(f"主人！時間到了，快去處理：{task}")
        try:
            winsound.Beep(900, 400)
            winsound.Beep(1100, 400)
        except:
            pass
        pet.update_discord_status(f"提醒完成事項：{task} 🔔")

    @staticmethod
    def show_todo_list(pet):
        pet.last_interaction_time = time.time()
        if not pet.todo_list:
            msg = "目前沒有任何待辦事項喔！過得很輕鬆呢~ ✨"
        else:
            msg = "目前的待辦清單：\n" + "\n".join([f"• {t}" for t in pet.todo_list])
        QMessageBox.information(pet, "待辦事項總覽", msg)