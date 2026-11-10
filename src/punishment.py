import os
import psutil

try:
    import win32gui
    import win32process
    import win32con
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

class PunishmentManager:
    @staticmethod
    def close_all_other_windows(pet_widget, bubble_widget):
        if not HAS_WIN32:
            print("未安裝 pywin32，無法執行關閉視窗功能")
            return

        current_hwnd = int(pet_widget.winId())  # 桌寵主視窗句柄
        bubble_hwnd = int(bubble_widget.winId()) if bubble_widget else 0  # 對話框句柄
        current_pid = os.getpid()  # 當前桌寵程式自身的 PID
        target_hwnds = []

        def enum_windows_callback(hwnd, extra):
            nonlocal target_hwnds
            if win32gui.IsWindowVisible(hwnd):
                if hwnd == current_hwnd or hwnd == bubble_hwnd:
                    return
                
                window_title = win32gui.GetWindowText(hwnd)
                if not window_title or len(window_title.strip()) == 0:
                    return
                
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                
                if pid == current_pid:
                    return

                try:
                    p = psutil.Process(pid)
                    p_name = p.name().lower()
                    
                    blacklisted_processes = [
                        "explorer.exe", "dwm.exe", "taskhostw.exe", 
                        "python.exe", "code.exe", 
                        "powershell.exe", "cmd.exe", "windowsterminal.exe", "wt.exe"
                    ]
                    if p_name in blacklisted_processes:
                        return
                except:
                    return

                target_hwnds.append(hwnd)

        try:
            win32gui.EnumWindows(enum_windows_callback, None)
            for hwnd in target_hwnds:
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            print(f"已成功關閉所有其他視窗（共 {len(target_hwnds)} 個）！")
        except Exception as e:
            print(f"執行視窗懲罰失敗: {e}")