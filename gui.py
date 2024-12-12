import sys
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QListWidget, QLineEdit, QLabel, QSlider, QDockWidget,
                             QProgressBar, QTabWidget, QGridLayout, QComboBox, QMenu, QMessageBox,
                             QCheckBox, QStackedLayout, QSizePolicy)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QEvent
from PyQt6.QtGui import QIcon, QDoubleValidator, QKeySequence
import os
from player import play_song
from utils import load_json, key_mapping, release_all_keys
import threading
import keyboard
import pygetwindow as gw
import random
import time
import webbrowser
import requests
from config import LOCAL_VERSION

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def fetch_latest_version():
    try:
        response = requests.get('https://gitee.com/Tloml-Starry/resources/raw/master/resources/json/SkyAutoMusicVersion.json')
        if response.status_code == 200:
            data = response.json()
            return data.get('version', '未知版本')
        else:
            return '获取失败'
    except Exception as e:
        print(f"获取最新版本信息失败: {e}")
        return '获取失败'

class PlayThread(QThread):
    update_log = pyqtSignal(str)
    update_progress = pyqtSignal(float)
    update_time = pyqtSignal(float)

    def __init__(self, song_data, speed, delay_enabled=False, delay_min=200, delay_max=500):
        super().__init__()
        self.song_data = song_data
        self.speed = speed
        self.stop_event = threading.Event()
        self.paused = False
        self.seek_position = 0
        self.initial_progress = 0
        self.manual_stop = False
        self.start_time = 0
        self.delay_enabled = delay_enabled
        self.delay_min = delay_min
        self.delay_max = delay_max

    def run(self):
        try:
            self.start_time = time.time()
            play_song(
                self.song_data, 
                self.stop_event, 
                self.speed, 
                self,
                self.initial_progress,
                self.delay_enabled,
                self.delay_min,
                self.delay_max
            )
            self.update_play_progress(self.initial_progress)
        except Exception as e:
            self.update_log.emit(f"播放出错: {str(e)}")

    def stop(self):
        self.manual_stop = True
        self.stop_event.set()

    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            release_all_keys()

    def log(self, message):
        self.update_log.emit(message)

    def update_play_progress(self, progress):
        self.update_progress.emit(progress)
        current_time = (time.time() - self.start_time) * self.speed
        if not self.paused:
            self.update_time.emit(current_time)

class HotkeyEdit(QLineEdit):
    def __init__(self, default_key, parent=None):
        super().__init__(parent)
        self.default_key = default_key
        self.setReadOnly(True)
        self.setText(default_key)
        self.setPlaceholderText("点击输入快捷键...")
        self.setup_style()
        
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.setPlaceholderText("请按下新的快捷键...")
        
    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        if not self.text():
            self.setText(self.default_key)
        self.setPlaceholderText("点击输入快捷键...")
        
    def keyPressEvent(self, event):
        modifiers = event.modifiers()
        key = event.key()
        
        if key in (Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta):
            return
            
        key_sequence = []
        
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            key_sequence.append("Ctrl")
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            key_sequence.append("Shift")
        if modifiers & Qt.KeyboardModifier.AltModifier:
            key_sequence.append("Alt")
        
        key_text = QKeySequence(key).toString()
        if key_text:
            key_sequence.append(key_text)
            
        final_text = "+".join(key_sequence)
        
        if final_text:
            self.setText(final_text)
            self.clearFocus()
            self.setStyleSheet("""
                QLineEdit {
                    background-color: #4CAF50;
                    color: #ffffff;
                    border: 1px solid #45a049;
                    border-radius: 4px;
                    padding: 4px;
                }
            """)
            QTimer.singleShot(500, self.restore_style)
            
            if self.parent() and hasattr(self.parent(), "update_hotkey"):
                self.parent().update_hotkey(self.objectName(), final_text)
    
    def restore_style(self):
        self.setStyleSheet("""
            QLineEdit {
                background-color: #3b3b3b;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px;
            }
            QLineEdit:focus {
                border: 1px solid #4CAF50;
                background-color: #333333;
            }
        """)
    
    def reset(self):
        self.setText(self.default_key)
        self.setStyleSheet("""
            QLineEdit {
                background-color: #45a049;
                color: #ffffff;
                border: 1px solid #4CAF50;
                border-radius: 4px;
                padding: 4px;
            }
        """)
        QTimer.singleShot(500, self.restore_style)
    
    def setup_style(self):
        self.setStyleSheet("""
            QLineEdit {
                background-color: #3b3b3b;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px;
            }
            QLineEdit:focus {
                border: 1px solid #4CAF50;
                background-color: #333333;
            }
        """)

