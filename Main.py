import os
import tkinter as tk
from gui import MainApplication

def main():
    root = tk.Tk()
    songs_folder = "score/score/"
    songs = [f.replace('.json', '') for f in os.listdir(songs_folder) if f.endswith('.json')]
    app = MainApplication(root, songs)
    root.mainloop()

if __name__ == "__main__":
    main()