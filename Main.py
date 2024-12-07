import os
import tkinter as tk
from gui import MainApplication

def rename_txt_to_json(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith('.txt'):
            base = os.path.splitext(filename)[0]
            new_filename = base + '.json'
            new_filepath = os.path.join(folder_path, new_filename)
            if not os.path.exists(new_filepath):
                os.rename(os.path.join(folder_path, filename), new_filepath)
                print(f"重命名 {filename} 为 {new_filename}")
            else:
                print(f"文件 {new_filename} 已存在，跳过重命名 {filename}")

def main():
    songs_folder = "score/score/"
    rename_txt_to_json(songs_folder)

    root = tk.Tk()
    songs = [f.replace('.json', '') for f in os.listdir(songs_folder) if f.endswith('.json')]
    app = MainApplication(root, songs)
    root.mainloop()

if __name__ == "__main__":
    main()