import tkinter as tk
from tkinter import ttk, messagebox, PhotoImage
import pygetwindow as gw
from PIL import Image, ImageTk
import difflib

def choose_song_gui(songs):
    def on_select(event):
        if song_listbox.curselection():
            selected_song.set(song_listbox.get(song_listbox.curselection()))

    def on_play():
        if selected_song.get():
            window = gw.getWindowsWithTitle("Sky")
            sky_windows = [win for win in window if win.title == "Sky"]
            if sky_windows:
                root.quit()
            else:
                messagebox.showwarning("警告", "未找到名为'Sky'的窗口，请先启动游戏")

    def on_exit():
        root.quit()
        exit()

    def on_search(event):
        search_term = search_var.get()
        if search_term == "":
            filtered_songs = songs
        else:
            filtered_songs = difflib.get_close_matches(search_term, songs, n=len(songs), cutoff=0.1)
        song_listbox.delete(0, tk.END)
        for song in filtered_songs:
            song_listbox.insert(tk.END, song)

    def on_close():
        root.quit()

    root = tk.Tk()
    root.title("PC端光遇自动弹琴 by:Tloml-Starry github开源项目")
    root.geometry("600x400")
    root.protocol("WM_DELETE_WINDOW", on_close)

    icon = ImageTk.PhotoImage(Image.open('icon.ico'))
    root.iconphoto(True, icon)

    style = ttk.Style()
    style.configure("TButton", font=("Helvetica", 12))
    style.configure("TLabel", font=("Helvetica", 12))
    style.configure("TListbox", font=("Helvetica", 12))

    selected_song = tk.StringVar()
    search_var = tk.StringVar()
    
    frame_left = ttk.Frame(root, padding="10")
    frame_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    frame_right = ttk.Frame(root, padding="10")
    frame_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    search_entry = ttk.Entry(frame_left, textvariable=search_var, font=("Helvetica", 12))
    search_entry.pack(fill=tk.X, pady=5)
    search_entry.bind('<KeyRelease>', on_search)

    song_listbox = tk.Listbox(frame_left, font=("Helvetica", 12))
    song_listbox.pack(fill=tk.BOTH, expand=True)
    for song in songs:
        song_listbox.insert(tk.END, song)
    song_listbox.bind('<<ListboxSelect>>', on_select)

    play_button = ttk.Button(frame_right, text="播放", command=on_play)
    play_button.pack(pady=10)

    exit_button = ttk.Button(frame_right, text="退出", command=on_exit)
    exit_button.pack(pady=10)

    speed_label = ttk.Label(frame_right, text="播放速度")
    speed_label.pack(pady=10)

    speed_var = tk.DoubleVar(value=1.0)
    speed_scale = ttk.Scale(frame_right, variable=speed_var, from_=0.5, to=2.0, orient=tk.HORIZONTAL)
    speed_scale.pack(pady=10)

    root.mainloop()
    return selected_song.get(), speed_var.get()

class LogWindow:
    def __init__(self, root):
        self.root = root
        self.log_frame = ttk.Frame(root)
        self.log_frame.pack(fill=tk.BOTH, expand=True)
        self.text_widget = tk.Text(self.log_frame, state='disabled', wrap='word')
        self.text_widget.pack(fill=tk.BOTH, expand=True)

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