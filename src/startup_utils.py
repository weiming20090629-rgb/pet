import os
import sys
from pathlib import Path
import subprocess


SHORTCUT_NAME = "DesktopPet.lnk"


def get_startup_dir() -> Path:
    appdata = os.getenv("APPDATA")
    if appdata:
        return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    return Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def get_shortcut_path() -> Path:
    return get_startup_dir() / SHORTCUT_NAME


def get_launch_target() -> tuple[str, str, str]:
    """回傳 (target_path, arguments, working_dir)"""
    if getattr(sys, "frozen", False):
        exe_path = Path(sys.executable).resolve()
        return str(exe_path), "", str(exe_path.parent)
    else:
        main_py = Path(__file__).resolve().parent.parent / "main.py"
        python_exe = Path(sys.executable).resolve()
        # 若使用 pythonw.exe 可避免跳黑框；若只有 python.exe 也能正常啟動
        pythonw_exe = python_exe.with_name("pythonw.exe")
        runner = str(pythonw_exe if pythonw_exe.exists() else python_exe)
        return runner, f'"{main_py}"', str(main_py.parent)


def is_autostart_enabled() -> bool:
    return get_shortcut_path().exists()


def set_autostart(enabled: bool) -> tuple[bool, str]:
    if sys.platform != "win32":
        return False, "目前僅支援 Windows 開機自動啟動"

    shortcut_path = get_shortcut_path()
    try:
        if enabled:
            shortcut_path.parent.mkdir(parents=True, exist_ok=True)
            target, args, work_dir = get_launch_target()

            # 跳脫單引號以安全傳入 PowerShell
            t_esc = target.replace("'", "''")
            a_esc = args.replace("'", "''")
            w_esc = work_dir.replace("'", "''")
            s_esc = str(shortcut_path).replace("'", "''")

            ps_script = (
                "$ws = New-Object -ComObject WScript.Shell; "
                f"$sc = $ws.CreateShortcut('{s_esc}'); "
                f"$sc.TargetPath = '{t_esc}'; "
                f"$sc.Arguments = '{a_esc}'; "
                f"$sc.WorkingDirectory = '{w_esc}'; "
                "$sc.Save()"
            )
            subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
                check=True,
                capture_output=True,
                text=True,
            )
            return True, "已開啟開機自動啟動"
        else:
            if shortcut_path.exists():
                shortcut_path.unlink()
            return True, "已關閉開機自動啟動"
    except Exception as e:
        return False, f"設定失敗：{e}"

INIT_FLAG_NAME = ".autostart_initialized"


def ensure_autostart_on_first_run() -> tuple[bool, str]:
    """僅在打包後的 .exe 首次啟動時自動加入開機啟動，之後尊重使用者手動變更。"""
    if sys.platform != "win32" or not getattr(sys, "frozen", False):
        return False, "非 Windows 打包版，略過自動加入"

    exe_dir = Path(sys.executable).resolve().parent
    flag_path = exe_dir / INIT_FLAG_NAME

    if flag_path.exists():
        return False, "已完成首次開機啟動初始化"

    ok, msg = set_autostart(True)
    try:
        flag_path.write_text("1", encoding="utf-8")
    except Exception:
        pass
    return ok, msg