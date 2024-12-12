import PyInstaller.__main__

PyInstaller.__main__.run([
    'Main.py',
    '--onefile',
    '--windowed',
    '--icon=icon.ico',
    '--add-data=icon.ico;.',
    '--name=SkyPlayer v2.4.1',
    '--manifest=app.manifest'
])