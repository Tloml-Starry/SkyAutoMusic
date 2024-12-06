import time
import threading
from utils import press_key

def play_song(song_data, stop_event, speed_factor, log_window):
    notes = song_data.get("songNotes", [])
    start_time = time.perf_counter()
    
    for i, note in enumerate(notes):
        if stop_event.is_set():
            log_window.log("演奏已停止")
            return
        
        if "key" in note:
            current_time = time.perf_counter()
            note_time = note["time"] / 1000 / speed_factor
            sleep_time = note_time - (current_time - start_time)
            
            if sleep_time > 0:
                time.sleep(sleep_time)
            
            press_key(note["key"], 0.1)
    
    log_window.log("演奏结束")