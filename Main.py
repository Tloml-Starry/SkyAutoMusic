import os
import pygetwindow as gw
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from gui import choose_song_gui, show_log_window
from utils import load_json
from player import play_song
import keyboard
import ctypes

def main():
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("myappid")

    songs_folder = "score/score/"
    songs = [f.replace('.json', '') for f in os.listdir(songs_folder) if f.endswith('.json')]

    chosen_song, speed_factor = choose_song_gui(songs)
    if chosen_song:
        song_data_list = load_json(os.path.join(songs_folder, chosen_song + '.json'))
        if song_data_list and isinstance(song_data_list, list) and len(song_data_list) > 0:
            song_data = song_data_list[0]
            if "songNotes" in song_data:
                sky_windows = None
                window = gw.getWindowsWithTitle("Sky")
                sky_windows = [win for win in window if win.title == "Sky"]
                if sky_windows:
                    sky_window = window[0]
                    sky_window.activate()
                else:
                    messagebox.showwarning("警告", "未找到名为'Sky'的窗口，请先启动游戏")
                    return

                stop_event = threading.Event()
                keyboard.on_press_key("F11", lambda _: stop_event.set())

                log_root, log_window = show_log_window()
                log_window.log("按下 F11 键停止演奏")
                threading.Thread(target=play_song, args=(song_data, stop_event, speed_factor, log_window)).start()
                
                log_window.log("开始播放歌曲: " + chosen_song)
                log_root.mainloop()
            else:
                messagebox.showerror("错误", "曲谱数据格式不正确")
        else:
            messagebox.showerror("错误", "加载曲谱数据失败或数据格式不正确")

if __name__ == "__main__":
    main()