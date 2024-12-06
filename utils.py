import json
import chardet
import codecs
import keyboard
import time

def load_key_mapping(custom_mapping=None):
    # 默认按键映射
    default_mapping = {
        "1Key0": "Y", "1Key1": "U", "1Key2": "I", "1Key3": "O", "1Key4": "P",
        "1Key5": "H", "1Key6": "J", "1Key7": "K", "1Key8": "L", "1Key9": ";",
        "1Key10": "N", "1Key11": "M", "1Key12": ",", "1Key13": ".", "1Key14": "/",
        "2Key0": "Y", "2Key1": "U", "2Key2": "I", "2Key3": "O", "2Key4": "P",
        "2Key5": "H", "2Key6": "J", "2Key7": "K", "2Key8": "L", "2Key9": ";",
        "2Key10": "N", "2Key11": "M", "2Key12": ",", "2Key13": ".", "2Key14": "/"
    }
    if custom_mapping:
        default_mapping.update(custom_mapping)
    return default_mapping

key_mapping = load_key_mapping()

def load_json(file_path):
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            encoding = chardet.detect(raw_data)['encoding']  # 检测文件编码
        with codecs.open(file_path, 'r', encoding=encoding) as f:
            return json.load(f)  # 加载JSON数据
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"读取JSON文件出错: {e}")
        return None

def press_key(key, time_interval):
    if key in key_mapping:
        key_to_press = key_mapping[key]
        keyboard.press(key_to_press)  # 按下按键
        time.sleep(time_interval)  # 等待指定时间
        keyboard.release(key_to_press)  # 释放按键