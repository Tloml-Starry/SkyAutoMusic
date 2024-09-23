# build_exe.py
import PyInstaller.__main__

PyInstaller.__main__.run([
    'Main.py',
    '--onefile',
    '--windowed',
    '--icon=icon.ico',
    '--name=SkyPlayer'
])