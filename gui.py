import tkinter as tk
from tkinter import ttk, messagebox, PhotoImage
from PIL import Image, ImageTk
from utils import load_json, load_key_mapping
from player import play_song
import threading
import keyboard
import pygetwindow as gw
import json

class MainApplication:
    def __init__(self, root, songs):
        self.root = root
        self.songs = songs
        self.selected_song = tk.StringVar()
        self.search_var = tk.StringVar()
        self.speed_var = tk.DoubleVar(value=1.0)
        
        self.key_mapping = load_key_mapping()
        self.setup_ui()
        self.log_window = LogWindow(self.frame_right)
        self.playing = False
        self.paused = False
        self.stop_event = threading.Event()
        self.play_thread = None

    def setup_ui(self):
        self.root.title("？")
        self.root.geometry("800x600")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        try:
            icon = ImageTk.PhotoImage(Image.open('icon.ico'))
            self.root.iconphoto(True, icon)
        except Exception as e:
            print(f"加载图标失败: {e}")

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", font=("Helvetica", 12), padding=6)
        style.configure("TLabel", font=("Helvetica", 12), padding=6)
        style.configure("TListbox", font=("Helvetica", 12), padding=6)

        self.frame_left = ttk.Frame(self.root, padding="10")
        self.frame_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.frame_right = ttk.Frame(self.root, padding="10")
        self.frame_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        search_entry = ttk.Entry(self.frame_left, textvariable=self.search_var, font=("Helvetica", 12))
        search_entry.pack(fill=tk.X, pady=5)
        search_entry.bind('<KeyRelease>', self.on_search)

        self.song_listbox_frame = ttk.Frame(self.frame_left)
        self.song_listbox_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.song_listbox_scrollbar = ttk.Scrollbar(self.song_listbox_frame, orient=tk.VERTICAL)
        self.song_listbox = tk.Listbox(self.song_listbox_frame, font=("Helvetica", 12), yscrollcommand=self.song_listbox_scrollbar.set)
        self.song_listbox_scrollbar.config(command=self.song_listbox.yview)

        self.song_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.song_listbox_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for song in self.songs:
            self.song_listbox.insert(tk.END, song)
        self.song_listbox.bind('<<ListboxSelect>>', self.on_select)

        button_frame = ttk.Frame(self.frame_right)
        button_frame.pack(pady=10)

        play_button = ttk.Button(button_frame, text="播放", command=self.on_play)
        play_button.pack(side=tk.LEFT, padx=5)

        pause_button = ttk.Button(button_frame, text="暂停", command=lambda: self.toggle_pause(None))
        pause_button.pack(side=tk.LEFT, padx=5)

        exit_button = ttk.Button(button_frame, text="退出", command=self.on_exit)
        exit_button.pack(side=tk.LEFT, padx=5)

        speed_label = ttk.Label(self.frame_right, text="播放速度", font=("Helvetica", 12, "bold"))
        speed_label.pack(pady=10)

        speed_frame = ttk.Frame(self.frame_right)
        speed_frame.pack(pady=5)

        speed_scale = ttk.Scale(speed_frame, variable=self.speed_var, from_=0.5, to=2.0, orient=tk.HORIZONTAL, command=self.update_speed_label)
        speed_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.speed_display = ttk.Label(speed_frame, text=f"{self.speed_var.get():.1f}x", font=("Helvetica", 10))
        self.speed_display.pack(side=tk.LEFT, padx=5)

        song_count_label = ttk.Label(self.frame_left, text=f"曲谱数量: {len(self.songs)}", font=("Helvetica", 12))
        song_count_label.pack(pady=5)

        self.edit_score_button = ttk.Button(self.frame_right, text="编辑曲谱", command=self.open_score_editor)
        self.edit_score_button.pack(pady=5)

    def on_select(self, event):
        if self.song_listbox.curselection():
            self.selected_song.set(self.song_listbox.get(self.song_listbox.curselection()))

    def on_play(self):
        if self.selected_song.get():
            try:
                windows = gw.getWindowsWithTitle('Sky') + gw.getWindowsWithTitle('光·遇')
                sky_window = next((w for w in windows if w.title.strip() == 'Sky' or w.title.strip() == '光·遇'), None)
                if sky_window:
                    print(f"找到窗口: {sky_window.title}")
                    sky_window.activate()
                    self.playing = True
                else:
                    raise IndexError
            except IndexError:
                messagebox.showerror("错误", "未找到 光·遇 窗口，请打开光·遇再点击演奏")
                self.playing = False
            except Exception as e:
                print(f"发生错误: {e}")
                messagebox.showerror("错误", f"发生未知错误: {e}")

            if self.playing and not self.paused:
                song_data_list = load_json(f"score/score/{self.selected_song.get()}.json")
                if song_data_list and isinstance(song_data_list, list) and len(song_data_list) > 0:
                    song_data = song_data_list[0]
                    if "songNotes" in song_data:
                        self.stop_event.clear()
                        keyboard.on_press_key("F11", lambda _: self.stop_event.set())
                        keyboard.on_press_key("F10", self.toggle_pause)

                        self.log_window.log("按下 F11 键停止演奏")
                        self.play_thread = threading.Thread(target=play_song, args=(song_data, self.stop_event, self.speed_var.get(), self.log_window))
                        self.play_thread.start()
                        
                        self.log_window.log("开始播放歌曲: " + self.selected_song.get())
                    else:
                        messagebox.showerror("错误", "曲谱数据格式不正确")
                else:
                    messagebox.showerror("错误", "加载曲谱数据失败或数据格式不正确")

    def toggle_pause(self, event):
        if self.playing:
            if self.paused:
                self.paused = False
                self.stop_event.clear()
                self.log_window.log("继续演奏")
            else:
                self.paused = True
                self.stop_event.set()
                self.log_window.log("演奏暂停")

    def on_exit(self):
        self.root.quit()
        exit()

    def on_search(self, event):
        search_term = self.search_var.get().lower()
        filtered_songs = [song for song in self.songs if search_term in song.lower()]
        self.song_listbox.delete(0, tk.END)
        for song in filtered_songs:
            self.song_listbox.insert(tk.END, song)

    def on_close(self):
        self.root.quit()

    def update_speed_label(self, value):
        self.speed_display.config(text=f"{float(value):.1f}x")

    def open_score_editor(self):
        if not self.selected_song.get():
            messagebox.showwarning("提示", "请先选择一首曲谱进行编辑")
            return

        editor_window = tk.Toplevel(self.root)
        editor_window.title("曲谱编辑器")

        song_data = load_json(f"score/score/{self.selected_song.get()}.json")
        if song_data:
            text_widget = tk.Text(editor_window)
            text_widget.insert(tk.END, json.dumps(song_data, indent=4))
            text_widget.pack()

        def save_score():
            try:
                new_data = json.loads(text_widget.get("1.0", tk.END))
                with open(f"score/score/{self.selected_song.get()}.json", 'w') as f:
                    json.dump(new_data, f, indent=4)
                messagebox.showinfo("成功", "曲谱已保存")
            except json.JSONDecodeError:
                messagebox.showerror("错误", "曲谱格式不正确")

        save_button = ttk.Button(editor_window, text="保存", command=save_score)
        save_button.pack()

