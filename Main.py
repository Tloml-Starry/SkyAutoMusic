import os
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from gui import ModernSkyMusicPlayer
from config import LOCAL_VERSION  # 从 config.py 导入

def resource_path(relative_path):
    """获取资源文件的绝对路径"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

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

    app = QApplication(sys.argv)
    
    try:
        app_icon = QIcon(resource_path("icon.ico"))
        app.setWindowIcon(app_icon)
    except Exception as e:
        print(f"加载图标失败: {str(e)}")
    
    window = ModernSkyMusicPlayer()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()