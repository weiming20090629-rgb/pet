import os
from PyQt5.QtGui import QPixmap, QTransform
from PyQt5.QtCore import Qt


class PetAnimationManager:
    FRAME_FILES = ["1.png", "2.png", "3.png", "4.png", "5.png", "6.png", "7.png", "8.png"]
    WORK_LOOP_FILES = ["work_1.png", "work_2.png", "work_3.png"]

    @staticmethod
    def list_skins(root_dir):
        assets_dir = os.path.join(root_dir, "assets")
        if not os.path.isdir(assets_dir):
            return ["default"]

        skins = sorted(
            name
            for name in os.listdir(assets_dir)
            if os.path.isdir(os.path.join(assets_dir, name)) and not name.startswith(".")
        )
        return skins if skins else ["default"]

    @staticmethod
    def _load_pixmap_with_fallback(skin_dir, default_dir, filename):
        for folder in (skin_dir, default_dir):
            if folder:
                path = os.path.join(folder, filename)
                if os.path.exists(path):
                    pm = QPixmap(path)
                    if not pm.isNull():
                        return pm
        return QPixmap()

    @staticmethod
    def init_animations(pet, root_dir, skin_name=None):
        assets_dir = os.path.join(root_dir, "assets")
        available_skins = PetAnimationManager.list_skins(root_dir)
        chosen_skin = skin_name or getattr(pet, "skin", "default")
        if chosen_skin not in available_skins:
            chosen_skin = available_skins[0]
        pet.skin = chosen_skin

        skin_dir = os.path.join(assets_dir, chosen_skin)
        default_dir = os.path.join(assets_dir, "default")
        if not os.path.isdir(skin_dir) and os.path.isdir(assets_dir):
            skin_dir = assets_dir

        frames = []
        for file in PetAnimationManager.FRAME_FILES:
            pm = PetAnimationManager._load_pixmap_with_fallback(skin_dir, default_dir, file)
            if not pm.isNull():
                frames.append(pm)

        pet.frames = frames
        pet.drag_pixmap = PetAnimationManager._load_pixmap_with_fallback(
            skin_dir, default_dir, "pet_drag.png"
        )
        pet.idle_pixmap = PetAnimationManager._load_pixmap_with_fallback(
            skin_dir, default_dir, "pet_idle.png"
        )
        pet.work_start_pixmap = PetAnimationManager._load_pixmap_with_fallback(
            skin_dir, default_dir, "work_start.png"
        )

        work_loop_frames = []
        for file in PetAnimationManager.WORK_LOOP_FILES:
            pm = PetAnimationManager._load_pixmap_with_fallback(skin_dir, default_dir, file)
            if not pm.isNull():
                work_loop_frames.append(pm)
        pet.work_loop_frames = work_loop_frames

        if not pet.frames:
            pet.label.setText("🐾 找不到圖片")
            pet.label.setStyleSheet(
                "color: white; background-color: rgba(0, 0, 0, 160); "
                "font-size: 14px; border-radius: 8px; padding: 10px;"
            )
            pet.resize(200, 60)
            return False

        pet.current_frame = (
            pet.current_frame % len(pet.frames) if hasattr(pet, "current_frame") else 0
        )
        pet.current_work_loop_frame = 0
        return True

    @staticmethod
    def switch_skin(pet, root_dir, skin_name):
        ok = PetAnimationManager.init_animations(pet, root_dir, skin_name)
        if ok:
            pet.update_image()
            if hasattr(pet, "bubble_widget") and pet.bubble_widget.isVisible():
                pet.update_bubble_position()
        return ok

    @staticmethod
    def update_image(pet):
        if not pet.frames:
            return

        if pet.is_reporting_work:
            pixmap = pet.work_start_pixmap if not pet.work_start_pixmap.isNull() else pet.frames[0]
        elif pet.is_working:
            if pet.work_loop_frames:
                idx = pet.current_work_loop_frame % len(pet.work_loop_frames)
                pixmap = pet.work_loop_frames[idx]
            else:
                pixmap = pet.work_start_pixmap if not pet.work_start_pixmap.isNull() else pet.frames[0]
        elif pet.dragging:
            pixmap = pet.drag_pixmap if not pet.drag_pixmap.isNull() else pet.frames[0]
        elif not pet.is_walking and not pet.idle_pixmap.isNull():
            pixmap = pet.idle_pixmap
        else:
            idx = pet.current_frame % len(pet.frames)
            pixmap = pet.frames[idx]

        transform = QTransform()
        if pet.direction == -1 and not pet.dragging and not pet.is_working and not pet.is_reporting_work:
            transform.scale(-1 * pet.scale_factor, pet.scale_factor)
        else:
            transform.scale(pet.scale_factor, pet.scale_factor)

        scaled_pixmap = pixmap.transformed(transform, Qt.SmoothTransformation)

        padding = 10
        w = scaled_pixmap.width() + padding
        h = scaled_pixmap.height() + padding

        pet.resize(w, h)
        pet.label.resize(w, h)
        pet.label.setPixmap(scaled_pixmap)

    @staticmethod
    def next_frame(pet):
        if not pet.frames:
            return

        if pet.is_working:
            if pet.work_loop_frames:
                pet.current_work_loop_frame = (pet.current_work_loop_frame + 1) % len(pet.work_loop_frames)
                PetAnimationManager.update_image(pet)
            return

        if pet.is_reporting_work:
            return

        if pet.is_walking and not pet.dragging:
            pet.current_frame = (pet.current_frame + 1) % len(pet.frames)
            PetAnimationManager.update_image(pet)