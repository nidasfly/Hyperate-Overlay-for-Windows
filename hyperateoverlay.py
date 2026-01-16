# ----------------------------------------------------------------- #
# HypeRate Overlay for Windows                                      #
# This Python Script is 100% created by Gemini                      #
# Github: https://github.com/nidasfly/Hyperate-Overlay-for-Windows  #
# 官网 (HyperRateOverlay Web): https://clipshar.ing/hyperateoverlay  #
# ----------------------------------------------------------------- #

import tkinter as tk
from tkinter import simpledialog, messagebox
import threading
import time
import json
import re
import os
import sys    # 用于获取exe路径
import logging
import winreg # 用于开机自启
import ctypes
from ctypes import windll # 显式导入 windll
from PIL import Image, ImageDraw, ImageFont, ImageTk
import pystray

# ================= 全局配置 =================
APP_NAME = "HypeRateOverlay"
DEFAULT_WIDTH = 220
DEFAULT_HEIGHT = 100
FONT_SIZE = 40
FONT_COLOR = "#FF0000"
BG_COLOR = "black"

# 屏蔽 Selenium 日志
logging.getLogger('selenium').setLevel(logging.WARNING)

class HeartRateApp:
    def __init__(self):
        self.root = tk.Tk()
        self.config_path = self.get_config_path()
        self.config = self.load_config()
        
        # 设置全局图标 (爱心)
        self.set_app_icon() 
        
        # 首次运行询问 ID
        if not self.config.get("short_id"):
            self.ask_for_id()

        if not self.config.get("short_id"):
            self.root.destroy()
            return

        self.current_hr = "--"
        self.running = True
        self.ws_url = None
        
        # 【修改点 1】从配置加载穿透状态，如果没有则默认为 False
        self.click_through = self.config.get("click_through", False)
        
        self.tray_icon = None

        self.setup_window()
        self.setup_ui()
        self.setup_drag()
        
        # 启动托盘 (独立线程)
        self.tray_thread = threading.Thread(target=self.init_tray_icon, daemon=True)
        self.tray_thread.start()

        # 启动核心逻辑
        self.logic_thread = threading.Thread(target=self.main_logic, daemon=True)
        self.logic_thread.start()

        # 启动置顶看门狗
        self.keep_topmost()

    def keep_topmost(self):
        """
        [FSO 增强版] 对抗全屏游戏的层级压制
        原理：通过 BringWindowToTop 唤醒 + SetWindowPos 强行置顶
        """
        if self.running:
            try:
                hwnd = windll.user32.GetParent(self.root.winfo_id())
                if hwnd == 0: hwnd = self.root.winfo_id()
                
                # 1. 尝试唤醒窗口到前台 (不激活)
                windll.user32.BringWindowToTop(hwnd)
                
                # 2. 强行置顶
                # HWND_TOPMOST(-1), NOSIZE|NOMOVE|NOACTIVATE|SHOWWINDOW
                windll.user32.SetWindowPos(
                    hwnd, -1, 0, 0, 0, 0, 
                    0x0001 | 0x0002 | 0x0010 | 0x0040
                )
            except Exception: pass
            # 200ms 频率
            self.root.after(200, self.keep_topmost)

    def get_config_path(self):
        user_dir = os.path.expanduser("~")
        app_dir = os.path.join(user_dir, APP_NAME)
        if not os.path.exists(app_dir): os.makedirs(app_dir)
        return os.path.join(app_dir, "config.json")

    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f: return json.load(f)
            except: pass
        # 【修改点 2】默认增加 click_through 字段
        return {"short_id": "", "x": None, "y": None, "click_through": False}

    def save_config(self):
        try:
            x = self.root.winfo_x()
            y = self.root.winfo_y()
            # 【修改点 3】保存时写入当前 click_through 状态
            data = {
                "short_id": self.config.get("short_id"), 
                "x": x, 
                "y": y,
                "click_through": self.click_through
            }
            with open(self.config_path, "w") as f: json.dump(data, f)
        except: pass

    def ask_for_id(self):
        self.root.withdraw()
        user_input = simpledialog.askstring("Setting / 设置", "请输入 HypeRate ID (例如: 2A01):", parent=self.root)
        if user_input: self.config["short_id"] = user_input.strip()
        self.root.deiconify()

    def set_app_icon(self):
        try:
            icon_image = self.create_tray_image()
            self.tk_icon = ImageTk.PhotoImage(icon_image)
            self.root.iconphoto(True, self.tk_icon)
        except Exception: pass

    def setup_window(self):
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-transparentcolor", BG_COLOR)
        self.root.configure(bg=BG_COLOR)

        last_x = self.config.get("x")
        last_y = self.config.get("y")
        if last_x is not None and last_y is not None:
            self.root.geometry(f"{DEFAULT_WIDTH}x{DEFAULT_HEIGHT}+{last_x}+{last_y}")
        else:
            sh = self.root.winfo_screenheight()
            self.root.geometry(f"{DEFAULT_WIDTH}x{DEFAULT_HEIGHT}+50+{sh - DEFAULT_HEIGHT - 100}")
        
        # 任务栏隐身初始化
        self.root.update_idletasks()
        hwnd = windll.user32.GetParent(self.root.winfo_id())
        if hwnd == 0: hwnd = self.root.winfo_id()
        
        GWL_EXSTYLE = -20
        WS_EX_TOOLWINDOW = 0x00000080
        WS_EX_APPWINDOW = 0x00040000
        WS_EX_LAYERED = 0x80000
        WS_EX_TRANSPARENT = 0x20

        # 获取当前样式
        style = windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        
        # 基础操作：移除APPWINDOW，添加TOOLWINDOW (隐藏任务栏)
        style = (style & ~WS_EX_APPWINDOW) | WS_EX_TOOLWINDOW
        
        # 【修改点 4】如果在配置中开启了穿透，初始化时直接应用穿透样式
        if self.click_through:
            style = style | WS_EX_LAYERED | WS_EX_TRANSPARENT
            self.root.wm_attributes("-alpha", 0.7) # 视觉提示：变透明
        
        windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)

    def setup_ui(self):
        self.label = tk.Label(self.root, text="Waiting...", font=("Segoe UI", 20, "bold"), fg="white", bg=BG_COLOR)
        self.label.pack(expand=True)

    def setup_drag(self):
        self.root.bind("<Button-1>", self.start_move)
        self.root.bind("<B1-Motion>", self.do_move)
        self.root.bind("<ButtonRelease-1>", lambda e: self.save_config())

    def start_move(self, event):
        self.x, self.y = event.x, event.y

    def do_move(self, event):
        x = self.root.winfo_x() + (event.x - self.x)
        y = self.root.winfo_y() + (event.y - self.y)
        self.root.geometry(f"+{x}+{y}")

    # --- 托盘 & 绘图 ---
    def create_tray_image(self):
        img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        dc = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("seguiemj.ttf", 48)
            pos = (5, 12) 
        except IOError:
            font = None
            pos = (16, 8)
        dc.text(pos, "❤", fill="#FF0000", font=font)
        return img

    def init_tray_icon(self):
        menu = pystray.Menu(
            pystray.MenuItem("官网 (HyperateOverlay Web)", lambda icon, item: os.startfile("https://clipshar.ing/hyperateoverlay")),
            pystray.MenuItem("GitHub", lambda icon, item: os.startfile("https://github.com/nidasfly/Hyperate-Overlay-for-Windows")),
            # 穿透开关 (带 √)
            pystray.MenuItem("锁定穿透 (Click-through)", self.toggle_click_through_action, checked=lambda i: self.click_through),
            # 开机自启开关 (带 √)
            pystray.MenuItem("开机自启 (Start at Login)", self.toggle_startup_action, checked=lambda i: self.is_startup_enabled()),
            pystray.MenuItem("重置 ID", self.reset_id_action),
            pystray.MenuItem("退出 (Exit)", self.on_close)
        )
        self.tray_icon = pystray.Icon("HypeRateOverlay", self.create_tray_image(), "HypeRate Overlay", menu)
        self.tray_icon.run()

    # --- 穿透逻辑 ---
    def toggle_click_through_action(self, icon, item):
        self.click_through = not self.click_through
        
        hwnd = windll.user32.GetParent(self.root.winfo_id())
        if hwnd == 0: hwnd = self.root.winfo_id()
        
        GWL_EXSTYLE = -20
        WS_EX_LAYERED = 0x80000
        WS_EX_TRANSPARENT = 0x20
        WS_EX_TOOLWINDOW = 0x00000080 # 保持隐藏任务栏
        
        old_style = windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        
        if self.click_through:
            # 开启穿透 + 保持 ToolWindow
            new_style = old_style | WS_EX_TRANSPARENT | WS_EX_LAYERED | WS_EX_TOOLWINDOW
            windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
            # 在主线程更新 UI 透明度
            self.root.after(0, lambda: self.root.wm_attributes("-alpha", 0.7)) 
            print("穿透模式：开启")
        else:
            # 关闭穿透 + 保持 ToolWindow
            new_style = (old_style & ~WS_EX_TRANSPARENT) | WS_EX_TOOLWINDOW
            windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
            self.root.after(0, lambda: self.root.wm_attributes("-alpha", 1.0))
            print("穿透模式：关闭")
            
        # 【修改点 5】切换状态后立即保存到配置文件
        self.save_config()

    # --- 开机自启逻辑 ---
    def get_exe_path(self):
        # 获取当前运行的 exe 完整路径
        if getattr(sys, 'frozen', False):
            return sys.executable
        else:
            return os.path.abspath(sys.argv[0])

    def is_startup_enabled(self):
        """检查注册表是否已开启自启"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            val, _ = winreg.QueryValueEx(key, APP_NAME)
            winreg.CloseKey(key)
            return val == self.get_exe_path()
        except: return False

    def toggle_startup_action(self, icon, item):
        """切换开机自启"""
        path = self.get_exe_path()
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
            if self.is_startup_enabled():
                winreg.DeleteValue(key, APP_NAME)
                print("自启已关闭")
            else:
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, path)
                print("自启已开启")
            winreg.CloseKey(key)
        except Exception as e: 
            print(f"注册表错误: {e}")
            messagebox.showerror("Error", str(e))

    def reset_id_action(self, icon, item):
        self.config["short_id"] = ""
        self.save_config()
        self.root.after(0, lambda: messagebox.showinfo("Reset ID", "ID has been reset. Please restart.\nID 已重设，请重启程序。"))
        self.root.after(100, self.on_close)

    def on_close(self, icon=None, item=None):
        self.running = False
        self.save_config()
        if self.tray_icon: self.tray_icon.stop()
        self.root.quit()
        os._exit(0)

    # --- 网络 ---
    def get_token_automatically(self):
        """
        自动获取 Token (支持 Chrome 和 Edge 双内核)
        """
        from selenium import webdriver
        # Chrome 依赖
        from selenium.webdriver.chrome.service import Service as ChromeService
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        from webdriver_manager.chrome import ChromeDriverManager
        # Edge 依赖
        from selenium.webdriver.edge.service import Service as EdgeService
        from selenium.webdriver.edge.options import Options as EdgeOptions
        from webdriver_manager.microsoft import EdgeChromiumDriverManager

        self.root.after(0, lambda: self.label.config(text="Linking..."))
        
        driver = None
        found_url = None
        current_id = self.config.get("short_id")

        # --- 内部函数：尝试启动浏览器 ---
        def try_browser(browser_type):
            nonlocal driver
            try:
                if browser_type == "chrome":
                    options = ChromeOptions()
                    # 关键配置
                    options.add_argument('--headless=new') 
                    options.add_argument('--disable-gpu')
                    options.add_argument('--ignore-certificate-errors')
                    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
                    
                    service = ChromeService(ChromeDriverManager().install())
                    driver = webdriver.Chrome(service=service, options=options)
                    print(">>> 使用 Chrome 浏览器")
                    
                elif browser_type == "edge":
                    options = EdgeOptions()
                    options.add_argument('--headless=new')
                    options.add_argument('--disable-gpu')
                    options.add_argument('--ignore-certificate-errors')
                    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
                    
                    service = EdgeService(EdgeChromiumDriverManager().install())
                    driver = webdriver.Edge(service=service, options=options)
                    print(">>> 使用 Edge 浏览器 (Chrome 未找到)")
                
                return True
            except Exception as e:
                print(f"{browser_type} 启动失败: {e}")
                return False

        # --- 1. 优先尝试 Chrome ---
        if not try_browser("chrome"):
            # --- 2. 如果失败，尝试 Edge ---
            if not try_browser("edge"):
                print("❌ 所有浏览器均启动失败")
                self.root.after(0, lambda: self.label.config(text="Browser Chrome/Edge Not Found", font=("Segoe UI", 20)))
                return None

        # --- 3. 统一的抓包逻辑 (Chrome 和 Edge 通用) ---
        try:
            # 开启网络监听
            driver.execute_cdp_cmd('Network.enable', {})
            
            # 访问网页
            target_url = f"https://app.hyperate.io/{current_id}"
            driver.get(target_url)
            
            pat = re.compile(r'(wss://app\.hyperate\.io/socket/websocket\?token=[a-zA-Z0-9_\-]+)')
            start_time = time.time()
            
            while time.time() - start_time < 30:
                logs = str(driver.get_log('performance'))
                match = pat.search(logs)
                if match:
                    found_url = match.group(1)
                    if "vsn=2.0.0" not in found_url: 
                        found_url += "&vsn=2.0.0"
                    break
                time.sleep(0.5)
        except Exception as e:
            print(f"抓包过程出错: {e}")
        finally:
            if driver: 
                try: driver.quit()
                except: pass
                
        return found_url

    def connect_websocket(self, url):
        import websocket
        self.root.after(0, lambda: self.label.config(text=f"♥ --", font=("Segoe UI", FONT_SIZE, "bold"), fg=FONT_COLOR))
        def on_msg(ws, msg):
            if not self.running: ws.close(); return
            try:
                d = json.loads(msg)
                if d.get("event") == "hr_update":
                    self.current_hr = str(d["payload"]["hr"])
                    self.root.after(0, lambda: self.label.config(text=f"♥ {self.current_hr}"))
            except: pass
        def on_open(ws):
            ws.send(json.dumps({"topic":f"hr:{self.config.get('short_id')}","event":"phx_join","payload":{},"ref":"1"}))
            def keep():
                while self.running and ws.sock and ws.sock.connected:
                    time.sleep(20)
                    try: ws.send(json.dumps({"topic":"phoenix","event":"heartbeat","payload":{},"ref":"1"}))
                    except: break
            threading.Thread(target=keep, daemon=True).start()
        ws = websocket.WebSocketApp(url, on_message=on_msg, on_open=on_open, header={"User-Agent": "Mozilla/5.0"})
        ws.run_forever()

    def main_logic(self):
        url = self.get_token_automatically()
        if url: self.connect_websocket(url)
        else: self.root.after(0, lambda: self.label.config(text="Retry", font=("Segoe UI", 20)))

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = HeartRateApp()
    app.run()