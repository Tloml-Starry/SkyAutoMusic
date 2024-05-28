import json
import time
import keyboard
import pygetwindow as gw

# 读取JSON文件并返回数据
def load_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("文件不存在")
        return None
    except json.JSONDecodeError:
        print("JSON文件格式错误")
        return None

# 选择曲目
def choose_song(songs):
    print("请选择一个曲目喵：")
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

# 执行曲谱
def play_song(song_data):
    for note in song_data:
        keys = note['key']  # 获取当前音符的按键信息
        duration = note['time']  # 获取当前音符的持续时间
        # 按下当前音符对应的按键
        for key in keys:
            keyboard.press(key)
        time.sleep(duration)  # 等待当前音符的持续时间
        # 松开当前音符对应的按键
        for key in keys:
            keyboard.release(key)
        time.sleep(0.1)  # 等待一小段时间，确保按键完全松开后再执行下一个音符

# 查找窗口并激活
def find_and_activate_window(window_title):
    try:
        window = gw.getWindowsWithTitle(window_title)[0]
        window.activate()
    except IndexError:
        print(f"未找到窗口标题为'{window_title}'的窗口")
        exit()
        
# 主程序
if __name__ == "__main__":
    songs_folder = "score/"  # 替换成你的曲谱文件夹路径喵

    # 从文件夹读取所有曲目
    import os
    songs = [f.replace('.json', '') for f in os.listdir(songs_folder) if f.endswith('.json')]

    chosen_song = choose_song(songs)
    if chosen_song:
        song_data = load_json(songs_folder + chosen_song + '.json')
        if song_data:
            find_and_activate_window("Sky")
            play_song(song_data)