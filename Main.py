import time
import keyboard
import json
import pygetwindow as gw
import os
import subprocess

subprocess.call("更新曲库.bat", shell=True)

key_mapping = {
    "1Key0": "Y", "1Key1": "U", "1Key2": "I", "1Key3": "O", "1Key4": "P",
    "1Key5": "H", "1Key6": "J", "1Key7": "K", "1Key8": "L", "1Key9": ";",
    "1Key10": "N", "1Key11": "M", "1Key12": ",", "1Key13": ".", "1Key14": "/",
    "2Key0": "Y", "2Key1": "U", "2Key2": "I", "2Key3": "O", "2Key4": "P",
    "2Key5": "H", "2Key6": "J", "2Key7": "K", "2Key8": "L", "2Key9": ";",
    "2Key10": "N", "2Key11": "M", "2Key12": ",", "Key13": ".", "Key14": "/"
}


def load_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"读取JSON文件出错: {e}")
        return None


def choose_song(songs):
    print("请选择一个曲目：")
    for i, song in enumerate(songs):
        print(f"{i + 1}. {song}")
    while True:
        try:
            song_index = int(input("输入曲目编号：")) - 1
            if 0 <= song_index < len(songs):
                return songs[song_index]
            else:
                print("请输入有效的曲目编号")
        except ValueError:
            print("请输入有效的曲目编号")


def press_key(key, time_interval):
    if key in key_mapping:
        key_to_press = key_mapping[key]
        keyboard.press(key_to_press)
        time.sleep(time_interval)
        keyboard.release(key_to_press)


def play_song(song_data):
    print("开始演奏曲谱，按下ESC键终止")
    start_time = time.time()
    prev_note_time = song_data[0]['songNotes'][0]["time"]
    for note in song_data[0]["songNotes"]:
        if not running:
            break

        delay = note["time"] - prev_note_time
        time.sleep(delay / 1000)
        press_key(note["key"], 6 / song_data[0]["bpm"])
        prev_note_time = note["time"]

    end_time = time.time()
    total_time = end_time - start_time
    print(f"曲谱演奏完成！总共用时：{total_time:.2f}秒")


if __name__ == "__main__":
    songs_folder = "score/score/"
    songs = [f.replace('.json', '') for f in os.listdir(songs_folder) if f.endswith('.json')]

    chosen_song = choose_song(songs)
    if chosen_song:
        song_data = load_json(os.path.join(songs_folder, chosen_song + '.json'))
        if song_data:
            window = gw.getWindowsWithTitle("Sky")
            if window:
                sky_window = window[0]
                sky_window.activate()
            else:
                print("未找到名为'Sky'的窗口")
                exit()

            running = {'value': True}
            keyboard.on_press_key("esc", lambda _: setattr(running, 'value', False))
            play_song(song_data)
