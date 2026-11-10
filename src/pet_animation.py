import os
from PyQt5.QtGui import QPixmap, QTransform
from PyQt5.QtCore import Qt

class PetAnimationManager:
    @staticmethod
    def init_animations(pet, root_dir):
        # 👈 指定圖片統一放在根目錄底下的 assets 資料夾內
        assets_dir = os.path.join(root_dir, 'assets')
        
        pet.frame_files = ['1.png', '2.png', '3.png', '4.png', '5.png', '6.png', '7.png', '8.png']
        pet.frames = []
        
        for file in pet.frame_files:
            file_path = os.path.join(assets_dir, file)
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                pet.frames.append(pixmap)
        
        drag_path = os.path.join(assets_dir, 'pet_drag.png')
        pet.drag_pixmap = QPixmap(drag_path)

        idle_path = os.path.join(assets_dir, 'pet_idle.png')
        pet.idle_pixmap = QPixmap(idle_path)

        work_start_path = os.path.join(assets_dir, 'work_start.png')
        pet.work_start_pixmap = QPixmap(work_start_path)

        pet.work_loop_files = ['work_1.png', 'work_2.png', 'work_3.png']
        pet.work_loop_frames = []
        for file in pet.work_loop_files:
            file_path = os.path.join(assets_dir, file)
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                pet.work_loop_frames.append(pixmap)

        if not pet.frames:
            pet.label.setText("🐾 找不到圖片")
            pet.label.setStyleSheet(
                "color: white; background-color: rgba(0, 0, 0, 160); "
                "font-size: 14px; border-radius: 8px; padding: 10px;"
            )
            pet.resize(200, 60)
            return False

        pet.current_frame = 0
        pet.current_work_loop_frame = 0
        return True

    @staticmethod
    def update_image(pet):
        if not pet.frames:
            return

        if pet.is_reporting_work:
            pixmap = pet.work_start_pixmap if not pet.work_start_pixmap.isNull() else pet.frames[0]
        elif pet.is_working:
            if pet.work_loop_frames:
                pixmap = pet.work_loop_frames[pet.current_work_loop_frame]
            else:
                pixmap = pet.work_start_pixmap if not pet.work_start_pixmap.isNull() else pet.frames[0]
        elif pet.dragging:
            pixmap = pet.drag_pixmap if not pet.drag_pixmap.isNull() else pet.frames[0]
        elif not pet.is_walking and not pet.idle_pixmap.isNull():
            pixmap = pet.idle_pixmap
        else:
            pixmap = pet.frames[pet.current_frame]

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