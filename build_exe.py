import PyInstaller.__main__

# 使用PyInstaller打包Python脚本为可执行文件
PyInstaller.__main__.run([
    'Main.py',  # 主程序入口文件
    '--onefile',  # 打包成单个可执行文件
    '--windowed',  # 不显示命令行窗口
    '--icon=icon.ico',  # 设置程序图标
    '--name=SkyPlayer'  # 设置生成的可执行文件名称
])