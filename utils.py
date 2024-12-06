import json
import chardet
import codecs
import keyboard
import time

def load_key_mapping(custom_mapping=None):
    # 默认按键映射
    default_mapping = {f"1Key{i}": chr(89 + i) for i in range(15)}
    default_mapping.update({f"2Key{i}": chr(89 + i) for i in range(15)})
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