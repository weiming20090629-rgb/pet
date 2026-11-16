import time
import psutil
from PyQt5.QtCore import QTimer
from pypresence import Presence
from .punishment import PunishmentManager


class PetMonitorManager:
    """管理飽食度定時器、冷落扣好感、系統監控與 Discord RPC"""

    @staticmethod
    def init_discord_rpc(pet, client_id: str):
        try:
            pet.RPC = Presence(client_id)
            pet.RPC.connect()
            pet.start_time = time.time()
            pet.RPC.update(
                state=f"金幣: {pet.coins} 💰 | 好感度: {pet.favorability}",
                details="桌面生活秘書與打工養成中",
                start=pet.start_time,
                large_image="pet_idle",
                large_text="桌面寵物",
            )
        except Exception:
            pass

    @staticmethod
    def update_discord_status(pet, state_text: str):
        try:
            if hasattr(pet, "RPC"):
                pet.RPC.update(
                    state=state_text,
                    details=f"金幣: {pet.coins} 💰 | 好感度: {pet.favorability}",
                    start=pet.start_time,
                    large_image="pet_idle",
                    large_text="桌面寵物",
                )
        except Exception:
            pass

    @staticmethod
    def close_discord_rpc(pet):
        try:
            if hasattr(pet, "RPC"):
                pet.RPC.close()
        except Exception:
            pass

    @staticmethod
    def init_satiety_timer(pet):
        pet._last_hungry_alert_time = 0.0
        pet.satiety_timer = QTimer(pet)
        pet.satiety_timer.timeout.connect(lambda: PetMonitorManager.update_satiety(pet))
        pet.satiety_timer.start(2 * 60 * 1000)

    @staticmethod
    def update_satiety(pet):
        prev_satiety = pet._clamp_satiety(getattr(pet, "satiety", 80))
        if prev_satiety > 0:
            pet.satiety = max(0, prev_satiety - 2)
            pet.save_data()
        else:
            pet.satiety = 0

        if pet.dragging or pet.bubble_widget.isVisible() or pet.is_working or pet.is_reporting_work:
            return

        now = time.time()
        if pet.satiety <= 25 and (now - getattr(pet, "_last_hungry_alert_time", 0.0)) >= 600:
            pet._last_hungry_alert_time = now
            if pet.satiety == 0:
                msg = "肚子餓扁了啦……快去商店買點東西吃吧！😵"
                speech = "我好餓喔，快去商店買食物給我吃！"
            else:
                msg = f"有點餓了呢（飽食度 {pet.satiety}/100），要去商店挑點食物嗎？🍪"
                speech = "我有點餓了，想去買點東西吃。"
            pet.show_speech_bubble(msg)
            pet.speak_text(speech)
            PetMonitorManager.update_discord_status(pet, f"飽食度偏低 ({pet.satiety}/100) 🍽️")

    @staticmethod
    def init_neglect_timer(pet):
        pet.neglect_timer = QTimer(pet)
        pet.neglect_timer.timeout.connect(lambda: PetMonitorManager.check_neglect(pet))
        pet.neglect_timer.start(30000)

    @staticmethod
    def check_neglect(pet):
        if (
            pet.dragging
            or pet.bubble_widget.isVisible()
            or pet.is_working
            or pet.is_reporting_work
            or pet.favorability <= 0
        ):
            return

        current_time = time.time()
        if current_time - pet.last_interaction_time > 60:
            pet.favorability = max(pet.favorability - 5, 0)
            pet.save_data()
            text = "哼，都都不理我..."
            pet.show_speech_bubble(text)
            pet.speak_text(text)
            PetMonitorManager.update_discord_status(pet, f"好感度下降 ({pet.favorability}) 💢")
            pet.last_interaction_time = current_time

    @staticmethod
    def init_punishment_timer(pet):
        pet.punishment_timer = QTimer(pet)
        pet.punishment_timer.timeout.connect(lambda: PetMonitorManager.execute_punishment_loop(pet))
        pet.punishment_timer.start(10000)

    @staticmethod
    def execute_punishment_loop(pet):
        if pet.favorability <= 0:
            inv = getattr(pet, "inventory", {})
            if inv.get("shield", 0) > 0:
                inv["shield"] -= 1
                pet.favorability = 30
                pet.save_data()
                msg = "🛡️ 觸發【黑化免死金牌】！成功抵銷關視窗制裁，好感度回復至 30！"
                pet.show_speech_bubble(msg)
                pet.speak_text("哼，算你運氣好有免死金牌，這次就放過你！")
                PetMonitorManager.update_discord_status(pet, "免死金牌發動，逃過一劫 🛡️")
                return

            warning_text = "💢 好感度歸零！本小姐要發飆關閉所有視窗囉！"
            pet.show_speech_bubble(warning_text)
            pet.speak_text("好感度歸零！我要把所有視窗通通關掉！")
            QTimer.singleShot(
                3000,
                lambda: PunishmentManager.close_all_other_windows(pet, pet.bubble_widget),
            )

    @staticmethod
    def init_system_monitor(pet):
        pet.system_alert_cooldown = 0
        pet.monitor_timer = QTimer(pet)
        pet.monitor_timer.timeout.connect(lambda: PetMonitorManager.check_system_resources(pet))
        pet.monitor_timer.start(10000)

    @staticmethod
    def check_system_resources(pet):
        if pet.bubble_widget.isVisible() or pet.dragging:
            return

        try:
            cpu_usage = psutil.cpu_percent(interval=None)
            ram_info = psutil.virtual_memory()
            ram_usage = ram_info.percent
            current_time = time.time()

            if (cpu_usage > 85 or ram_usage > 85) and current_time - pet.system_alert_cooldown > 180:
                if cpu_usage > 85 and ram_usage > 85:
                    text = f"⚠️ 電腦負荷過重！CPU: {cpu_usage:.0f}% | RAM: {ram_usage:.0f}% 主人小心當機！"
                    speech = "哇！CPU跟記憶體都快爆掉囉，主人注意一下！"
                elif cpu_usage > 85:
                    text = f"⚠️ CPU 正在燃燒！(使用率 {cpu_usage:.0f}%) 主人小心當機喔！"
                    speech = "哇！電腦好燙，CPU 負荷太高囉！"
                else:
                    text = f"⚠️ 記憶體快滿啦！(RAM 使用率 {ram_usage:.0f}%) 記得清理背景程式喔！"
                    speech = "記憶體快被塞滿囉，主人要不要關掉一些分頁？"

                pet.show_speech_bubble(text)
                pet.speak_text(speech)
                pet.system_alert_cooldown = current_time
        except Exception as e:
            print(f"系統監控錯誤: {e}")