class LogWindow:
    def __init__(self, root):
        self.root = root
        self.log_frame = ttk.Frame(root)
        self.log_frame.pack(fill=tk.BOTH, expand=True)
        self.text_widget = tk.Text(self.log_frame, state='disabled', wrap='word')
        self.text_widget.pack(fill=tk.BOTH, expand=True)

        self.text_widget.config(state='normal')
        self.text_widget.insert(tk.END, "作者: Tloml-Starry\n")
        self.text_widget.insert(tk.END, "公告: 欢迎使用SkyAutoMusic!这是开源项目,如果你是买来的,那你被骗了!\n")
        self.text_widget.insert(tk.END, "访问项目主页: ")
        self.text_widget.insert(tk.END, "https://github.com/Tloml-Starry/SkyAutoMusic\n", ("link",))
        self.text_widget.tag_config("link", foreground="blue")
        self.text_widget.config(state='disabled')

    def log(self, message):
        self.text_widget.config(state='normal')
        self.text_widget.insert(tk.END, message + '\n')
        self.text_widget.config(state='disabled')
        self.text_widget.yview(tk.END)

    def close(self):
        self.root.destroy()

def show_log_window():
    root = tk.Tk()
    root.title("日志")
    log_window = LogWindow(root)
    return root, log_window

def show_progress_window():
    root = tk.Tk()
    root.title("Progress Window")
    
    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100)
    progress_bar.pack(expand=True, fill='both')
    
    return root, progress_var