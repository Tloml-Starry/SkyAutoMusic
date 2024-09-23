import time
import threading
from utils import press_key

def play_song(song_data, stop_event, speed_factor, log_window):
    notes = song_data.get("songNotes", [])
    
    start_time = time.time()
    
    for i, note in enumerate(notes):
        if stop_event.is_set():
            log_window.log("演奏已停止")
            time.sleep(3)
            log_window.close()
            break
        
        print(f"Note {i}: {note}")
        
        if "key" in note:
            current_time = time.time()
            note_time = note["time"] / 1000 / speed_factor
            sleep_time = note_time - (current_time - start_time)
            
            if sleep_time > 0:
                time.sleep(sleep_time)
            
            press_key(note["key"], 0.1)
        else:
            print(f"Note {i} does not contain 'key' field")