import os
import re
from PyQt5.QtGui import QPainter, QPixmap, QTransform
from PyQt5.QtCore import Qt


class PetAnimationManager:
    VALID_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".gif")
    JOB_KEYS = ("work1", "work2", "work3")
    WORK3_BG_ROTATE_STEP = 25  # work3 背景每次影格旋轉角度（度）

    @staticmethod
    def _resolve_assets_dir(base_dir):
        if os.path.basename(os.path.normpath(base_dir)).lower() == "assets":
            return base_dir
        nested = os.path.join(base_dir, "assets")
        return nested if os.path.isdir(nested) else base_dir

    @staticmethod
    def _resolve_skins_dir(base_dir):
        assets_dir = PetAnimationManager._resolve_assets_dir(base_dir)
        skins_dir = os.path.join(assets_dir, "skins")
        return skins_dir if os.path.isdir(skins_dir) else assets_dir
    
    @staticmethod
    def list_skins(base_dir):
        skins_dir = PetAnimationManager._resolve_skins_dir(base_dir)
        if not os.path.isdir(skins_dir):
            return ["default"]

        skins = sorted(
            name
            for name in os.listdir(skins_dir)
            if os.path.isdir(os.path.join(skins_dir, name))
            and not name.startswith(".")
            and name.lower() != "engine"
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
    def _compose_rotating_scene(person_pm, bg_pm, angle):
        """將旋轉後的背景圖與人物圖合成在同一張 QPixmap"""
        if person_pm.isNull() and bg_pm.isNull():
            return QPixmap()
        if bg_pm.isNull():
            return person_pm
        if person_pm.isNull():
            bg_transform = QTransform().rotate(angle)
            return bg_pm.transformed(bg_transform, Qt.SmoothTransformation)

        canvas_w = max(person_pm.width(), bg_pm.width())
        canvas_h = max(person_pm.height(), bg_pm.height())
        canvas = QPixmap(canvas_w, canvas_h)
        canvas.fill(Qt.transparent)

        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        bg_transform = QTransform()
        bg_transform.translate(bg_pm.width() / 2.0, bg_pm.height() / 2.0)
        bg_transform.rotate(angle)
        bg_transform.translate(-bg_pm.width() / 2.0, -bg_pm.height() / 2.0)
        rotated_bg = bg_pm.transformed(bg_transform, Qt.SmoothTransformation)

        bg_x = (canvas_w - rotated_bg.width()) // 2
        bg_y = (canvas_h - rotated_bg.height()) // 2
        painter.drawPixmap(bg_x, bg_y, rotated_bg)

        person_x = (canvas_w - person_pm.width()) // 2
        person_y = (canvas_h - person_pm.height()) // 2
        painter.drawPixmap(person_x, person_y, person_pm)

        painter.end()
        return canvas

    @staticmethod
    def _resolve_assets_dir(root_dir):
        if os.path.basename(os.path.normpath(root_dir)).lower() == "assets":
            return root_dir
        nested = os.path.join(root_dir, "assets")
        return nested if os.path.isdir(nested) else root_dir

    @staticmethod
    def init_animations(pet, root_dir, skin_name=None):
        assets_dir = PetAnimationManager._resolve_assets_dir(root_dir)
        skins_dir = PetAnimationManager._resolve_skins_dir(root_dir)
        available_skins = PetAnimationManager.list_skins(root_dir)
        chosen_skin = skin_name or getattr(pet, "skin", "default")
        if chosen_skin not in available_skins:
            chosen_skin = available_skins[0]
        pet.skin = chosen_skin

        skin_dir = os.path.join(skins_dir, chosen_skin)
        default_dir = os.path.join(skins_dir, "default")

        # 回退順序：目前皮膚資料夾 -> skins/default -> assets 根目錄本身
        fallback_dirs = []
        for folder in (skin_dir, default_dir, assets_dir):
            if folder and os.path.isdir(folder) and folder not in fallback_dirs:
                fallback_dirs.append(folder)
                
        def _load_seq_with_fallback(pattern_regex):
            for folder in fallback_dirs:
                seq = PetAnimationManager._load_numbered_sequence(folder, pattern_regex)
                if seq:
                    return seq
            return []

        def _load_pm_with_fallback(filename):
            for folder in fallback_dirs:
                path = os.path.join(folder, filename)
                if os.path.exists(path):
                    pm = QPixmap(path)
                    if not pm.isNull():
                        return pm
            return QPixmap()

        # 1. 動態載入走路動畫 (1.png, 2.png, ..., N.png)
        walk_pattern = re.compile(r"^(\d+)\.[^.]+$", re.IGNORECASE)
        pet.frames = _load_seq_with_fallback(walk_pattern)

        # 2. 載入單張狀態圖與多張發呆序列 (idle_1.png, idle_2.png, ...)
        pet.drag_pixmap = _load_pm_with_fallback("pet_drag.png")
        pet.idle_pixmap = _load_pm_with_fallback("pet_idle.png")
        idle_pattern = re.compile(r"^idle_(\d+)\.[^.]+$", re.IGNORECASE)
        pet.idle_frames = _load_seq_with_fallback(idle_pattern)
        pet.current_idle_frame = 0

        pet.work_start_pixmap = _load_pm_with_fallback("work_start.png")

        # 3. 載入通用打工循環動畫 (work_1.png, work_2.png, ...)
        default_work_pattern = re.compile(r"^work_(\d+)\.[^.]+$", re.IGNORECASE)
        pet.work_loop_frames = _load_seq_with_fallback(default_work_pattern)

        # 4. 分別載入 3 種工作的專屬動畫 (work1_1.png, work2_1.png, work3_1.png ...)
        pet.job_loop_frames = {}
        pet.job_start_pixmaps = {}
        for job_key in PetAnimationManager.JOB_KEYS:
            job_pattern = re.compile(rf"^{job_key}_(\d+)\.[^.]+$", re.IGNORECASE)
            pet.job_loop_frames[job_key] = _load_seq_with_fallback(job_pattern)
            pet.job_start_pixmaps[job_key] = _load_pm_with_fallback(f"{job_key}_start.png")

        # 5. 工作三（work3）專屬：人物圖 + 旋轉背景圖
        pet.work3_person_pixmap = _load_pm_with_fallback("work3_person.png")
        pet.work3_bg_pixmap = _load_pm_with_fallback("work3_bg.png")
        pet.work3_bg_angle = 0

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
    def _has_work3_rotating_assets(pet):
        return not getattr(pet, "work3_person_pixmap", QPixmap()).isNull() or not getattr(
            pet, "work3_bg_pixmap", QPixmap()
        ).isNull()

    @staticmethod
    def _get_active_work_assets(pet):
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

        idle_frames = getattr(pet, "idle_frames", [])

        if pet.is_reporting_work:
            _, active_start = PetAnimationManager._get_active_work_assets(pet)
            pixmap = active_start if not active_start.isNull() else pet.frames[0]
        elif pet.is_working:
            if (
                getattr(pet, "current_job_type", "") == "work3"
                and PetAnimationManager._has_work3_rotating_assets(pet)
            ):
                angle = getattr(pet, "work3_bg_angle", 0)
                composed = PetAnimationManager._compose_rotating_scene(
                    getattr(pet, "work3_person_pixmap", QPixmap()),
                    getattr(pet, "work3_bg_pixmap", QPixmap()),
                    angle,
                )
                pixmap = composed if not composed.isNull() else pet.frames[0]
            else:
                active_loops, active_start = PetAnimationManager._get_active_work_assets(pet)
                if active_loops:
                    idx = pet.current_work_loop_frame % len(active_loops)
                    pixmap = active_loops[idx]
                else:
                    pixmap = active_start if not active_start.isNull() else pet.frames[0]
        elif pet.dragging:
            pixmap = pet.drag_pixmap if not pet.drag_pixmap.isNull() else pet.frames[0]
        elif not pet.is_walking:
            if idle_frames:
                idx = getattr(pet, "current_idle_frame", 0) % len(idle_frames)
                pixmap = idle_frames[idx]
            elif not pet.idle_pixmap.isNull():
                pixmap = pet.idle_pixmap
            else:
                pixmap = pet.frames[0]
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
            if (
                getattr(pet, "current_job_type", "") == "work3"
                and PetAnimationManager._has_work3_rotating_assets(pet)
            ):
                pet.work3_bg_angle = (
                    getattr(pet, "work3_bg_angle", 0) + PetAnimationManager.WORK3_BG_ROTATE_STEP
                ) % 360
                PetAnimationManager.update_image(pet)
                return

            active_loops, _ = PetAnimationManager._get_active_work_assets(pet)
            if active_loops:
                pet.current_work_loop_frame = (pet.current_work_loop_frame + 1) % len(active_loops)
                PetAnimationManager.update_image(pet)
            return

        if pet.is_reporting_work:
            return

        if pet.dragging:
            return

        if not pet.is_walking:
            idle_frames = getattr(pet, "idle_frames", [])
            if len(idle_frames) > 1:
                pet.current_idle_frame = (getattr(pet, "current_idle_frame", 0) + 1) % len(idle_frames)
                PetAnimationManager.update_image(pet)
            return

        pet.current_frame = (pet.current_frame + 1) % len(pet.frames)
        PetAnimationManager.update_image(pet)