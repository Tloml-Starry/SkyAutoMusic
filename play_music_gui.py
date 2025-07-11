import os
import json
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import pyautogui
import keyboard
from collections import defaultdict
import win32gui
import win32process
import win32con
import psutil
import sys
import ctypes
import webbrowser

# 资源路径适配函数，兼容PyInstaller打包和开发环境
def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

# 配置
SHEET_MUSIC_DIR = resource_path('Sheet Music')
if not os.path.exists(SHEET_MUSIC_DIR):
    os.makedirs(SHEET_MUSIC_DIR)
note_to_key = {
    "1Key0": "Y", "1Key1": "U", "1Key2": "I", "1Key3": "O", "1Key4": "P",
    "1Key5": "H", "1Key6": "J", "1Key7": "K", "1Key8": "L", "1Key9": ";",
    "1Key10": "N", "1Key11": "M", "1Key12": ",", "1Key13": ".", "1Key14": "/",
    "2Key0": "Y", "2Key1": "U", "2Key2": "I", "2Key3": "O", "2Key4": "P",
    "2Key5": "H", "2Key6": "J", "2Key7": "K", "2Key8": "L", "2Key9": ";",
    "2Key10": "N", "2Key11": "M", "2Key12": ",", "2Key13": ".", "2Key14": "/"
}

CONFIG_FILE = resource_path('config.json')

def is_dark_mode():
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize')
        value, _ = winreg.QueryValueEx(key, 'AppsUseLightTheme')
        return value == 0
    except Exception:
        return False

class AutoPlayer:
    def __init__(self, notes_by_time, sorted_times):
        self.notes_by_time = notes_by_time
        self.sorted_times = sorted_times
        self._stop = threading.Event()
        self._pause = threading.Event()
        self._pause.set()  # 初始为未暂停
        self.current_idx = 0
        self.is_playing = False

    def play(self, update_status):
        self.is_playing = True
        self._stop.clear()
        self._pause.set()
        for idx in range(self.current_idx, len(self.sorted_times)):
            if self._stop.is_set():
                break
            while not self._pause.is_set():
                time.sleep(0.1)
            t = self.sorted_times[idx]
            keys = self.notes_by_time[t]
            for k in keys:
                key = note_to_key.get(k)
                if key:
                    pyautogui.keyDown(key)
            time.sleep(0.05)
            for k in keys:
                key = note_to_key.get(k)
                if key:
                    pyautogui.keyUp(key)
            update_status(f"演奏进度: {idx+1}/{len(self.sorted_times)}")
            if idx < len(self.sorted_times) - 1:
                interval = (self.sorted_times[idx + 1] - t) / 1000.0
                if interval > 0:
                    time.sleep(interval)
            self.current_idx = idx + 1
        self.is_playing = False
        update_status("演奏结束！")

    def stop(self):
        self._stop.set()
        self.is_playing = False
        self.current_idx = 0

    def pause(self):
        self._pause.clear()

    def resume(self):
        self._pause.set()

class MusicGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SkyAutoMusic 自动弹琴")
        # 读取窗口配置
        win_w, win_h = 600, 480
        x, y = None, None
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                win_w = cfg.get('width', win_w)
                win_h = cfg.get('height', win_h)
                x = cfg.get('x')
                y = cfg.get('y')
            except Exception:
                pass
        if x is not None and y is not None:
            self.root.geometry(f"{win_w}x{win_h}+{x}+{y}")
        else:
            screen_w = self.root.winfo_screenwidth()
            screen_h = self.root.winfo_screenheight()
            x = (screen_w - win_w) // 2
            y = (screen_h - win_h) // 2
            self.root.geometry(f"{win_w}x{win_h}+{x}+{y}")
        self.root.resizable(True, True)
        self.root.minsize(480, 360)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        # 统一浅色风格
        self.bg_color = "#F7F9FB"
        self.fg_color = "#222"
        self.accent = "#4F8CFF"
        self.frame_bg = "#FFFFFF"
        self.entry_bg = "#F8F8F8"
        self.entry_fg = "#222"
        self.button_bg = "#4F8CFF"
        self.button_fg = "#FFFFFF"
        self.button_active_bg = "#3399FF"
        self.root.configure(bg=self.bg_color)
        self.set_style()
        self.default_hotkeys = {'start': 'F5', 'stop': 'F7'}
        self.hotkeys = self.default_hotkeys.copy()
        self.hotkey_vars = {k: tk.StringVar(value=v) for k, v in self.hotkeys.items()}
        self.status_var = tk.StringVar(value="请选择乐谱并点击开始演奏")
        self.elapsed_time_var = tk.StringVar(value="0:00")
        self.total_time_var = tk.StringVar(value="0:00")
        self.music_info_vars = {
            'filename': tk.StringVar(),
            'path': tk.StringVar(),
            'name': tk.StringVar(),
            'author': tk.StringVar(),
            'transcribedBy': tk.StringVar(),
        }
        self.filtered_music_files = []  # 先初始化，防止后续方法引用时报错
        self.favorites = set()  # 收藏的乐谱文件名集合，可持久化
        self.favorite_file = resource_path('favorites.json')  # 用resource_path，兼容打包
        self.load_favorites()  # 启动时加载收藏
        self.create_widgets()
        # 关键：初始化后立即加载乐谱列表并刷新
        self.all_music_files = self.get_all_music_files() or []
        self.filtered_music_files = self.all_music_files.copy()
        self.refresh_music_listbox()
        self.player = None
        self.music_data = None
        self.notes_by_time = None
        self.sorted_times = None
        self.play_thread = None
        self.last_music_files = set(self.all_music_files or [])
        self.schedule_music_dir_watch()

    def set_style(self):
        style = ttk.Style()
        if sys.platform == "win32":
            try:
                style.theme_use('vista')
            except Exception:
                style.theme_use('clam')
        else:
            style.theme_use('clam')
        style.configure('.', font=('微软雅黑', 10))
        style.configure('TFrame', background=self.bg_color)
        style.configure('TLabelframe', background=self.bg_color, foreground=self.fg_color, borderwidth=0)
        style.configure('TLabelframe.Label', background=self.bg_color, foreground=self.accent, font=('微软雅黑', 9, 'bold'))
        style.configure('TLabel', background=self.bg_color, foreground=self.fg_color)
        style.configure('TButton', background=self.button_bg, foreground='#222', borderwidth=0, relief='flat', padding=4, font=('微软雅黑', 9, 'bold'))
        style.map('TButton', background=[('active', self.button_active_bg)], foreground=[('active', '#222')])
        style.configure('Accent.TButton', background=self.accent, foreground='#222', borderwidth=0, relief='flat', padding=4, font=('微软雅黑', 9, 'bold'))
        style.map('Accent.TButton', background=[('active', self.button_active_bg)], foreground=[('active', '#222')])
        style.configure('TEntry', fieldbackground=self.entry_bg, background=self.entry_bg, foreground=self.entry_fg, borderwidth=1, relief='flat')
        style.configure('TCombobox', fieldbackground=self.entry_bg, background=self.entry_bg, foreground=self.entry_fg, borderwidth=1, relief='flat')
        style.map('TCombobox', fieldbackground=[('readonly', self.entry_bg)], background=[('readonly', self.entry_bg)], foreground=[('readonly', self.entry_fg)])
        # 现代美观进度条样式
        style.layout('Modern.Horizontal.TProgressbar', [
            ('Horizontal.Progressbar.trough', {'children': [
                ('Horizontal.Progressbar.pbar', {'side': 'left', 'sticky': 'ns'})
            ], 'sticky': 'nswe'})
        ])
        style.configure('Modern.Horizontal.TProgressbar',
            troughcolor='#E6EAF0',
            background=self.accent,
            thickness=18,
            borderwidth=0,
            relief='flat',
            lightcolor='#A7C7FF',
            darkcolor='#4F8CFF',
            bordercolor='#E6EAF0',
            padding=2
        )
        # 渐变色和圆角效果（部分平台支持）
        try:
            style.element_create('Rounded.pbar', 'from', 'clam')
            style.layout('Modern.Horizontal.TProgressbar', [
                ('Horizontal.Progressbar.trough', {'children': [
                    ('Rounded.pbar', {'side': 'left', 'sticky': 'ns'})
                ], 'sticky': 'nswe'})
            ])
        except Exception:
            pass

    def create_widgets(self):
        # 主Notebook分页
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=0, pady=0)
        # 播放Tab
        play_tab = ttk.Frame(notebook)
        notebook.add(play_tab, text="播放")
        # 设置Tab
        settings_tab = ttk.Frame(notebook)
        notebook.add(settings_tab, text="说明")
        # 播放Tab内容（三栏布局）
        main_frame = ttk.Frame(play_tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        main_frame.columnconfigure(0, weight=0, minsize=220)
        main_frame.columnconfigure(1, weight=1, minsize=320)
        main_frame.columnconfigure(2, weight=0, minsize=0)
        # ====== 右侧主控区 ======
        center_frame = ttk.Frame(main_frame, width=320)
        center_frame.grid(row=0, column=1, sticky="nswe", padx=10, pady=10)
        center_frame.grid_propagate(False)
        center_frame.config(width=320)

        # ====== 曲谱信息展示区（右侧，按钮组上方） ======
        # 歌名、作者、制谱人在上方大字号高亮，文件名在下方小字号
        self.music_info_frame = ttk.LabelFrame(center_frame, text="曲谱信息", padding=6)
        self.music_info_frame.pack(fill="x", pady=(0, 8), anchor="n")
        # 歌名
        ttk.Label(self.music_info_frame, text="歌名:", width=7, anchor="e").grid(row=0, column=0, sticky="e", pady=(0,2))
        ttk.Label(self.music_info_frame, textvariable=self.music_info_vars['name'], width=18, anchor="w", font=("微软雅黑", 12, "bold"), foreground=self.accent).grid(row=0, column=1, sticky="w", pady=(0,2))
        # 作者
        ttk.Label(self.music_info_frame, text="作者:", width=7, anchor="e").grid(row=1, column=0, sticky="e", pady=(0,2))
        ttk.Label(self.music_info_frame, textvariable=self.music_info_vars['author'], width=18, anchor="w", font=("微软雅黑", 12, "bold"), foreground=self.accent).grid(row=1, column=1, sticky="w", pady=(0,2))
        # 制谱人
        ttk.Label(self.music_info_frame, text="制谱:", width=7, anchor="e").grid(row=2, column=0, sticky="e", pady=(0,2))
        ttk.Label(self.music_info_frame, textvariable=self.music_info_vars['transcribedBy'], width=18, anchor="w", font=("微软雅黑", 12, "bold"), foreground=self.accent).grid(row=2, column=1, sticky="w", pady=(0,2))
        # 文件名
        ttk.Label(self.music_info_frame, text="文件名:", width=7, anchor="e").grid(row=3, column=0, sticky="e", pady=(6,0))
        ttk.Label(self.music_info_frame, textvariable=self.music_info_vars['filename'], width=18, anchor="w", font=("微软雅黑", 9), foreground="#888").grid(row=3, column=1, sticky="w", pady=(6,0))
        # ====== 左侧乐谱区 ======
        left_frame = ttk.Frame(main_frame, width=220)
        left_frame.grid(row=0, column=0, sticky="nswe", padx=(10, 0), pady=10)
        left_frame.grid_propagate(False)
        left_frame.config(width=220)

        # ====== 乐谱分页按钮（全部/收藏） ======
        # 可自定义：tab_names 可扩展更多分页
        self.music_tabs = ["全部曲谱", "收藏曲谱"]  # 可自定义：分页名称
        self.current_music_tab = tk.StringVar(value=self.music_tabs[0])
        tab_frame = ttk.Frame(left_frame)
        tab_frame.pack(fill="x", pady=(0, 4))
        for name in self.music_tabs:
            btn = ttk.Radiobutton(tab_frame, text=name, value=name, variable=self.current_music_tab,
                                  command=self.on_music_tab_changed, style="Toolbutton")
            btn.pack(side="left", padx=2)

        # ====== 搜索栏 ======
        ttk.Label(left_frame, text="搜索乐谱:", font=("微软雅黑", 10, "bold"), foreground=self.accent, width=12, anchor="w").pack(anchor="w", pady=(0, 2))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(left_frame, textvariable=self.search_var, font=("微软雅黑", 10), width=18)
        self.search_entry.pack(fill="x", padx=(0, 2), pady=(0, 6))
        self.search_entry.bind('<KeyRelease>', self.on_search)

        # ====== 乐谱列表区 ======
        # 可自定义：height 控制显示行数，width 控制显示宽度
        self.music_listbox = tk.Listbox(left_frame, width=22, height=22, font=("微软雅黑", 10), activestyle='dotbox', borderwidth=1, relief='solid')
        self.music_listbox.pack(fill="both", expand=True)
        self.music_listbox.bind('<<ListboxSelect>>', self.on_listbox_select)
        self.music_listbox.bind('<Button-3>', self.on_music_listbox_right_click)  # 右键菜单
        self.refresh_music_listbox()
        self.tooltip = None
        # 中间：歌曲信息三行+播放时长+主按钮组
        info_frame = ttk.Frame(center_frame, width=300)
        info_frame.pack(pady=(10, 8), fill="x")
        info_frame.pack_propagate(False)
        ttk.Label(info_frame, text="歌曲：", font=("微软雅黑", 10, "bold"), width=6, anchor="w").pack(anchor="w")
        ttk.Label(info_frame, textvariable=self.music_info_vars['name'], font=("微软雅黑", 10, "bold"), foreground=self.accent, width=20, anchor="w").pack(anchor="w", padx=(8, 0))
        ttk.Label(info_frame, text="作者：", font=("微软雅黑", 10, "bold"), width=6, anchor="w").pack(anchor="w", pady=(6, 0))
        ttk.Label(info_frame, textvariable=self.music_info_vars['author'], font=("微软雅黑", 10, "bold"), width=20, anchor="w").pack(anchor="w", padx=(8, 0))
        # 播放时长显示（紧凑居中）
        time_frame = ttk.Frame(center_frame, width=300)
        time_frame.pack(pady=(0, 8), fill="x")
        time_frame.pack_propagate(False)
        self.elapsed_time_var = tk.StringVar(value="0:00")
        self.total_time_var = tk.StringVar(value="0:00")
        time_inner = ttk.Frame(time_frame, width=180)
        time_inner.pack(anchor="center")
        time_inner.pack_propagate(False)
        ttk.Label(time_inner, textvariable=self.elapsed_time_var, font=("Consolas", 11, "bold"), foreground=self.accent, width=7, anchor="e").pack(side="left")
        ttk.Label(time_inner, text="/", font=("微软雅黑", 10, "bold"), foreground="#888", width=2, anchor="center").pack(side="left", padx=2)
        ttk.Label(time_inner, textvariable=self.total_time_var, font=("Consolas", 11, "bold"), foreground="#888", width=7, anchor="w").pack(side="left")
        # 操作按钮组
        btn_frame = ttk.Frame(center_frame, width=220)
        btn_frame.pack(pady=12)
        btn_frame.pack_propagate(False)
        self.start_btn = ttk.Button(btn_frame, text="开始演奏 (F5)", command=self.start_play, style='Accent.TButton', width=14)
        self.start_btn.grid(row=0, column=0, padx=10, pady=6)
        self.stop_btn = ttk.Button(btn_frame, text="停止 (F7)", command=self.stop_play, state="disabled", style='Accent.TButton', width=14)
        self.stop_btn.grid(row=0, column=1, padx=10, pady=6)
        # 状态栏
        self.status_label = ttk.Label(center_frame, textvariable=self.status_var, anchor="center", font=("微软雅黑", 10, "bold"), background=self.bg_color, foreground=self.accent, width=32)
        self.status_label.pack(pady=6, fill="x")
        # 设置Tab内容
        self.create_hotkey_settings(parent=settings_tab)

    def create_hotkey_settings(self, parent=None):
        frame = ttk.LabelFrame(parent or self.root, text="程序说明", padding=14)
        frame.pack(pady=10, fill="x", padx=8)
        # 作者超链接
        author_label = tk.Label(frame, text="作者: 傅卿何（点击访问主页）", fg="#3366cc", cursor="hand2", font=("微软雅黑", 10, "underline"))
        author_label.grid(row=0, column=0, sticky="w", padx=4, pady=4)
        author_label.bind("<Button-1>", lambda e: webbrowser.open("https://gitee.com/Tloml-Starry"))
        # 交流群超链接
        group_label = tk.Label(frame, text="交流群（点击加入）", fg="#3366cc", cursor="hand2", font=("微软雅黑", 10, "underline"))
        group_label.grid(row=1, column=0, sticky="w", padx=4, pady=4)
        group_label.bind("<Button-1>", lambda e: webbrowser.open("https://qm.qq.com/q/XVf2HjGJgK"))
        # 其它说明
        ttk.Label(frame, text="本程序完全免费，仅供学习交流，严禁商用.").grid(row=2, column=0, sticky="w", padx=4, pady=4)
        ttk.Label(frame, text="右键曲谱可以收藏曲谱，方便下次演奏.").grid(row=3, column=0, sticky="w", padx=4, pady=4)
        # 热键说明区
        frame = ttk.LabelFrame(parent or self.root, text="热键说明", padding=14)
        frame.pack(pady=10, fill="x", padx=8)
        ttk.Label(frame, text="开始/继续:").grid(row=0, column=0, sticky="e", padx=4, pady=4)
        ttk.Label(frame, textvariable=self.hotkey_vars['start'], font=("微软雅黑", 10, "bold"), foreground=self.accent).grid(row=0, column=1, sticky="w", padx=4, pady=4)
        ttk.Label(frame, text="停止:").grid(row=2, column=0, sticky="e", padx=4, pady=4)
        ttk.Label(frame, textvariable=self.hotkey_vars['stop'], font=("微软雅黑", 10, "bold"), foreground=self.accent).grid(row=2, column=1, sticky="w", padx=4, pady=4)

    def get_all_music_files(self):
        return [f for f in os.listdir(SHEET_MUSIC_DIR) if f.endswith('.json')]

    def refresh_music_listbox(self):
        # 根据当前tab显示全部或收藏
        tab = getattr(self, 'current_music_tab', None)
        if tab and getattr(self, 'music_tabs', None):
            if self.current_music_tab.get() == "收藏曲谱":
                files = [f for f in self.filtered_music_files if f in self.favorites]
            else:
                files = self.filtered_music_files or []
        else:
            files = self.filtered_music_files or []
        self.music_listbox.delete(0, tk.END)
        # 只显示文件名（带.json），不做display_name截断，保证索引一一对应
        for f in files:
            self.music_listbox.insert(tk.END, f)
        if files:
            self.music_listbox.selection_set(0)
            self.update_song_info(files[0])
        else:
            self.update_song_info(None)

    def on_search(self, event=None):
        keyword = self.search_var.get().lower()
        if not keyword:
            self.filtered_music_files = self.all_music_files.copy()
        else:
            self.filtered_music_files = [f for f in self.all_music_files if keyword in f.lower()]
        self.refresh_music_listbox()

    def on_listbox_select(self, event=None):
        sel = self.music_listbox.curselection()
        if sel:
            filename = self.filtered_music_files[sel[0]]
            self.update_song_info(filename)
            self.status_var.set(f"已选择乐谱: {filename}")

    def refresh_music_list(self):
        # 兼容旧接口，实际不再用
        self.all_music_files = self.get_all_music_files() or []
        self.filtered_music_files = self.all_music_files.copy() if self.all_music_files else []
        self.refresh_music_listbox()

    def update_song_info(self, filename):
        # 页面信息区展示选中曲谱详细信息
        import os
        import json
        if not filename:
            self.music_info_vars['filename'].set("")
            self.music_info_vars['name'].set("")
            self.music_info_vars['author'].set("")
            self.music_info_vars['transcribedBy'].set("")
            return
        self.music_info_vars['filename'].set(filename)
        path = os.path.join(SHEET_MUSIC_DIR, filename)  # SHEET_MUSIC_DIR已用resource_path
        encodings = ['utf-8', 'utf-8-sig', 'gbk', 'utf-16', 'utf-16-le', 'utf-16-be']
        data = None
        last_err = None
        for enc in encodings:
            try:
                with open(path, 'r', encoding=enc) as f:
                    data = json.load(f)
                break
            except Exception as e:
                last_err = e
                data = None
        if data is None:
            self.music_info_vars['name'].set('')
            self.music_info_vars['author'].set('')
            self.music_info_vars['transcribedBy'].set('')
            return
        meta = {}
        # 兼容多种结构
        if isinstance(data, dict):
            meta = data
        elif isinstance(data, list) and len(data) > 0:
            # 优先第一个元素
            if isinstance(data[0], dict):
                meta = data[0]
            else:
                for item in data:
                    if isinstance(item, dict) and ('songName' in item or 'name' in item):
                        meta = item
                        break
        # 兼容不同字段名
        name = meta.get('songName') or meta.get('name') or ''
        author = meta.get('author') or ''
        transcribed = meta.get('transcribedBy') or meta.get('transcriber') or ''
        self.music_info_vars['name'].set(name)
        self.music_info_vars['author'].set(author)
        self.music_info_vars['transcribedBy'].set(transcribed)

    def start_play(self):
        if not self.check_and_set_game_window():
            return
        if self.player and self.player.is_playing:
            return
        if not self.load_music():
            return
        self.player = AutoPlayer(self.notes_by_time, self.sorted_times)
        self.play_thread = threading.Thread(target=self.play_with_progress, args=(self.status_var.set,))
        self.play_thread.daemon = True
        self.play_thread.start()
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_var.set("演奏中... 可用F7停止")

    def play_with_progress(self, update_status):
        import keyboard
        if self.sorted_times is None or self.notes_by_time is None or self.player is None:
            update_status("未加载乐谱，无法演奏！")
            return
        total = len(self.sorted_times)
        if total == 0:
            self.elapsed_time_var.set("0:00")
            return
        t0 = self.sorted_times[0]
        # ====== bpm节奏系数，标准bpm为120，可自定义 ======
        bpm = getattr(self, 'bpm', 120)
        bpm_factor = 120 / bpm if bpm else 1.0  # bpm越大越快
        time.sleep(0.5)
        for idx in range(total):
            if self.player._stop.is_set():
                break
            # 必须始终引用self.player._pause，防止对象被替换
            while self.player and not self.player._pause.is_set():
                time.sleep(0.05)
            if not self.player or self.player._stop.is_set():
                break
            t = self.sorted_times[idx]
            keys = self.notes_by_time[t]
            for k in keys:
                key = note_to_key.get(k)
                if key:
                    try:
                        keyboard.press(key)
                    except Exception:
                        try:
                            pyautogui.keyDown(key)
                        except Exception:
                            pass
            time.sleep(0.05)
            for k in keys:
                key = note_to_key.get(k)
                if key:
                    try:
                        keyboard.release(key)
                    except Exception:
                        try:
                            pyautogui.keyUp(key)
                        except Exception:
                            pass
            elapsed_sec = max(0, (t - t0) / 1000)
            m, s = divmod(int(elapsed_sec), 60)
            self.elapsed_time_var.set(f"{m}:{s:02d}")
            update_status(f"演奏进度: {idx+1}/{total}")
            if idx < total - 1:
                interval = (self.sorted_times[idx + 1] - t) / 1000.0 * bpm_factor  # 按bpm调整节奏
                if interval > 0:
                    time.sleep(interval)
            self.player.current_idx = idx + 1
        if self.player:
            self.player.is_playing = False
            self.elapsed_time_var.set(self.total_time_var.get())
        update_status("演奏结束！")

    def stop_play(self):
        if self.player:
            self.player.stop()
        self.status_var.set("已停止，点击开始或按F5重新演奏")
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

    def check_and_set_game_window(self):
        # 查找进程名为'Sky'或'光遇'的窗口，优先'Sky'
        def enum_windows_callback(hwnd, result):
            if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
                tid, pid = win32process.GetWindowThreadProcessId(hwnd)
                try:
                    proc = psutil.Process(pid)
                    name = proc.name()
                    # 进程名可能为Sky.exe、光遇.exe等
                    if name.lower().startswith('sky'):
                        result['Sky'] = hwnd
                    elif '光遇' in name:
                        result['光遇'] = hwnd
                except Exception:
                    pass
        result = {}
        win32gui.EnumWindows(enum_windows_callback, result)
        hwnd = None
        if 'Sky' in result:
            hwnd = result['Sky']
        elif '光遇' in result:
            hwnd = result['光遇']
        if hwnd:
            # 置顶窗口
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                                  win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            return True
        else:
            messagebox.showwarning("未检测到游戏", "未找到进程名为 'Sky' 或 '光遇' 的游戏窗口，请先打开游戏！")
            return False

    def load_music(self):
        sel = self.music_listbox.curselection()
        if not sel:
            messagebox.showwarning("提示", "请先选择乐谱！")
            return False
        selected = self.filtered_music_files[sel[0]]
        path = os.path.join(SHEET_MUSIC_DIR, selected)  # SHEET_MUSIC_DIR已用resource_path
        encodings = ['utf-8', 'utf-8-sig', 'gbk', 'utf-16', 'utf-16-le', 'utf-16-be']
        last_err = None
        music_json = None
        for enc in encodings:
            try:
                with open(path, 'r', encoding=enc) as f:
                    music_json = json.load(f)
                break
            except Exception as e:
                last_err = e
                music_json = None
        if music_json is None:
            messagebox.showerror("错误", f"乐谱文件解析失败: {last_err}")
            return False
        if isinstance(music_json, list) and 'songNotes' in music_json[0]:
            song_notes = music_json[0]['songNotes']
            # 读取bpm字段，若无则默认120
            self.bpm = music_json[0].get('bpm', 120)
        else:
            messagebox.showerror("错误", "乐谱文件格式不正确，未找到songNotes。")
            return False
        notes_by_time = defaultdict(list)
        for note in song_notes:
            notes_by_time[note['time']].append(note['key'])
        sorted_times = sorted(notes_by_time.keys())
        self.notes_by_time = notes_by_time
        self.sorted_times = sorted_times
        return True

    def on_close(self):
        # 保存窗口大小和位置
        try:
            geo = self.root.geometry()
            size_pos = geo.split('+')
            size = size_pos[0].split('x')
            width, height = int(size[0]), int(size[1])
            x, y = int(size_pos[1]), int(size_pos[2])
            cfg = {'width': width, 'height': height, 'x': x, 'y': y}
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(cfg, f)
        except Exception:
            pass
        self.root.destroy()

    def schedule_music_dir_watch(self):
        current_files = set(self.get_all_music_files())
        if current_files != self.last_music_files:
            self.all_music_files = list(current_files)
            self.filtered_music_files = self.all_music_files.copy()
            self.on_search()  # 保持搜索关键字过滤
            self.last_music_files = current_files
        self.root.after(1000, self.schedule_music_dir_watch)

    def bind_hotkeys(self):
        import keyboard
        # 先解绑，防止重复注册
        try:
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass
        # 只注册开始和停止热键
        try:
            keyboard.add_hotkey(self.hotkeys['start'], lambda: self.start_play())
            keyboard.add_hotkey(self.hotkeys['stop'], lambda: self.stop_play())
        except Exception as e:
            messagebox.showwarning("热键注册失败", f"全局热键注册失败，可能需要以管理员身份运行。\n详细信息：{e}")

    def on_music_tab_changed(self):
        # 分页切换时刷新乐谱列表
        self.refresh_music_listbox()

    def on_music_listbox_right_click(self, event):
        """
        右键菜单：仅保留收藏/取消收藏
        """
        idx = self.music_listbox.nearest(event.y)
        if idx < 0 or idx >= len(self.filtered_music_files or []):
            return
        self.music_listbox.selection_clear(0, tk.END)
        self.music_listbox.selection_set(idx)
        filename = self.filtered_music_files[idx]
        menu = tk.Menu(self.music_listbox, tearoff=0)
        # 只保留收藏/取消收藏
        if filename in self.favorites:
            menu.add_command(label="取消收藏", command=lambda: self.toggle_favorite(filename))
        else:
            menu.add_command(label="收藏", command=lambda: self.toggle_favorite(filename))
        menu.tk_popup(event.x_root, event.y_root)

    def toggle_favorite(self, filename):
        """
        收藏/取消收藏，并保存到本地
        """
        if filename in self.favorites:
            self.favorites.remove(filename)
        else:
            self.favorites.add(filename)
        self.save_favorites()
        self.refresh_music_listbox()

    def load_favorites(self):
        """
        加载收藏数据
        """
        import json
        try:
            with open(self.favorite_file, 'r', encoding='utf-8') as f:
                self.favorites = set(json.load(f))
        except Exception:
            self.favorites = set()

    def save_favorites(self):
        """
        保存收藏数据
        """
        import json
        try:
            with open(self.favorite_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.favorites), f, ensure_ascii=False, indent=2)
        except Exception:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    style.theme_use('clam')
    style.configure('.', font=('微软雅黑', 10))
    app = MusicGUI(root)
    app.bind_hotkeys()
    root.mainloop() 