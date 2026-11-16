import time
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QFrame,
)
from .styles import DIALOG_STYLE

SHOP_ITEMS = [
    {
        "id": "candy",
        "name": "🍬 草莓糖果",
        "price": 15,
        "type": "gift",
        "favor": 5,
        "satiety": 10,
        "desc": "甜甜的小零嘴，心情變好一點（好感 +5、飽食 +10）",
        "speech": "哇，是草莓糖果！謝謝主人，好甜喔～",
    },
    {
        "id": "boba",
        "name": "🧋 珍珠奶茶",
        "price": 35,
        "type": "gift",
        "favor": 12,
        "satiety": 25,
        "desc": "肥宅快樂水，喝了超開心又解餓（好感 +12、飽食 +25）",
        "speech": "是珍奶耶！主人最懂我了，幸福感爆棚～",
    },
    {
        "id": "cake",
        "name": "🍰 豪華草莓蛋糕",
        "price": 80,
        "type": "gift",
        "favor": 28,
        "satiety": 45,
        "desc": "精緻下午茶甜點，生氣消一半又能吃飽（好感 +28、飽食 +45）",
        "speech": "天啊看起來超好吃！看在蛋糕的份上就原諒你吧～",
    },
    {
        "id": "plushie",
        "name": "🧸 限量絨毛玩偶",
        "price": 150,
        "type": "gift",
        "favor": 100,
        "desc": "夢幻逸品禮物，好感度回滿至 100（好感回滿）",
        "speech": "好可愛的玩偶！！我最最喜歡主人了，啾咪！",
    },
    {
        "id": "shield",
        "name": "🛡️ 黑化免死金牌",
        "price": 200,
        "type": "item",
        "desc": "持有時，若好感度歸零發動黑化懲罰，自動消耗並抵銷關視窗（好感回 30）",
        "speech": "哼，收下這個護身符，下次發飆就勉強放你一馬！",
    },
    {
        "id": "charm",
        "name": "🍀 投資幸運符",
        "price": 120,
        "type": "item",
        "desc": "下次賣出股票且「獲利」時自動消耗，讓本次賺到的利潤變為 1.5 倍！（虧損不消耗）",
        "speech": "有了投資幸運符，下次賣股票賺錢一定會大豐收的！",
    },
]


class PetShopDialog(QDialog):
    """桌寵金幣商店：購買禮物/食物增加好感與飽食度、購買功能道具"""

    def __init__(self, pet):
        super().__init__(pet)
        self.pet = pet
        if not hasattr(self.pet, "inventory") or not isinstance(self.pet.inventory, dict):
            self.pet.inventory = {"shield": 0, "charm": 0}
        if not hasattr(self.pet, "satiety"):
            self.pet.satiety = 80

        self.setWindowTitle("🛍️ 桌寵金幣小舖")
        self.setMinimumWidth(520)
        self.setStyleSheet(DIALOG_STYLE)
        self._init_ui()
        self._refresh_header()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        self.status_label = QLabel()
        self.status_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #1e3a5f;")
        layout.addWidget(self.status_label)

        self.bag_label = QLabel()
        self.bag_label.setStyleSheet("color: #475569; font-size: 12px;")
        layout.addWidget(self.bag_label)

        for item in SHOP_ITEMS:
            card = QFrame()
            card.setStyleSheet(
                "QFrame { background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 6px; }"
            )
            row = QHBoxLayout(card)
            row.setContentsMargins(10, 6, 10, 6)

            info_col = QVBoxLayout()
            title_lbl = QLabel(f"{item['name']}  —  💰 {item['price']} 金幣")
            title_lbl.setStyleSheet("font-weight: bold; border: none; background: transparent;")
            desc_lbl = QLabel(item["desc"])
            desc_lbl.setStyleSheet("color: #64748b; font-size: 12px; border: none; background: transparent;")
            info_col.addWidget(title_lbl)
            info_col.addWidget(desc_lbl)

            buy_btn = QPushButton("購買")
            buy_btn.setFixedWidth(72)
            buy_btn.clicked.connect(lambda checked, it=item: self.buy_item(it))

            row.addLayout(info_col, stretch=1)
            row.addWidget(buy_btn)
            layout.addWidget(card)

    def _refresh_header(self):
        inv = self.pet.inventory
        satiety = getattr(self.pet, "satiety", 80)
        self.status_label.setText(
            f"💰 金幣：{self.pet.coins} 枚  |  ❤️ 好感：{self.pet.favorability}/100  |  🍽️ 飽食：{satiety}/100"
        )
        self.bag_label.setText(
            f"🎒 持有道具：🛡️ 免死金牌 x{inv.get('shield', 0)}   ｜   🍀 投資幸運符 x{inv.get('charm', 0)}"
        )

    def _show_tip(self, title: str, text: str):
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setText(text)
        box.setStyleSheet(DIALOG_STYLE)
        box.exec_()

    def buy_item(self, item: dict):
        price = item["price"]
        if self.pet.coins < price:
            self._show_tip(
                "金幣不足",
                f"購買「{item['name']}」需要 {price} 金幣，目前只有 {self.pet.coins} 金幣。\n快去打工或炒股賺錢吧！",
            )
            return

        sat_gain_cfg = item.get("satiety", 0)
        current_sat = getattr(self.pet, "satiety", 80)
        if item["type"] == "gift" and sat_gain_cfg > 0 and current_sat >= 100:
            self._show_tip(
                "吃太飽囉",
                f"目前飽食度已經 100/100 囉，先消化一下再買「{item['name']}」吧！",
            )
            return

        self.pet.coins -= price
        self.pet.last_interaction_time = time.time()

        if item["type"] == "gift":
            old_favor = self.pet.favorability
            self.pet.favorability = min(self.pet.favorability + item.get("favor", 0), 100)
            gained_favor = self.pet.favorability - old_favor

            old_sat = getattr(self.pet, "satiety", 80)
            self.pet.satiety = max(0, min(100, old_sat + sat_gain_cfg))
            gained_sat = self.pet.satiety - old_sat

            bubble_msg = (
                f"收到【{item['name']}】！好感 +{gained_favor} ({self.pet.favorability})、"
                f"飽食 +{gained_sat} ({self.pet.satiety}/100) 💕"
            )
        else:
            item_id = item["id"]
            self.pet.inventory[item_id] = self.pet.inventory.get(item_id, 0) + 1
            bubble_msg = f"獲得道具【{item['name']}】！目前持有 {self.pet.inventory[item_id]} 個 ✨"

        self.pet.save_data()
        self._refresh_header()
        self.pet.show_speech_bubble(bubble_msg)
        self.pet.speak_text(item["speech"])
        self.pet.update_discord_status(
            f"好感 {self.pet.favorability} | 飽食 {self.pet.satiety}/100 | 金幣 {self.pet.coins} 💰"
        )