import os
import sys


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def get_app_dir() -> str:
    """可寫入的應用程式根目錄（存檔、使用者新增的皮膚放在這裡）"""
    if is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def get_bundle_dir() -> str:
    """唯讀資源目錄（打包時指向 _MEIPASS 或執行檔所在目錄）"""
    if is_frozen():
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def get_assets_dir() -> str:
    """優先使用執行檔旁的 assets（方便新增皮膚），找不到再用打包內建的 assets"""
    external_assets = os.path.join(get_app_dir(), "assets")
    if os.path.isdir(external_assets):
        return external_assets
    return os.path.join(get_bundle_dir(), "assets")


def get_save_path(filename: str = "pet_save.json") -> str:
    """存檔一律放在可寫入的應用程式目錄"""
    return os.path.join(get_app_dir(), filename)