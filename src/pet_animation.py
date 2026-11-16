import os
import re
from PyQt5.QtGui import QPixmap, QTransform
from PyQt5.QtCore import Qt


class PetAnimationManager:
    VALID_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".gif")
    JOB_KEYS = ("work1", "work2", "work3")

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
    def _load_numbered_sequence(folder, pattern_regex):
        """依檔名中的數字順序，動態載入資料夾內所有符合規則的圖片"""
        if not folder or not os.path.isdir(folder):
            return []

        matched_files = []
        for fname in os.listdir(folder):
            lower_name = fname.lower()
            if not lower_name.endswith(PetAnimationManager.VALID_EXTS):
                continue
            m = pattern_regex.match(fname)
            if m:
                num = int(m.group(1))
                matched_files.append((num, fname))

        matched_files.sort(key=lambda x: x[0])

        pixmaps = []
        for _, fname in matched_files:
            pm = QPixmap(os.path.join(folder, fname))
            if not pm.isNull():
                pixmaps.append(pm)
        return pixmaps

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

        # 1. 動態載入走路動畫 (1.png, 2.png, ..., N.png)
        walk_pattern = re.compile(r"^(\d+)\.[^.]+$", re.IGNORECASE)
        frames = PetAnimationManager._load_numbered_sequence(skin_dir, walk_pattern)
        if not frames and skin_dir != default_dir:
            frames = PetAnimationManager._load_numbered_sequence(default_dir, walk_pattern)
        pet.frames = frames

        # 2. 載入單張狀態圖
        pet.drag_pixmap = PetAnimationManager._load_pixmap_with_fallback(
            skin_dir, default_dir, "pet_drag.png"
        )
        pet.idle_pixmap = PetAnimationManager._load_pixmap_with_fallback(
            skin_dir, default_dir, "pet_idle.png"
        )
        pet.work_start_pixmap = PetAnimationManager._load_pixmap_with_fallback(
            skin_dir, default_dir, "work_start.png"
        )

        # 3. 載入通用打工循環動畫 (work_1.png, work_2.png, ...)
        default_work_pattern = re.compile(r"^work_(\d+)\.[^.]+$", re.IGNORECASE)
        default_work_frames = PetAnimationManager._load_numbered_sequence(skin_dir, default_work_pattern)
        if not default_work_frames and skin_dir != default_dir:
            default_work_frames = PetAnimationManager._load_numbered_sequence(default_dir, default_work_pattern)
        pet.work_loop_frames = default_work_frames

        # 4. 分別載入 3 種工作的專屬動畫 (work1_1.png, work2_1.png, work3_1.png ...)
        pet.job_loop_frames = {}
        pet.job_start_pixmaps = {}
        for job_key in PetAnimationManager.JOB_KEYS:
            job_pattern = re.compile(rf"^{job_key}_(\d+)\.[^.]+$", re.IGNORECASE)
            j_frames = PetAnimationManager._load_numbered_sequence(skin_dir, job_pattern)
            if not j_frames and skin_dir != default_dir:
                j_frames = PetAnimationManager._load_numbered_sequence(default_dir, job_pattern)
            pet.job_loop_frames[job_key] = j_frames

            # 專屬完成/回報圖：work1_start.png, work2_start.png, work3_start.png
            j_start = PetAnimationManager._load_pixmap_with_fallback(
                skin_dir, default_dir, f"{job_key}_start.png"
            )
            pet.job_start_pixmaps[job_key] = j_start

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
    def _get_active_work_assets(pet):
        """取得當前工作對應的 (循環圖列表, 完成回報圖)，若無專屬圖則自動退回通用打工圖"""
        job_key = getattr(pet, "current_job_type", "default")
        job_loops = getattr(pet, "job_loop_frames", {}).get(job_key, [])
        active_loops = job_loops if job_loops else getattr(pet, "work_loop_frames", [])

        job_start = getattr(pet, "job_start_pixmaps", {}).get(job_key, QPixmap())
        active_start = job_start if not job_start.isNull() else getattr(pet, "work_start_pixmap", QPixmap())
        return active_loops, active_start

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
            _, active_start = PetAnimationManager._get_active_work_assets(pet)
            pixmap = active_start if not active_start.isNull() else pet.frames[0]
        elif pet.is_working:
            active_loops, active_start = PetAnimationManager._get_active_work_assets(pet)
            if active_loops:
                idx = pet.current_work_loop_frame % len(active_loops)
                pixmap = active_loops[idx]
            else:
                pixmap = active_start if not active_start.isNull() else pet.frames[0]
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
            active_loops, _ = PetAnimationManager._get_active_work_assets(pet)
            if active_loops:
                pet.current_work_loop_frame = (pet.current_work_loop_frame + 1) % len(active_loops)
                PetAnimationManager.update_image(pet)
            return

        if pet.is_reporting_work:
            return

        if pet.is_walking and not pet.dragging:
            pet.current_frame = (pet.current_frame + 1) % len(pet.frames)
            PetAnimationManager.update_image(pet)