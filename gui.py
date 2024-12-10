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
from config import LOCAL_VERSION  # 从 config.py 导入

def resource_path(relative_path):
    """获取资源文件的绝对路径"""
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

    def __init__(self, song_data, speed):
        super().__init__()
        self.song_data = song_data
        self.speed = speed
        self.stop_event = threading.Event()
        self.paused = False
        self.seek_position = 0
        self.initial_progress = 0

    def run(self):
        try:
            # 播放歌曲
            play_song(self.song_data, self.stop_event, self.speed, self, self.initial_progress)
            
        except Exception as e:
            self.update_log.emit(f"播放出错: {str(e)}")

    def stop(self):
        self.stop_event.set()

    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            release_all_keys()

    def log(self, message):
        self.update_log.emit(message)

    def update_play_progress(self, progress):
        self.update_progress.emit(progress)

class HotkeyEdit(QLineEdit):
    """自定义的快捷键输入框"""
    def __init__(self, default_key, parent=None):
        super().__init__(parent)
        self.default_key = default_key
        self.setReadOnly(True)
        self.setText(default_key)
        self.setPlaceholderText("点击输入快捷键...")
        self.setup_style()
        
    def mousePressEvent(self, event):
        """点击时显示提示"""
        super().mousePressEvent(event)
        self.setPlaceholderText("请按下新的快捷键...")
        
    def focusOutEvent(self, event):
        """失去焦点时恢复显示"""
        super().focusOutEvent(event)
        if not self.text():
            self.setText(self.default_key)
        self.setPlaceholderText("点击输入快捷键...")
        
    def keyPressEvent(self, event):
        """处理按键输入"""
        modifiers = event.modifiers()
        key = event.key()
        
        # 忽略单独的修饰键
        if key in (Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta):
            return
            
        # 创建组合键文本
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
            
        # 组合所有按键文本
        final_text = "+".join(key_sequence)
        
        if final_text:
            self.setText(final_text)
            self.clearFocus()
            # 设置成功样式
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
            
            # 如果父窗口存在,通知更新快捷键
            if self.parent() and hasattr(self.parent(), "update_hotkey"):
                self.parent().update_hotkey(self.objectName(), final_text)
    
    def restore_style(self):
        """恢复原始样式"""
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
        """重置为默认值"""
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
    """自定义的倍速输入框"""
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
        self.setGeometry(100, 100, 1000, 800)
        
        try:
            self.setWindowIcon(QIcon(resource_path("icon.ico")))
        except Exception as e:
            print(f"加载窗口图标失败: {str(e)}")
        
        # 设置窗口样式
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
                image: url(down_arrow.png);  /* 可选：添加下拉箭头图标 */
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
        
        # 初始化主布局
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # 初始化变量
        self.current_song_data = None
        self.play_thread = None
        self.current_hotkeys = {
            "pause": "F10",
            "stop": "F11"
        }
        self.hotkey_edits = {}
        
        # 使用缓存存储常用数据
        self._song_cache = {}
        self._current_song = None
        self._max_cache_size = 50
        
        # 初始化文件路径
        self.favorites_file = "favorites.json"
        self.hotkey_settings_file = "hotkey_settings.json"
        
        # 初始化延时设置属性
        self.delay_enabled = False
        self.delay_min = 200
        self.delay_max = 500
        
        # 设置界面 - 注意初始化顺序
        self.setup_main_interface()  # 主界面
        self.setup_log_window()  # 日志窗口
        
        # 加载设置和数据
        self.favorites = self.load_favorites()
        self.load_hotkey_settings()
        self.load_song_list()
        self.load_favorites_list()
        
        # 连接进度条的鼠标事件
        self.progress_bar.mousePressEvent = self.on_progress_click
        self.progress_bar.mouseMoveEvent = self.on_progress_drag
        
        # 使用定时器优化界面更新
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._update_ui)
        self._update_timer.start(100)  # 每100ms更新一次UI

        # 初始化快捷键
        self.setup_hotkeys()
        
        # 注册全局快捷键
        self.register_global_hotkeys()

        # 添加窗口检测定时器
        self.window_check_timer = QTimer()
        self.window_check_timer.timeout.connect(self.check_window_focus)
        self.window_check_timer.start(1000)  # 每秒检查一次

        self.progress_bar.installEventFilter(self)

        self.load_delay_settings()

    def setup_main_interface(self):
        """设置主界面"""
        main_interface = QWidget()
        main_layout = QVBoxLayout(main_interface)
        
        # 创建主标签页
        main_tab_widget = QTabWidget()
        
        # 添加播放界面
        play_tab = QWidget()
        play_layout = QHBoxLayout(play_tab)
        
        # 左侧面板
        self.setup_left_panel(play_layout)
        
        # 右侧面板
        self.setup_right_panel(play_layout)
        
        main_tab_widget.addTab(play_tab, "播放")
        
        # 添加关于标签页
        about_tab = QWidget()
        about_layout = QVBoxLayout(about_tab)
        about_layout.setContentsMargins(20, 20, 20, 20)  # 增加边距
        about_layout.setSpacing(10)  # 增加控件间距
        
        # 软件信息
        latest_version = fetch_latest_version()
        
        version_label = QLabel(f"当前版本: {LOCAL_VERSION}")
        latest_version_label = QLabel(f"最新版本: {latest_version}")
        author_label = QLabel("作者: Tloml-Starry")
        
        # 使用按钮代替标签
        homepage_button = QPushButton("项目主页")
        homepage_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        homepage_button.clicked.connect(lambda: webbrowser.open("https://github.com/Tloml-Starry/SkyAutoMusic"))
        
        feedback_button = QPushButton("BUG反馈&功能提议")
        feedback_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        feedback_button.clicked.connect(lambda: webbrowser.open("https://qm.qq.com/q/dWe60BFyE0"))
        
        # 将标签添加到布局中
        for widget in [version_label, latest_version_label, author_label]:
            widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            about_layout.addWidget(widget)
        
        # 创建水平布局用于按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)  # 增加按钮间距
        button_layout.addWidget(homepage_button)
        button_layout.addWidget(feedback_button)
        
        # 将按钮布局添加到关于布局中
        about_layout.addStretch()  # 添加弹性空间
        about_layout.addLayout(button_layout)
        about_layout.addStretch()  # 添加弹性空间
        
        main_tab_widget.addTab(about_tab, "关于")
        
        main_layout.addWidget(main_tab_widget)
        self.main_layout.addWidget(main_interface)

    def setup_left_panel(self, layout):
        """设置左侧面板"""
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)
        
        # 搜索框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索歌曲...")
        self.search_input.textChanged.connect(self.filter_songs)
        left_layout.addWidget(self.search_input)
        
        # 创建标签页
        tab_widget = QTabWidget()
        tab_widget.currentChanged.connect(self.on_tab_changed)  # 连接标签页切换事件
        
        # 歌曲列表标签页
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
        """设置右侧面板"""
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 5, 5, 5)
        right_layout.setSpacing(10)
        
        play_controls = QHBoxLayout()
        
        self.play_button = QPushButton("开始")
        self.play_button.clicked.connect(self.toggle_play)
        self.play_button.setFixedHeight(30)
        play_controls.addWidget(self.play_button)
        
        self.play_mode = QComboBox()
        self.play_mode.addItems(["单曲播放", "顺序播放", "随机播放"])
        self.play_mode.setFixedHeight(30)
        play_controls.addWidget(self.play_mode)
        
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
        
        speed_layout = QHBoxLayout()
        speed_label = QLabel("速度:")
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(10, 1000)
        self.speed_slider.setValue(100)
        self.speed_slider.valueChanged.connect(self.update_speed_label)
        
        self.speed_input = SpeedInput()
        self.speed_input.setText("1.0")
        
        speed_layout.addWidget(speed_label)
        speed_layout.addWidget(self.speed_slider)
        speed_layout.addWidget(self.speed_input)
        right_layout.addLayout(speed_layout)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setMouseTracking(True)
        self.progress_bar.mousePressEvent = self.on_progress_click
        self.progress_bar.mouseMoveEvent = self.on_progress_drag
        self.progress_bar.mouseReleaseEvent = self.on_progress_release
        self.is_dragging = False
        right_layout.addWidget(self.progress_bar)
        
        hotkey_layout = QGridLayout()
        hotkey_layout.addWidget(QLabel("暂停:"), 0, 0)
        self.hotkey_edits["pause"] = HotkeyEdit("F10")
        hotkey_layout.addWidget(self.hotkey_edits["pause"], 0, 1)
        
        hotkey_layout.addWidget(QLabel("停止:"), 1, 0)
        self.hotkey_edits["stop"] = HotkeyEdit("F11")
        hotkey_layout.addWidget(self.hotkey_edits["stop"], 1, 1)
        right_layout.addLayout(hotkey_layout)
        
        delay_layout = QHBoxLayout()
        self.delay_checkbox = QCheckBox("启用按键延时")
        self.delay_checkbox.setChecked(self.delay_enabled)
        self.delay_checkbox.stateChanged.connect(self.toggle_delay)
        
        self.delay_min_input = QLineEdit(str(self.delay_min))
        self.delay_max_input = QLineEdit(str(self.delay_max))
        
        delay_layout.addWidget(self.delay_checkbox)
        delay_layout.addWidget(QLabel("下限(ms):"))
        delay_layout.addWidget(self.delay_min_input)
        delay_layout.addWidget(QLabel("上限(ms):"))
        delay_layout.addWidget(self.delay_max_input)
        
        right_layout.addLayout(delay_layout)
        
        save_button = QPushButton("保存设置")
        save_button.clicked.connect(self.save_delay_settings)
        right_layout.addWidget(save_button)
        
        right_layout.addStretch()
        layout.addWidget(right_panel, stretch=1)

    def _update_ui(self):
        """定时更新UI状态"""
        if self.play_thread and self.play_thread.isRunning():
            pass

    def on_tab_changed(self, index):
        """处理标签页切换事件"""
        if index == 2:
            self.open_score_folder()
            self.sender().setCurrentIndex(0)

    def setup_log_window(self):
        """设置日志窗口"""
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
        """设置快捷键"""
        self.hotkey_edits["pause"].setObjectName("pause")
        self.hotkey_edits["stop"].setObjectName("stop")
        
        for action, key in self.current_hotkeys.items():
            if action in self.hotkey_edits:
                self.hotkey_edits[action].setText(key)

    def load_song_list(self):
        """加载歌曲列表"""
        songs_folder = "score/score/"
        if os.path.exists(songs_folder):
            songs = [f.replace('.json', '') for f in os.listdir(songs_folder) if f.endswith('.json')]
            self.song_list.addItems(sorted(songs))
        else:
            self.log("歌曲文件夹不存在")

    def load_favorites_list(self):
        """加载收藏列表"""
        self.favorites_list.clear()
        self.favorites_list.addItems(sorted(self.favorites))

    def filter_songs(self, text):
        """过滤歌曲列表"""
        for i in range(self.song_list.count()):
            item = self.song_list.item(i)
            if item:
                item.setHidden(text.lower() not in item.text().lower())

    def load_song(self, item):
        """只加载歌曲，不播放"""
        song_name = item.text()
        
        if song_name in self._song_cache:
            self.current_song_data = self._song_cache[song_name]
            self.log(f"从缓存加载: {song_name}")
            return
            
        file_path = f"score/score/{song_name}.json"
        try:
            song_data = load_json(file_path)
            if not song_data:
                self.log("加载歌曲失败")
                return
                
            self._song_cache[song_name] = song_data
            self.current_song_data = song_data
            self._current_song = song_name
            
            self.log(f"已加载: {song_name}")
            
        except Exception as e:
            self.log(f"加载歌曲出错: {str(e)}")

    def load_and_play_song(self, item):
        """加载并播放歌曲"""
        self.load_song(item)
        if self.current_song_data:
            if not self.check_sky_window():
                return
            self.start_playback()
            self.play_button.setText("停止")

    def toggle_play(self):
        """切换播放状态"""
        if self.play_thread and self.play_thread.isRunning():
            self.stop_playback()
            self.play_button.setText("开始")
        else:
            if not self.current_song_data:
                self.log("请先选择一首歌曲")
                return
            
            if not self.check_sky_window():
                return
            
            self.start_playback()
            self.play_button.setText("停止")

    def start_playback(self):
        """开始播放"""
        if not self.current_song_data:
            self.log("没有加载歌曲")
            return
        
        try:
            speed = float(self.speed_input.text())
            self.play_thread = PlayThread(self.current_song_data, speed)
            
            if hasattr(self, 'target_progress'):
                progress = int(self.target_progress)
                self.play_thread.seek_position = progress
                self.play_thread.initial_progress = progress
                self.progress_bar.setValue(progress)
                delattr(self, 'target_progress')
                self.log(f"从 {progress}% 处开始播放")
            
            self.play_thread.update_log.connect(self.log)
            self.play_thread.update_progress.connect(lambda p: self.progress_bar.setValue(int(p)))
            self.play_thread.finished.connect(self.on_playback_finished)
            self.play_thread.start()
            self.play_button.setText("停止")
        except Exception as e:
            self.log(f"播放出错: {str(e)}")

    def stop_playback(self):
        """停止播放"""
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
        """切换暂停状态"""
        if self.play_thread and self.play_thread.isRunning():
            self.play_thread.toggle_pause()
            if not self.play_thread.paused:
                if not self.check_sky_window():
                    self.play_thread.toggle_pause()
                    return
            status = "暂停" if self.play_thread.paused else "继续"
            self.log(f"演奏{status}")
        elif hasattr(self, 'target_progress'):
            if self.check_sky_window():
                self.start_playback()
                self.play_button.setText("停止")

    def on_playback_finished(self):
        """播放结束的处理"""
        self.play_button.setText("开始")
        self.progress_bar.setValue(0)
        
        if self.auto_play.isChecked():
            current_mode = self.play_mode.currentText()
            if current_mode != "单曲播放":
                QTimer.singleShot(5000, lambda: self.play_next_song(current_mode))
                self.log("5秒后自动播放下一首...")
        else:
            self.log("播放结束")

    def play_next_song(self, mode):
        """播放下一首歌"""
        if not self.auto_play.isChecked():
            return
        
        if self.current_song_data:
            current_song = self._current_song
            if (current_song in self.favorites) and (self.favorites_list.count() > 0):
                items = self.favorites_list.findItems(current_song, Qt.MatchFlag.MatchExactly)
                if items:
                    current_list = self.favorites_list
                    current_row = self.favorites_list.row(items[0])
                else:
                    current_list = self.song_list
                    items = self.song_list.findItems(current_song, Qt.MatchFlag.MatchExactly)
                    current_row = self.song_list.row(items[0]) if items else 0
            else:
                current_list = self.song_list
                items = self.song_list.findItems(current_song, Qt.MatchFlag.MatchExactly)
                current_row = self.song_list.row(items[0]) if items else 0
        else:
            current_list = self.song_list
            current_row = 0
        
        if mode == "顺序播放":
            next_row = (current_row + 1) % current_list.count()
        else:
            next_row = current_row
            while next_row == current_row and current_list.count() > 1:
                next_row = random.randint(0, current_list.count() - 1)
        
        current_list.setCurrentRow(next_row)
        next_item = current_list.item(next_row)
        if next_item:
            self.log(f"即将播放: {next_item.text()}")
            if current_list == self.favorites_list:
                self.log("从收藏列表继续播放")
            else:
                self.log("从所有歌曲列表继续播放")
            self.load_and_play_song(next_item)

    def update_speed_label(self, value):
        """更新速度标签"""
        speed = value / 100
        self.speed_input.setText(f"{speed:.1f}")

    def update_speed_from_input(self, text):
        """从输入框更新速度"""
        try:
            speed = float(text)
            if 0.1 <= speed <= 10.0:
                self.speed_slider.setValue(int(speed * 100))
        except:
            pass

    def open_score_editor(self):
        self.log("Opening score editor")

    def log(self, message):
        """记录日志"""
        if hasattr(self, 'log_widget'):
            self.log_widget.addItem(message)
            self.log_widget.scrollToBottom()

    def stop_playback(self):
        """停止播放"""
        if self.play_thread and self.play_thread.isRunning():
            self.play_thread.stop()
            self.play_thread.wait()
            self.play_button.setText("开始")
            release_all_keys()
            self.log("演奏已停止")

    def update_hotkey(self, action, new_key):
        """更新快捷键设置"""
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
            
            self.log(f"已将{action}的快捷键设置为: {new_key}")
            self.save_hotkey_settings()
        except Exception as e:
            self.log(f"快捷键设置失败: {str(e)}")
            self.hotkey_edits[action].setText(self.current_hotkeys[action])

    def save_hotkey_settings(self):
        """保存快捷键设置到文件"""
        try:
            with open(self.hotkey_settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_hotkeys, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log(f"保存快捷键设置失败: {str(e)}")

    def load_hotkey_settings(self):
        """从文件加载快捷键设置"""
        try:
            if os.path.exists(self.hotkey_settings_file):
                with open(self.hotkey_settings_file, 'r', encoding='utf-8') as f:
                    self.current_hotkeys = json.load(f)
        except Exception as e:
            self.log(f"加载快捷键设置失败: {str(e)}")

    def load_favorites(self):
        """加载收藏列表"""
        try:
            if os.path.exists(self.favorites_file):
                with open(self.favorites_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            if hasattr(self, 'log_widget'):  # 检查是否已初始化日志窗口
                self.log(f"加载收藏列表失败: {str(e)}")
            return []

    def save_favorites(self):
        """保存收藏列表"""
        try:
            with open(self.favorites_file, 'w', encoding='utf-8') as f:
                json.dump(self.favorites, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log(f"保存收藏列表失败: {str(e)}")

    def show_song_context_menu(self, position):
        """显示歌曲列表的右键菜单"""
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
        
        menu.exec(self.song_list.mapToGlobal(position))

    def show_favorites_context_menu(self, position):
        """显示收藏列表的右键菜单"""
        menu = QMenu()
        item = self.favorites_list.itemAt(position)
        
        if item:
            song_name = item.text()
            remove_action = menu.addAction("从收藏中移除")
            remove_action.triggered.connect(lambda: self.remove_from_favorites(song_name))
        
        menu.exec(self.favorites_list.mapToGlobal(position))

    def add_to_favorites(self, song_name):
        """添加歌曲到收藏"""
        if song_name not in self.favorites:
            self.favorites.append(song_name)
            self.favorites_list.addItem(song_name)
            self.save_favorites()
            self.log(f"已将 {song_name} 添加到收藏")

    def remove_from_favorites(self, song_name):
        """从收藏中移除歌曲"""
        if song_name in self.favorites:
            self.favorites.remove(song_name)
            # 更新收藏列表显示
            items = self.favorites_list.findItems(song_name, Qt.MatchFlag.MatchExactly)
            for item in items:
                self.favorites_list.takeItem(self.favorites_list.row(item))
            self.save_favorites()
            self.log(f"已将 {song_name} 从收藏中移除")

    def on_progress_click(self, event):
        """处理进度条点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.update_progress_position(event)

    def on_progress_drag(self, event):
        """处理进度条拖动事件"""
        if self.is_dragging:
            self.update_progress_position(event)

    def on_progress_release(self, event):
        """处理鼠标释放事件"""
        if self.is_dragging:
            self.is_dragging = False
            # 只更新进度位置，不自动开始播放
            progress = self.progress_bar.value()
            if self.play_thread and self.play_thread.isRunning():
                # 如果正在播放，则停止播放
                self.stop_playback()
                self.play_button.setText("开始")
            # 保存目标进度位置
            self.target_progress = progress
            self.log(f"已设置播放位置: {progress}%")

    def update_progress_position(self, event):
        """更新进度条位置"""
        width = self.progress_bar.width()
        x = event.position().x()
        x = max(0, min(x, width))  # 确保 x 在有效范围内
        progress = (x / width) * 100
        self.progress_bar.setValue(int(progress))

    def clear_log(self):
        """清空日志"""
        self.log_widget.clear()
        self.log("日志已清空")

    def check_sky_window(self):
        """检查光遇窗口是否存在"""
        try:
            windows = gw.getWindowsWithTitle('Sky') + gw.getWindowsWithTitle('光·遇')
            sky_window = next((w for w in windows if w.title.strip() == 'Sky' or w.title.strip() == '光·遇'), None)
            
            if sky_window:
                try:
                    # 确保窗口不是最小化状态
                    if sky_window.isMinimized:
                        sky_window.restore()
                    # 只激活窗口，不最大化
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
        """注册全局快捷键"""
        try:
            keyboard.add_hotkey(self.current_hotkeys["pause"], self.toggle_pause)
            keyboard.add_hotkey(self.current_hotkeys["stop"], self.stop_playback)
            self.log("快捷键注册成功")
        except Exception as e:
            self.log(f"快捷键注册失败: {str(e)}")

    def check_window_focus(self):
        """检查光遇窗口是否保持焦点"""
        if self.play_thread and self.play_thread.isRunning() and not self.play_thread.paused:
            try:
                windows = gw.getWindowsWithTitle('Sky') + gw.getWindowsWithTitle('光·遇')
                sky_window = next((w for w in windows if w.title.strip() == 'Sky' or w.title.strip() == '光·遇'), None)
                
                if sky_window and not sky_window.isActive:
                    # 如果光遇窗口存在但不是活动窗口，自动暂停
                    self.play_thread.toggle_pause()
                    self.log("检测到光遇窗口失去焦点，自动暂停演奏")
                    
            except Exception as e:
                self.log(f"检查窗口焦点时出错: {str(e)}")

    def open_score_folder(self):
        """打开曲谱文件夹"""
        folder_path = os.path.abspath("score/score")
        if os.path.exists(folder_path):
            os.startfile(folder_path)  # 在Windows上使用os.startfile
        else:
            self.log("曲谱文件夹不存在")

    def eventFilter(self, source, event):
        if source == self.progress_bar:
            if event.type() == QEvent.Type.MouseButtonPress:
                self.on_progress_click(event)
            elif event.type() == QEvent.Type.MouseMove:
                self.on_progress_drag(event)
            elif event.type() == QEvent.Type.MouseButtonRelease:
                self.on_progress_release(event)
        return super().eventFilter(source, event)

    def toggle_delay(self, state):
        self.delay_enabled = state == Qt.CheckState.Checked

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
            self.log("延时设置已保存")
        except ValueError:
            self.log("请输入有效的延时值")

    def load_delay_settings(self):
        try:
            with open('delay_settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)
                self.delay_enabled = settings.get('enabled', False)
                self.delay_min = settings.get('min', 200)
                self.delay_max = settings.get('max', 500)
        except FileNotFoundError:
            self.log("未找到延时设置文件，使用默认值")
        except Exception as e:
            self.log(f"加载延时设置失败: {str(e)}")