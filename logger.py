import tkinter as tk
from tkinter import ttk

class LogWindow:
    def __init__(self, root):
        self.root = root
        self.log_frame = ttk.Frame(root)
        self.log_frame.pack(fill=tk.BOTH, expand=True)
        self.text_widget = tk.Text(self.log_frame, state='disabled', wrap='word')
        self.text_widget.pack(fill=tk.BOTH, expand=True)

    def log(self, message):
        self.text_widget.config(state='normal')
        self.text_widget.insert(tk.END, message + '\n')
        self.text_widget.config(state='disabled')
        self.text_widget.yview(tk.END)

    def close(self):
        self.root.destroy()

def show_log_window():
    root = tk.Tk()
    root.title("日志")
    log_window = LogWindow(root)
    return root, log_window