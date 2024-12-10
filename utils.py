import json
import chardet
import codecs
import keyboard
import time
import random

def load_key_mapping(custom_mapping=None):
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

def load_json(file_path, encoding_cache={}):
    """优化JSON加载"""
    try:
        if file_path in encoding_cache:
            encoding = encoding_cache[file_path]
        else:
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                encoding = chardet.detect(raw_data)['encoding']
                encoding_cache[file_path] = encoding
                
        with codecs.open(file_path, 'r', encoding=encoding) as f:
            data = json.load(f)
            if isinstance(data, list) and data:
                song_data = data[0]
                return song_data if "songNotes" in song_data else data
            return data
    except Exception as e:
        print(f"读取JSON文件出错: {e}")
        return None

def press_key(key, time_interval, delay_enabled=False, delay_min=200, delay_max=500):
    if key in key_mapping:
        key_to_press = key_mapping[key]
        keyboard.press(key_to_press)
        
        if delay_enabled:
            delay = random.randint(delay_min, delay_max) / 1000.0
            time.sleep(delay)
        
        time.sleep(time_interval)
        keyboard.release(key_to_press)
    else:
        print(f"按键 {key} 未找到映射")

def release_all_keys():
    """释放所有已映射的按键"""
    for key in key_mapping.values():
        keyboard.release(key)

# 优化按键映射
_key_map_cache = {}

def get_key_mapping(key):
    """使用缓存获取按键映射"""
    if key not in _key_map_cache:
        _key_map_cache[key] = key_mapping.get(key)
    return _key_map_cache[key]
