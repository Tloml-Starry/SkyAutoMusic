import time
import threading
from utils import press_key, release_all_keys, get_key_mapping
import keyboard

def play_song(song_data, stop_event, speed_factor, log_window, initial_progress=0):
    # 预处理音符数据
    notes = []
    if isinstance(song_data, dict):
        notes = song_data.get("songNotes", [])
    else:
        notes = song_data
        
    if not notes:
        log_window.log("没有找到可播放的音符数据")
        return
        
    # 预计算时间戳
    first_time = notes[0].get("time", 0) if isinstance(notes[0], dict) else notes[0][1]
    last_time = notes[-1].get("time", 0) if isinstance(notes[-1], dict) else notes[-1][1]
    total_duration = last_time - first_time
    
    # 使用缓存的按键映射
    key_map = {}
    for note in notes:
        key = note.get("key") if isinstance(note, dict) else note[0]
        if key not in key_map:
            key_map[key] = get_key_mapping(key)
            
    # 播放主循环
    start_time = time.perf_counter() - (first_time / 1000 / speed_factor)
    pause_start_time = 0
    pause_total_time = 0
    
    # 获取起始位置
    start_position = getattr(log_window, 'seek_position', initial_progress)
    if start_position > 0:
        # 找到对应的音符索引
        current_index = 0
        for i, note in enumerate(notes):
            note_time = note.get("time", 0) if isinstance(note, dict) else note[1]
            if (note_time - first_time) / total_duration * 100 >= start_position:
                current_index = i
                break
        notes = notes[current_index:]  # 从指定位置开始播放
        first_time = notes[0].get("time", 0) if isinstance(notes[0], dict) else notes[0][1]
        start_time = time.perf_counter() - (first_time / 1000 / speed_factor)
        
        # 设置初始进度
        if hasattr(log_window, 'update_play_progress'):
            log_window.update_play_progress(start_position)
    
    # 记录当前时间点的所有音符
    current_chord = []
    current_time = 0
    
    for i, note in enumerate(notes):
        if stop_event.is_set():
            release_all_keys()
            return
            
        while getattr(log_window, 'paused', False):
            if stop_event.is_set():
                release_all_keys()
                return
            if pause_start_time == 0:
                pause_start_time = time.perf_counter()
                release_all_keys()
            time.sleep(0.1)
            continue
            
        if pause_start_time > 0:
            pause_duration = time.perf_counter() - pause_start_time
            pause_total_time += pause_duration
            pause_start_time = 0
            start_time += pause_duration
        
        key = note.get("key") if isinstance(note, dict) else note[0]
        note_time = (note.get("time", 0) if isinstance(note, dict) else note[1]) / 1000 / speed_factor
        
        # 检查是否需要播放和弦
        if i < len(notes) - 1:
            next_note = notes[i + 1]
            next_time = (next_note.get("time", 0) if isinstance(next_note, dict) else next_note[1]) / 1000 / speed_factor
            
            # 如果下一个音符时间间隔很小(小于0.05秒),则认为是和弦的一部分
            if abs(next_time - note_time) < 0.05:
                current_chord.append(key)
                current_time = note_time
                continue
        
        # 播放当前和弦或单个音符
        if current_chord:
            current_chord.append(key)
            sleep_time = current_time - (time.perf_counter() - start_time)
            
            if sleep_time > 0:
                time.sleep(sleep_time)
                
            # 同时按下和弦的所有音符
            try:
                for chord_key in current_chord:
                    key_to_press = key_map[chord_key]
                    keyboard.press(key_to_press)
                time.sleep(0.1)  
                # 同时释放和弦的所有音符
                for chord_key in current_chord:
                    key_to_press = key_map[chord_key]
                    keyboard.release(key_to_press)
                    
                # 更新进度
                progress = (note.get("time", 0) if isinstance(note, dict) else note[1] - first_time) / total_duration * 100
                if hasattr(log_window, 'update_play_progress'):
                    log_window.update_play_progress(progress)
            except Exception as e:
                log_window.log(f"按键错误: {str(e)}")
                release_all_keys()
                
            current_chord = []
        else:
            # 播放单个音符
            sleep_time = note_time - (time.perf_counter() - start_time)
            
            if sleep_time > 0:
                time.sleep(sleep_time)
            
            try:
                key_to_press = key_map[key]
                keyboard.press(key_to_press)
                time.sleep(0.1)
                keyboard.release(key_to_press)
                
                current_time = note.get("time", 0) if isinstance(note, dict) else note[1]
                progress = (current_time - first_time) / total_duration * 100
                if hasattr(log_window, 'update_play_progress'):
                    log_window.update_play_progress(progress)
            except Exception as e:
                log_window.log(f"按键错误 {key}: {str(e)}")
                release_all_keys()
    
    release_all_keys()
    log_window.log("演奏结束")