class SpeedInput(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        validator = QDoubleValidator(0.1, 10.0, 1, self)
        validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.setValidator(validator)
        self.setFixedWidth(50)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        try:
            value = float(self.text())
            if value < 0.1:
                self.setText("0.1")
            elif value > 10.0:
                self.setText("10.0")
        except:
            self.setText("1.0")

class ModernSkyMusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sky Auto Music")
        self.setGeometry(100, 100, 1200, 800)
        
        try:
            self.setWindowIcon(QIcon(resource_path("icon.ico")))
        except Exception as e:
            print(f"加载窗口图标失败: {str(e)}")
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QListWidget {
                background-color: #252525;
                color: #ffffff;
                border: 1px solid #333333;
                border-radius: 4px;
                font-size: 12px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 4px;
                border-radius: 2px;
            }
            QListWidget::item:selected {
                background-color: #2d2d2d;
                color: #4CAF50;
            }
            QListWidget::item:hover {
                background-color: #2a2a2a;
            }
            QLineEdit {
                background-color: #252525;
                color: #ffffff;
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 6px;
            }
            QPushButton {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #333333;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                border: 1px solid #4CAF50;
            }
            QPushButton:pressed {
                background-color: #4CAF50;
            }
            QLabel {
                color: #cccccc;
            }
            QProgressBar {
                border: 1px solid #333333;
                border-radius: 4px;
                text-align: center;
                background-color: #252525;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
            QSlider::groove:horizontal {
                border: 1px solid #333333;
                height: 8px;
                background: #252525;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #4CAF50;
                border: 1px solid #45a049;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #45a049;
            }
            QTabWidget::pane {
                border: 1px solid #333333;
                background-color: #252525;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #ffffff;
                padding: 8px 16px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #4CAF50;
            }
            QTabBar::tab:hover {
                background-color: #3d3d3d;
            }
            QDockWidget {
                color: #ffffff;
                titlebar-close-icon: url(close.png);
                titlebar-normal-icon: url(float.png);
            }
            QDockWidget::title {
                background-color: #2d2d2d;
                padding: 6px;
            }
            QMenu {
                background-color: #252525;
                color: #ffffff;
                border: 1px solid #333333;
            }
            QMenu::item {
                padding: 5px 20px;
            }
            QMenu::item:selected {
                background-color: #4CAF50;
            }
            QComboBox {
                background-color: #252525;
                color: #ffffff;
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 4px 8px;
                min-width: 100px;
            }
            QComboBox:hover {
                border: 1px solid #4CAF50;
            }
            QComboBox:focus {
                border: 1px solid #4CAF50;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png);
                width: 12px;
                height: 12px;
            }
            QComboBox::down-arrow:on {
                top: 1px;
            }
            QComboBox QAbstractItemView {
                background-color: #252525;
                color: #ffffff;
                selection-background-color: #4CAF50;
                selection-color: #ffffff;
                border: 1px solid #333333;
            }
        """)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        self.current_song_data = None
        self.play_thread = None
        self.current_hotkeys = {
            "pause": "F10",
            "stop": "F11"
        }
        self.hotkey_edits = {}
        self.total_duration = 0
        
        self._song_cache = {}
        self._current_song = None
        self._max_cache_size = 50
        
        self.favorites_file = "favorites.json"
        self.hotkey_settings_file = "hotkey_settings.json"
        
        self.delay_enabled = False
        self.delay_min = 200
        self.delay_max = 500
        
        self.current_play_mode = "单曲循环"
        
        self.setup_main_interface()
        self.setup_log_window()
        
        self.favorites = self.load_favorites()
        self.load_hotkey_settings()
        self.load_song_list()
        self.load_favorites_list()
        
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._update_ui)
        self._update_timer.start(100)

        self.setup_hotkeys()
        
        self.register_global_hotkeys()

        self.window_check_timer = QTimer()
        self.window_check_timer.timeout.connect(self.check_window_focus)
        self.window_check_timer.start(1000)

        self.load_delay_settings()

        self.is_dragging = False

    def setup_main_interface(self):
        main_interface = QWidget()
        main_layout = QVBoxLayout(main_interface)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        main_tab_widget = QTabWidget()
        
        play_tab = QWidget()
        play_layout = QHBoxLayout(play_tab)
        play_layout.setContentsMargins(5, 5, 5, 5)
        play_layout.setSpacing(10)
        
        self.setup_left_panel(play_layout)
        self.setup_right_panel(play_layout)
        
        main_tab_widget.addTab(play_tab, "播放")
        
        about_tab = QWidget()
        about_layout = QVBoxLayout(about_tab)
        about_layout.setContentsMargins(20, 20, 20, 20)
        about_layout.setSpacing(10)
        
        latest_version = fetch_latest_version()
        
        version_label = QLabel(f"当前版本: {LOCAL_VERSION}")
        latest_version_label = QLabel(f"最新版本: {latest_version}")
        author_label = QLabel("作者: Tloml-Starry")
        
        homepage_label = QLabel('项目主页：<a href="https://github.com/Tloml-Starry/SkyAutoMusic">GitHub</a> | <a href="https://gitee.com/Tloml-Starry/SkyAutoMusic">Gitee</a>')
        homepage_label.setOpenExternalLinks(True)
        
        feedback_label = QLabel('BUG反馈&功能提议&流: <a href="https://qm.qq.com/q/dWe60BFyE0">392665563</a>')
        feedback_label.setOpenExternalLinks(True)
        
        for widget in [version_label, latest_version_label, author_label, homepage_label, feedback_label]:
            widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            about_layout.addWidget(widget)
        
        about_layout.addStretch()
        
        main_tab_widget.addTab(about_tab, "关于")
        
        main_layout.addWidget(main_tab_widget)
        self.main_layout.addWidget(main_interface)

    def setup_left_panel(self, layout):
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)
        left_layout.setSpacing(10)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索曲...")
        self.search_input.setFixedHeight(30)
        self.search_input.textChanged.connect(self.filter_songs)
        left_layout.addWidget(self.search_input)
        
        tab_widget = QTabWidget()
        tab_widget.currentChanged.connect(self.on_tab_changed)
        
        songs_tab = QWidget()
        songs_layout = QVBoxLayout(songs_tab)
        self.song_list = QListWidget()
        self.song_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.song_list.itemDoubleClicked.connect(self.load_and_play_song)
        self.song_list.itemClicked.connect(self.load_song)
        self.song_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.song_list.customContextMenuRequested.connect(self.show_song_context_menu)
        songs_layout.addWidget(self.song_list)
        tab_widget.addTab(songs_tab, "🎵")
        
        favorites_tab = QWidget()
        favorites_layout = QVBoxLayout(favorites_tab)
        self.favorites_list = QListWidget()
        self.favorites_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.favorites_list.itemDoubleClicked.connect(self.load_and_play_song)
        self.favorites_list.itemClicked.connect(self.load_song)
        self.favorites_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.favorites_list.customContextMenuRequested.connect(self.show_favorites_context_menu)
        favorites_layout.addWidget(self.favorites_list)
        tab_widget.addTab(favorites_tab, "💙")
        
        open_folder_tab = QWidget()
        tab_widget.addTab(open_folder_tab, "📂")
        
        left_layout.addWidget(tab_widget)
        layout.addWidget(left_panel, stretch=2)

    def setup_right_panel(self, layout):
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 5, 5, 5)
        right_layout.setSpacing(10)
        
        # 播放控制区域
        play_controls = QHBoxLayout()
        play_controls.setSpacing(10)
        
        self.play_button = QPushButton("开始")
        self.play_button.setFixedHeight(30)
        self.play_button.clicked.connect(self.toggle_pause)
        play_controls.addWidget(self.play_button)
        
        self.stop_button = QPushButton("结束演奏")
        self.stop_button.setFixedHeight(30)
        self.stop_button.clicked.connect(self.stop_playback)
        play_controls.addWidget(self.stop_button)
        
        self.play_mode_button = QPushButton(self.current_play_mode)
        self.play_mode_button.setFixedHeight(30)
        self.play_mode_button.clicked.connect(self.toggle_play_mode)
        play_controls.addWidget(self.play_mode_button)
        
        self.auto_play = QCheckBox("自动播放")
        self.auto_play.setStyleSheet("""
            QCheckBox {
                color: #cccccc;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 1px solid #555555;
                background: #252525;
            }
            QCheckBox::indicator:checked {
                background: #4CAF50;
                border: 1px solid #45a049;
            }
            QCheckBox::indicator:hover {
                border: 1px solid #4CAF50;
            }
        """)
        play_controls.addWidget(self.auto_play)
        
        right_layout.addLayout(play_controls)
        
        # 时间显示
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(self.time_label)
        
        # 速度控制
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("速度:"))
        
        # 添加速度滑动条
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setMinimum(10)  # 最小速度 0.1
        self.speed_slider.setMaximum(1000)  # 最大速度 10.0
        self.speed_slider.setValue(100)  # 默认速度 1.0
        self.speed_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.speed_slider.setTickInterval(10)
        self.speed_slider.valueChanged.connect(self.update_speed_label)
        self.speed_slider.sliderPressed.connect(self.on_slider_pressed)
        self.speed_slider.sliderReleased.connect(self.on_slider_released)
        speed_layout.addWidget(self.speed_slider)
        
        self.speed_input = SpeedInput()
        self.speed_input.setText("1.0")
        self.speed_input.textChanged.connect(self.update_speed_from_input)
        speed_layout.addWidget(self.speed_input)
        right_layout.addLayout(speed_layout)
        
        # 快捷键设置
        hotkey_layout = QGridLayout()
        hotkey_layout.addWidget(QLabel("暂停:"), 0, 0)
        self.hotkey_edits["pause"] = HotkeyEdit("F10")
        hotkey_layout.addWidget(self.hotkey_edits["pause"], 0, 1)
        
        hotkey_layout.addWidget(QLabel("停止:"), 1, 0)
        self.hotkey_edits["stop"] = HotkeyEdit("F11")
        hotkey_layout.addWidget(self.hotkey_edits["stop"], 1, 1)
        right_layout.addLayout(hotkey_layout)
        
        # 延时设置
        delay_layout = QHBoxLayout()
        self.delay_checkbox = QCheckBox("启用按键延时")
        self.delay_checkbox.setStyleSheet("""
            QCheckBox {
                color: #cccccc;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 1px solid #555555;
                background: #252525;
            }
            QCheckBox::indicator:checked {
                background: #4CAF50;
                border: 1px solid #45a049;
            }
            QCheckBox::indicator:hover {
                border: 1px solid #4CAF50;
            }
        """)
        self.delay_checkbox.setChecked(self.delay_enabled)
        self.delay_checkbox.stateChanged.connect(self.toggle_delay)
        
        self.delay_min_input = QLineEdit(str(self.delay_min))
        self.delay_min_input.setFixedWidth(50)
        self.delay_max_input = QLineEdit(str(self.delay_max))
        self.delay_max_input.setFixedWidth(50)
        
        delay_layout.addWidget(self.delay_checkbox)
        delay_layout.addWidget(QLabel("下限(ms):"))
        delay_layout.addWidget(self.delay_min_input)
        delay_layout.addWidget(QLabel("上限(ms):"))
        delay_layout.addWidget(self.delay_max_input)
        
        right_layout.addLayout(delay_layout)
        
        save_button = QPushButton("保存设置")
        save_button.clicked.connect(self.save_delay_settings)
        right_layout.addWidget(save_button)
        
        # 添加弹性空间
        right_layout.addStretch()
        
        # 曲谱信息显示区域（移到底部）
        info_group = QWidget()
        info_layout = QGridLayout(info_group)
        
        self.song_name_label = QLabel("曲名: -")
        self.author_label = QLabel("作者: -")
        self.bpm_label = QLabel("BPM: -")
        self.duration_label = QLabel("时长: -")
        self.note_count_label = QLabel("按键数: -")
        
        # 设置标签样式
        info_style = """
            QLabel {
                color: #cccccc;
                padding: 2px;
                background-color: #2d2d2d;
                border-radius: 4px;
            }
        """
        for label in [self.song_name_label, self.author_label, self.bpm_label, 
                     self.duration_label, self.note_count_label]:
            label.setStyleSheet(info_style)
            label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        info_layout.addWidget(self.song_name_label, 0, 0)
        info_layout.addWidget(self.author_label, 1, 0)
        info_layout.addWidget(self.bpm_label, 2, 0)
        info_layout.addWidget(self.duration_label, 3, 0)
        info_layout.addWidget(self.note_count_label, 4, 0)
        
        right_layout.addWidget(info_group)
        
        layout.addWidget(right_panel, stretch=1)

    def _update_ui(self):
        if self.play_thread and self.play_thread.isRunning():
            pass

    def on_tab_changed(self, index):
        if index == 2:
            self.open_score_folder()
            self.sender().setCurrentIndex(0)

    def setup_log_window(self):
        log_dock = QDockWidget("日志", self)
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        
        clear_log_btn = QPushButton("清空日志")
        clear_log_btn.clicked.connect(self.clear_log)
        log_layout.addWidget(clear_log_btn)
        
        self.log_widget = QListWidget()
        log_layout.addWidget(self.log_widget)
        
        log_dock.setWidget(log_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, log_dock)

    def setup_hotkeys(self):
        self.hotkey_edits["pause"].setObjectName("pause")
        self.hotkey_edits["stop"].setObjectName("stop")
        
        for action, key in self.current_hotkeys.items():
            if action in self.hotkey_edits:
                self.hotkey_edits[action].setText(key)

    def load_song_list(self):
        songs_folder = "score/score/"
        if os.path.exists(songs_folder):
            songs = [f.replace('.json', '') for f in os.listdir(songs_folder) if f.endswith('.json')]
            self.song_list.addItems(sorted(songs))
        else:
            self.log("歌曲文件夹不存在")

    def load_favorites_list(self):
        self.favorites_list.clear()
        self.favorites_list.addItems(sorted(self.favorites))

    def filter_songs(self, text):
        for i in range(self.song_list.count()):
            item = self.song_list.item(i)
            if item:
                item.setHidden(text.lower() not in item.text().lower())

    def load_song(self, item):
        song_name = item.text()
        
        if song_name in self._song_cache:
            self.current_song_data = self._song_cache[song_name]
            self.update_song_info(self.current_song_data, song_name)
            self.log(f"从缓存加载: {song_name}")
            return
            
        file_path = f"score/score/{song_name}.json"
        try:
            song_data = load_json(file_path)
            if not song_data or "songNotes" not in song_data:
                self.log("加载歌曲失败")
                return
                
            self._song_cache[song_name] = song_data
            self.current_song_data = song_data
            self._current_song = song_name
            
            # 更新曲谱信息显示
            self.update_song_info(song_data, song_name)
            
            notes = song_data["songNotes"]
            if notes:
                if len(notes) > 1:
                    self.total_duration = (notes[-1]['time'] - notes[0]['time']) / 1000
                else:
                    self.total_duration = 0

                total_minutes = int(self.total_duration // 60)
                total_seconds = int(self.total_duration % 60)
                self.time_label.setText(f"00:00 / {total_minutes:02}:{total_seconds:02}")
            else:
                self.log("曲谱中没有音符数据")
            
            self.log(f"已加载: {song_name}")
            
        except Exception as e:
            self.log(f"加载歌曲出错: {str(e)}")

    def update_song_info(self, song_data, file_name):
        """更新曲谱信息显示"""
        real_name = song_data.get("name", file_name)
        author = song_data.get("author", "未知")
        bpm = song_data.get("bpm", "未知")
        notes = song_data.get("songNotes", [])
        
        duration = (notes[-1]['time'] - notes[0]['time']) / 1000 if notes else 0
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        
        self.song_name_label.setText(f"曲名: {real_name}")
        self.author_label.setText(f"作者: {author}")
        self.bpm_label.setText(f"BPM: {bpm}")
        self.duration_label.setText(f"时长: {minutes}分{seconds}秒")
        self.note_count_label.setText(f"按键数: {len(notes)}")

    def load_and_play_song(self, item):
        if item is None:
            self.log("未选择歌曲")
            return
        
        self.load_song(item)
        if self.current_song_data:
            if not self.check_sky_window():
                return
            self.start_playback()
            self.play_button.setText("暂停")

    def toggle_pause(self):
        # 如果有正在运行的播放线程，则处理暂停/继续
        if hasattr(self, 'play_thread') and self.play_thread and self.play_thread.isRunning():
            self.play_thread.toggle_pause()
            if self.play_thread.paused:
                self.play_button.setText("继续")
                self.log("演奏已暂停")
            else:
                if not self.check_sky_window():
                    self.play_thread.toggle_pause()
                    self.log("无法继续，未检测到游戏窗口")
                    return
                self.play_button.setText("暂停")
                self.log("演奏继续")
        else:
            # 直接开始播放当前选中的歌曲
            current_item = self.song_list.currentItem() or self.favorites_list.currentItem()
            if current_item:
                self.load_and_play_song(current_item)
            else:
                self.log("请先选择要播放的歌曲")

    def start_playback(self):
        if not self.current_song_data:
            self.log("没有加载歌曲")
            return
        
        try:
            speed = float(self.speed_input.text())
            self.log(f"启动播放线程，速度: {speed}")
            if self.delay_enabled:
                self.log(f"当前使用延时设置: {self.delay_min}ms - {self.delay_max}ms")
            self.play_thread = PlayThread(
                song_data=self.current_song_data, 
                speed=speed,
                delay_enabled=self.delay_enabled,
                delay_min=self.delay_min,
                delay_max=self.delay_max
            )
            
            self.play_thread.update_log.connect(self.log)
            self.play_thread.update_progress.connect(self.update_progress)
            self.play_thread.update_time.connect(self.update_time_label)
            self.play_thread.finished.connect(self.on_playback_finished)
            
            self.play_thread.start()
            self.play_button.setText("暂停")
            self.log("播放线程已启动")
        except Exception as e:
            self.log(f"播放出错: {str(e)}")

    def update_speed_label(self, value):
        speed = value / 100
        self.speed_input.setText(f"{speed:.1f}")

    def update_speed_from_input(self, text):
        try:
            speed = float(text)
            if 0.1 <= speed <= 10.0:
                self.speed_slider.setValue(int(speed * 100))
        except:
            pass

    def open_score_editor(self):
        self.log("Opening score editor")

    def log(self, message):
        if hasattr(self, 'log_widget'):
            self.log_widget.addItem(message)
            self.log_widget.scrollToBottom()

    def stop_playback(self):
        if self.play_thread and self.play_thread.isRunning():
            self.play_thread.stop()
            self.play_thread.wait()
            self.play_button.setText("开始")
            release_all_keys()
            self.log("演奏已停止")
            
            for timer in self.findChildren(QTimer):
                if timer != self.window_check_timer:
                    timer.stop()

    def toggle_pause(self):
        # 如果有正在运行的播放线程，则处理暂停/继续
        if hasattr(self, 'play_thread') and self.play_thread and self.play_thread.isRunning():
            self.play_thread.toggle_pause()
            if self.play_thread.paused:
                self.play_button.setText("继续")
                self.log("演奏已暂停")
            else:
                if not self.check_sky_window():
                    self.play_thread.toggle_pause()
                    self.log("无法继续，未检测到游戏窗口")
                    return
                self.play_button.setText("暂停")
                self.log("演奏继续")
        else:
            # 直接开始播放当前选中的歌曲
            current_item = self.song_list.currentItem() or self.favorites_list.currentItem()
            if current_item:
                self.load_and_play_song(current_item)
            else:
                self.log("请先选择要播放的歌曲")

    def on_playback_finished(self):
        self.play_button.setText("开始")
        
        if not self.play_thread.manual_stop:
            if self.auto_play.isChecked():
                if self.current_play_mode != "单曲循环":
                    QTimer.singleShot(5000, lambda: self.play_next_song(self.current_play_mode))
                    self.log("5秒后自动播放下一首...")
                else:
                    QTimer.singleShot(5000, lambda: self.load_and_play_song(self.song_list.currentItem()))
                    self.log("5秒后重新播放...")
            else:
                self.log("播放结束")

    def play_next_song(self, mode):
        if not self.auto_play.isChecked():
            return
        
        # 确定当前使用的列表和行号
        current_list = self.favorites_list if self.favorites_list.hasFocus() else self.song_list
        current_row = current_list.currentRow()
        if current_row == -1:  # 如果没有选中项，默认从第一行开始
            current_row = 0
        
        # 根据播放模式选择下一首歌
        if self.current_play_mode == "单曲循环":
            next_row = current_row
        elif self.current_play_mode == "列表循环":
            next_row = (current_row + 1) % current_list.count()
        else:  # 随机播放
            total_songs = current_list.count()
            if total_songs > 1:
                next_row = current_row
                while next_row == current_row:
                    next_row = random.randint(0, total_songs - 1)
            else:
                next_row = 0
        
        current_list.setCurrentRow(next_row)
        next_item = current_list.item(next_row)
        if next_item:
            self.log(f"即将播放: {next_item.text()}")
            if current_list == self.favorites_list:
                self.log("从收藏列表继续播放")
            else:
                self.log("从所有歌曲列表继续播放")
            self.load_and_play_song(next_item)

    def update_hotkey(self, action, new_key):
        if not new_key or new_key == self.current_hotkeys[action]:
            return
        
        try:
            keyboard.parse_hotkey(new_key)
            
            try:
                keyboard.remove_hotkey(self.current_hotkeys[action])
            except:
                pass
            
            self.current_hotkeys[action] = new_key
            
            if action == "pause":
                keyboard.add_hotkey(new_key, self.toggle_pause)
            elif action == "stop":
                keyboard.add_hotkey(new_key, self.stop_playback)
            
            self.log(f"已将{action}的快捷键置为: {new_key}")
            self.save_hotkey_settings()
        except Exception as e:
            self.log(f"快捷键设置失败: {str(e)}")
            self.hotkey_edits[action].setText(self.current_hotkeys[action])

    def save_hotkey_settings(self):
        try:
            with open(self.hotkey_settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_hotkeys, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log(f"保存快捷键设置失败: {str(e)}")

    def load_hotkey_settings(self):
        try:
            if os.path.exists(self.hotkey_settings_file):
                with open(self.hotkey_settings_file, 'r', encoding='utf-8') as f:
                    self.current_hotkeys = json.load(f)
        except Exception as e:
            self.log(f"加载快捷键设置失败: {str(e)}")

    def load_favorites(self):
        try:
            if os.path.exists(self.favorites_file):
                with open(self.favorites_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            if hasattr(self, 'log_widget'):
                self.log(f"加载收藏列表失败: {str(e)}")
            return []

    def save_favorites(self):
        try:
            with open(self.favorites_file, 'w', encoding='utf-8') as f:
                json.dump(self.favorites, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log(f"保存收藏列表失败: {str(e)}")

    def show_song_context_menu(self, position):
        menu = QMenu()
        item = self.song_list.itemAt(position)
        
        if item:
            song_name = item.text()
            if song_name not in self.favorites:
                add_action = menu.addAction("添加到收藏")
                if add_action:
                    add_action.triggered.connect(lambda: self.add_to_favorites(song_name))
            else:
                remove_action = menu.addAction("从收藏中移除")
                if remove_action:
                    remove_action.triggered.connect(lambda: self.remove_from_favorites(song_name))
            
            info_action = menu.addAction("查看曲谱信息")
            if info_action:
                info_action.triggered.connect(lambda: self.show_song_info(song_name))
        
        menu.exec(self.song_list.mapToGlobal(position))

    def show_song_info(self, song_name):
        """显示曲谱的详细信息"""
        file_path = f"score/score/{song_name}.json"
        song_data = load_json(file_path)
        
        if song_data:
            real_name = song_data.get("name", song_name)
            author = song_data.get("author", "未知")
            bpm = song_data.get("bpm", "未知")
            notes = song_data.get("songNotes", [])
            duration = (notes[-1]['time'] - notes[0]['time']) / 1000 if notes else 0
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            note_count = len(notes)
            
            info_message = (
                f"曲名: {real_name}\n"
                f"文件名: {song_name}\n"
                f"作者: {author}\n"
                f"BPM: {bpm}\n"
                f"时长: {minutes}分{seconds}秒\n"
                f"按键数量: {note_count}"
            )
            
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("曲谱信息")
            msg_box.setText(info_message)
            msg_box.setIcon(QMessageBox.Icon.Information)
            
            # 设置暗色主题样式
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #1e1e1e;
                    color: #ffffff;
                }
                QMessageBox QLabel {
                    color: #ffffff;
                }
                QPushButton {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    border: 1px solid #333333;
                    padding: 5px 15px;
                    border-radius: 3px;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #3d3d3d;
                    border: 1px solid #4CAF50;
                }
                QPushButton:pressed {
                    background-color: #4CAF50;
                }
            """)
            
            msg_box.exec()
        else:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("错误")
            msg_box.setText("无法加载曲谱信息")
            msg_box.setIcon(QMessageBox.Icon.Warning)
            
            # 设置错误提示的暗色主题样式
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #1e1e1e;
                    color: #ffffff;
                }
                QMessageBox QLabel {
                    color: #ffffff;
                }
                QPushButton {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    border: 1px solid #333333;
                    padding: 5px 15px;
                    border-radius: 3px;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #3d3d3d;
                    border: 1px solid #ff5252;
                }
                QPushButton:pressed {
                    background-color: #ff5252;
                }
            """)
            
            msg_box.exec()

    def show_favorites_context_menu(self, position):
        menu = QMenu()
        item = self.favorites_list.itemAt(position)
        
        if item:
            song_name = item.text()
            remove_action = menu.addAction("从收藏中移除")
            remove_action.triggered.connect(lambda: self.remove_from_favorites(song_name))
        
        menu.exec(self.favorites_list.mapToGlobal(position))

    def add_to_favorites(self, song_name):
        if song_name not in self.favorites:
            self.favorites.append(song_name)
            self.favorites_list.addItem(song_name)
            self.save_favorites()
            self.log(f"已将 {song_name} 添加到收藏")

    def remove_from_favorites(self, song_name):
        if song_name in self.favorites:
            self.favorites.remove(song_name)
            items = self.favorites_list.findItems(song_name, Qt.MatchFlag.MatchExactly)
            for item in items:
                self.favorites_list.takeItem(self.favorites_list.row(item))
            self.save_favorites()
            self.log(f"已将 {song_name} 从收藏中移除")

    def on_slider_pressed(self):
        self.is_dragging = True
        if self.play_thread and self.play_thread.isRunning():
            self.play_thread.toggle_pause()

    def on_slider_released(self):
        if self.is_dragging:
            self.is_dragging = False
            position = self.speed_slider.value() / 100.0  # 将滑动条值转换为速度值
            self.speed_input.setText(f"{position:.1f}")
            if self.play_thread and self.play_thread.isRunning():
                self.play_thread.toggle_pause()

    def update_progress_position(self, position):
        current_time = self.total_duration * (position / 100)
        current_minutes = int(current_time // 60)
        current_seconds = int(current_time % 60)
        total_minutes = int(self.total_duration // 60)
        total_seconds = int(self.total_duration % 60)
        self.time_label.setText(f"{current_minutes:02}:{current_seconds:02} / {total_minutes:02}:{total_seconds:02}")

    def clear_log(self):
        self.log_widget.clear()
        self.log("日志已清空")

    def check_sky_window(self):
        try:
            windows = gw.getWindowsWithTitle('Sky') + gw.getWindowsWithTitle('光·遇')
            sky_window = next((w for w in windows if w.title.strip() == 'Sky' or w.title.strip() == '光·遇'), None)
            
            if sky_window:
                try:
                    if sky_window.isMinimized:
                        sky_window.restore()
                    sky_window.activate()
                    return True
                except Exception as e:
                    self.log(f"激活游戏窗口失败: {str(e)}")
                    return False
            else:
                QMessageBox.warning(self, "警告", "未找到光遇窗口，请先打开光遇游戏")
                return False
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"检查游戏窗口时出错: {str(e)}")
            return False

    def register_global_hotkeys(self):
        try:
            keyboard.add_hotkey(self.current_hotkeys["pause"], self.toggle_pause)
            keyboard.add_hotkey(self.current_hotkeys["stop"], self.stop_playback)
            self.log("快捷键注册成功")
        except Exception as e:
            self.log(f"快捷键注册失败: {str(e)}")

    def check_window_focus(self):
        if self.play_thread and self.play_thread.isRunning() and not self.play_thread.paused:
            try:
                windows = gw.getWindowsWithTitle('Sky') + gw.getWindowsWithTitle('光·遇')
                sky_window = next((w for w in windows if w.title.strip() == 'Sky' or w.title.strip() == '光·遇'), None)
                
                if sky_window and not sky_window.isActive:
                    self.play_thread.toggle_pause()
                    self.play_button.setText("继续")
                    self.log("检测到光遇窗口失去焦点，自动暂停演奏")
                    
            except Exception as e:
                self.log(f"检查窗口焦点时出错: {str(e)}")

    def open_score_folder(self):
        folder_path = os.path.abspath("score/score")
        if os.path.exists(folder_path):
            os.startfile(folder_path)
        else:
            self.log("曲谱文件夹不存在")

    def toggle_delay(self, state):
        """切换按键延时状态"""
        # 使用 Qt.CheckState 来正确判断复选框状态
        self.delay_enabled = (state == Qt.CheckState.Checked.value)  # 添加 .value
        status = "开启" if self.delay_enabled else "关闭"
        self.log(f"按键延时已{status} - 范围: {self.delay_min}ms - {self.delay_max}ms")

    def save_delay_settings(self):
        try:
            self.delay_min = int(self.delay_min_input.text())
            self.delay_max = int(self.delay_max_input.text())
            with open('delay_settings.json', 'w', encoding='utf-8') as f:
                json.dump({
                    'enabled': self.delay_enabled,
                    'min': self.delay_min,
                    'max': self.delay_max
                }, f, ensure_ascii=False, indent=2)
            self.log(f"延时设置已保存 - 启用状态: {'开启' if self.delay_enabled else '关闭'}, 范围: {self.delay_min}ms - {self.delay_max}ms")
        except ValueError:
            self.log("请输入有效的延时值")

    def load_delay_settings(self):
        try:
            with open('delay_settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)
                self.delay_enabled = settings.get('enabled', False)
                self.delay_min = settings.get('min', 200)
                self.delay_max = settings.get('max', 500)
                self.delay_checkbox.setChecked(self.delay_enabled)
                self.delay_min_input.setText(str(self.delay_min))
                self.delay_max_input.setText(str(self.delay_max))
                self.log(f"已加载延时设置 - 启用状态: {'开启' if self.delay_enabled else '关闭'}, 范围: {self.delay_min}ms - {self.delay_max}ms")
        except FileNotFoundError:
            self.log("未找到延时设置文件，使用默认值")
        except Exception as e:
            self.log(f"加载延时设置失败: {str(e)}")

    def toggle_play_mode(self):
        """切换播放模式"""
        if self.current_play_mode == "单曲循环":
            self.current_play_mode = "列表循环"
        elif self.current_play_mode == "列表循环":
            self.current_play_mode = "随机播放"
        else:
            self.current_play_mode = "单曲循环"
        
        self.play_mode_button.setText(self.current_play_mode)
        self.log(f"播放模式切换为: {self.current_play_mode}")

    def update_time_label(self, current_time):
        current_minutes = int(current_time // 60)
        current_seconds = int(current_time % 60)
        total_minutes = int(self.total_duration // 60)
        total_seconds = int(self.total_duration % 60)
        self.time_label.setText(f"{current_minutes:02}:{current_seconds:02} / {total_minutes:02}:{total_seconds:02}")

    def update_progress(self, progress):
        """更新播放进度"""
        current_time = self.total_duration * progress
        current_minutes = int(current_time // 60)
        current_seconds = int(current_time % 60)
        total_minutes = int(self.total_duration // 60)
        total_seconds = int(self.total_duration % 60)
        self.time_label.setText(f"{current_minutes:02}:{current_seconds:02} / {total_minutes:02}:{total_seconds:02}")