import PyInstaller.__main__

PyInstaller.__main__.run([
    'Main.py',
    '--onefile',
    '--windowed',
    '--icon=icon.ico',
    '--add-data=icon.ico;.',
    '--name=SkyPlayer',
    '--manifest=app.manifest'
])