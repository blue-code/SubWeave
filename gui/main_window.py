"""
Main Application Window
Main window with video player, controls, and menus.
"""
from PySide6 import QtWidgets, QtCore, QtGui
from pathlib import Path
import logging

from player.player_widget import PlayerWidget
from subtitle.subtitle_pipeline import SubtitlePipeline
from gui.progress_dialog import ProgressDialog, WorkerThread
from gui.playlist_widget import PlaylistWidget
from utils.file_utils import move_to_trash, format_duration
from utils.video_editor import VideoEditor, VideoMarker
from core.config import get_config


class MainWindow(QtWidgets.QMainWindow):
    """Main application window."""

    def __init__(self):
        """Initialize main window."""
        super().__init__()

        self.config = get_config()
        self.subtitle_pipeline = SubtitlePipeline()
        self.current_video_path = None
        self.current_subtitle_path = None
        self.worker_thread = None

        # Enable drag and drop
        self.setAcceptDrops(True)

        self._setup_ui()
        self._setup_menu()
        self._setup_shortcuts()
        self._load_settings()

        logging.info("MainWindow initialized")

    def _setup_ui(self):
        """Setup user interface."""
        # Set window properties
        self.setWindowTitle("SubWeave - Japanese to Korean Subtitle Generator")

        ui_config = self.config.get('ui')
        self.resize(
            ui_config.get('window_width', 1280),
            ui_config.get('window_height', 720)
        )

        # Apply modern window styling
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #fafafa, stop:1 #f0f0f0);
            }
            QMenuBar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f5f5f5);
                border-bottom: 1px solid #d0d0d0;
                padding: 4px;
            }
            QMenuBar::item {
                padding: 6px 12px;
                background: transparent;
                border-radius: 4px;
            }
            QMenuBar::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e8f2ff, stop:1 #d0e8ff);
            }
            QMenu {
                background: white;
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 24px 6px 12px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f0f8ff, stop:1 #e0f0ff);
                color: #333333;
            }
            QStatusBar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e8e8e8, stop:1 #d8d8d8);
                border-top: 1px solid #c0c0c0;
                color: #555555;
                font-weight: 500;
            }
            QSplitter::handle {
                background: #d0d0d0;
                width: 1px;
            }
            QSplitter::handle:hover {
                background: #4a90e2;
            }
        """)

        # Central widget with splitter
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Splitter for player and playlist
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)

        # Left side: Player area
        player_container = QtWidgets.QWidget()
        player_layout = QtWidgets.QVBoxLayout(player_container)
        player_layout.setContentsMargins(0, 0, 0, 0)

        # Player widget
        try:
            self.player = PlayerWidget(self)
            self.player.error_occurred.connect(self._on_player_error)
            self.player.time_position_changed.connect(self._on_position_changed)
            self.player.duration_changed.connect(self._on_duration_changed)
            self.player.playback_ended.connect(self._on_playback_ended)
            player_layout.addWidget(self.player, stretch=1)
        except Exception as e:
            logging.error(f"Failed to create player: {e}")
            error_label = QtWidgets.QLabel(f"Failed to initialize player:\n{e}")
            error_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            player_layout.addWidget(error_label, stretch=1)
            self.player = None

        # Control panel
        control_panel = self._create_control_panel()
        player_layout.addWidget(control_panel)

        # Right side: Playlist
        self.playlist = PlaylistWidget(self)
        self.playlist.video_selected.connect(self._load_video)
        self.playlist.setMinimumWidth(250)
        self.playlist.setMaximumWidth(400)

        # Add to splitter
        self.splitter.addWidget(player_container)
        self.splitter.addWidget(self.playlist)
        self.splitter.setStretchFactor(0, 3)  # Player takes 75%
        self.splitter.setStretchFactor(1, 1)  # Playlist takes 25%

        main_layout.addWidget(self.splitter)

        # Status bar
        self.statusBar().showMessage("Ready")

    def _create_control_panel(self) -> QtWidgets.QWidget:
        """
        Create control panel widget.

        Returns:
            Control panel widget
        """
        panel = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout(panel)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        # Style for the panel
        panel.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f5f5f5, stop:1 #e8e8e8);
                border-top: 1px solid #d0d0d0;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f0f0f0);
                border: 1px solid #c0c0c0;
                border-radius: 4px;
                padding: 6px 12px;
                min-height: 28px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f0f8ff, stop:1 #e0f0ff);
                border: 1px solid #4a90e2;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #d0e8ff, stop:1 #b0d8ff);
            }
            QPushButton:disabled {
                background: #e0e0e0;
                color: #a0a0a0;
                border: 1px solid #d0d0d0;
            }
            QSlider::groove:horizontal {
                border: 1px solid #999;
                height: 6px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #d0d0d0, stop:1 #e8e8e8);
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #4a90e2);
                border: 1px solid #4a90e2;
                width: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #5aa0f2);
                border: 2px solid #4a90e2;
            }
            QLabel {
                color: #333333;
                font-weight: 500;
            }
        """)

        # Progress bar row
        progress_layout = QtWidgets.QHBoxLayout()
        progress_layout.setSpacing(10)

        # Time label (current)
        self.time_label = QtWidgets.QLabel("00:00 / 00:00")
        self.time_label.setFixedWidth(110)
        self.time_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        progress_layout.addWidget(self.time_label)

        # Position slider
        self.position_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.position_slider.setRange(0, 1000)
        self.position_slider.sliderMoved.connect(self._on_slider_moved)
        progress_layout.addWidget(self.position_slider, stretch=1)

        main_layout.addLayout(progress_layout)

        # Control buttons row
        controls_layout = QtWidgets.QHBoxLayout()
        controls_layout.setSpacing(8)

        # Playback control buttons
        playback_group = QtWidgets.QHBoxLayout()
        playback_group.setSpacing(6)

        # Get standard icons
        style = self.style()

        # Open file button
        self.open_button = QtWidgets.QPushButton()
        self.open_button.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DialogOpenButton))
        self.open_button.setIconSize(QtCore.QSize(28, 28))
        self.open_button.setFixedSize(50, 44)
        self.open_button.setToolTip("Open Video (Cmd+O)")
        self.open_button.clicked.connect(self._on_open_file)
        playback_group.addWidget(self.open_button)

        # Trash button
        self.trash_button = QtWidgets.QPushButton()
        self.trash_button.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_TrashIcon))
        self.trash_button.setIconSize(QtCore.QSize(28, 28))
        self.trash_button.setFixedSize(50, 44)
        self.trash_button.setToolTip("Move to Trash (Delete)")
        self.trash_button.clicked.connect(self._on_delete_file)
        playback_group.addWidget(self.trash_button)

        playback_group.addSpacing(10)

        # Previous button
        self.prev_button = QtWidgets.QPushButton()
        self.prev_button.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaSkipBackward))
        self.prev_button.setIconSize(QtCore.QSize(28, 28))
        self.prev_button.setFixedSize(50, 44)
        self.prev_button.setToolTip("Previous Video (P)")
        self.prev_button.clicked.connect(self._on_previous_video)
        playback_group.addWidget(self.prev_button)

        # Skip backward button
        self.skip_back_button = QtWidgets.QPushButton()
        self.skip_back_button.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaSeekBackward))
        self.skip_back_button.setIconSize(QtCore.QSize(28, 28))
        self.skip_back_button.setFixedSize(50, 44)
        self.skip_back_button.setToolTip("Skip Backward 5s (←)")
        self.skip_back_button.clicked.connect(lambda: self._seek_relative(-5))
        playback_group.addWidget(self.skip_back_button)

        # Play/Pause button (larger)
        self.play_button = QtWidgets.QPushButton()
        self.play_button.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaPlay))
        self.play_button.setIconSize(QtCore.QSize(32, 32))
        self.play_button.setFixedSize(60, 44)
        self.play_button.setToolTip("Play/Pause (Space)")
        self.play_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5aa0f2, stop:1 #4a90e2);
                border: 1px solid #3a80d2;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6ab0ff, stop:1 #5aa0f2);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a90e2, stop:1 #3a80d2);
            }
        """)
        self.play_button.clicked.connect(self._on_play_pause)
        playback_group.addWidget(self.play_button)

        # Stop button
        self.stop_button = QtWidgets.QPushButton()
        self.stop_button.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaStop))
        self.stop_button.setIconSize(QtCore.QSize(28, 28))
        self.stop_button.setFixedSize(50, 44)
        self.stop_button.setToolTip("Stop (Ctrl+.)")
        self.stop_button.clicked.connect(self._on_stop)
        playback_group.addWidget(self.stop_button)

        # Skip forward button
        self.skip_forward_button = QtWidgets.QPushButton()
        self.skip_forward_button.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaSeekForward))
        self.skip_forward_button.setIconSize(QtCore.QSize(28, 28))
        self.skip_forward_button.setFixedSize(50, 44)
        self.skip_forward_button.setToolTip("Skip Forward 5s (→)")
        self.skip_forward_button.clicked.connect(lambda: self._seek_relative(5))
        playback_group.addWidget(self.skip_forward_button)

        # Next button
        self.next_button = QtWidgets.QPushButton()
        self.next_button.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaSkipForward))
        self.next_button.setIconSize(QtCore.QSize(28, 28))
        self.next_button.setFixedSize(50, 44)
        self.next_button.setToolTip("Next Video (N)")
        self.next_button.clicked.connect(self._on_next_video)
        playback_group.addWidget(self.next_button)

        controls_layout.addLayout(playback_group)
        controls_layout.addSpacing(15)

        # Volume control
        volume_group = QtWidgets.QHBoxLayout()
        volume_group.setSpacing(6)

        self.volume_button = QtWidgets.QPushButton()
        self.volume_button.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaVolume))
        self.volume_button.setIconSize(QtCore.QSize(24, 24))
        self.volume_button.setFixedSize(44, 44)
        self.volume_button.setToolTip("Mute/Unmute (Ctrl+M)")
        self.volume_button.clicked.connect(self._on_toggle_mute)
        volume_group.addWidget(self.volume_button)

        self.volume_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(self.config.get('player.volume', 100))
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.setToolTip("Volume")
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        volume_group.addWidget(self.volume_slider)

        self.volume_label = QtWidgets.QLabel("100%")
        self.volume_label.setFixedWidth(40)
        self.volume_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        volume_group.addWidget(self.volume_label)

        controls_layout.addLayout(volume_group)
        controls_layout.addSpacing(15)

        # Additional controls
        extra_group = QtWidgets.QHBoxLayout()
        extra_group.setSpacing(6)

        # Generate subtitle button
        self.generate_subtitle_button = QtWidgets.QPushButton("Gen Sub")
        self.generate_subtitle_button.setFixedSize(80, 44)
        self.generate_subtitle_button.setToolTip("Generate Subtitles (G)")
        self.generate_subtitle_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #50c878, stop:1 #40b868);
                border: 1px solid #30a858;
                border-radius: 4px;
                color: white;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #60d888, stop:1 #50c878);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #40b868, stop:1 #30a858);
            }
            QPushButton:disabled {
                background: #e0e0e0;
                color: #a0a0a0;
                border: 1px solid #d0d0d0;
            }
        """)
        self.generate_subtitle_button.clicked.connect(self._on_generate_subtitles)
        extra_group.addWidget(self.generate_subtitle_button)

        extra_group.addSpacing(10)

        # Subtitle toggle button
        self.subtitle_button = QtWidgets.QPushButton("CC")
        self.subtitle_button.setFixedSize(44, 44)
        self.subtitle_button.setToolTip("Toggle Subtitles (S)")
        self.subtitle_button.setCheckable(True)
        self.subtitle_button.setChecked(False)
        self.subtitle_button.setStyleSheet("""
            QPushButton {
                font-size: 13px;
                font-weight: bold;
            }
        """)
        self.subtitle_button.clicked.connect(self._on_toggle_subtitles)
        self.subtitle_button.setEnabled(False)  # Disabled until subtitles are generated
        extra_group.addWidget(self.subtitle_button)

        # Subtitle size buttons
        self.subtitle_decrease_button = QtWidgets.QPushButton("A-")
        self.subtitle_decrease_button.setFixedSize(44, 44)
        self.subtitle_decrease_button.setToolTip("Decrease Subtitle Size (Ctrl+-)")
        self.subtitle_decrease_button.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                font-weight: bold;
            }
        """)
        self.subtitle_decrease_button.clicked.connect(self._on_decrease_subtitle_size)
        self.subtitle_decrease_button.setEnabled(False)  # Disabled until subtitles are generated
        extra_group.addWidget(self.subtitle_decrease_button)

        self.subtitle_increase_button = QtWidgets.QPushButton("A+")
        self.subtitle_increase_button.setFixedSize(44, 44)
        self.subtitle_increase_button.setToolTip("Increase Subtitle Size (Ctrl+=)")
        self.subtitle_increase_button.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                font-weight: bold;
            }
        """)
        self.subtitle_increase_button.clicked.connect(self._on_increase_subtitle_size)
        self.subtitle_increase_button.setEnabled(False)  # Disabled until subtitles are generated
        extra_group.addWidget(self.subtitle_increase_button)

        extra_group.addSpacing(10)

        # Playback speed
        self.speed_combo = QtWidgets.QComboBox()
        self.speed_combo.addItems(["0.5x", "0.75x", "1.0x", "1.25x", "1.5x", "2.0x"])
        self.speed_combo.setCurrentText("1.0x")
        self.speed_combo.setFixedWidth(80)
        self.speed_combo.setFixedHeight(44)
        self.speed_combo.setToolTip("Playback Speed")
        self.speed_combo.currentTextChanged.connect(self._on_speed_changed)
        extra_group.addWidget(self.speed_combo)

        extra_group.addSpacing(10)

        # Add marker button
        self.add_marker_button = QtWidgets.QPushButton("M+")
        self.add_marker_button.setFixedSize(44, 44)
        self.add_marker_button.setToolTip("Add Marker at Current Position (M)")
        self.add_marker_button.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                font-weight: bold;
            }
        """)
        self.add_marker_button.clicked.connect(self._on_add_marker)
        extra_group.addWidget(self.add_marker_button)

        # Remove marker button
        self.remove_marker_button = QtWidgets.QPushButton("M-")
        self.remove_marker_button.setFixedSize(44, 44)
        self.remove_marker_button.setToolTip("Remove Nearest Marker (Shift+M)")
        self.remove_marker_button.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                font-weight: bold;
            }
        """)
        self.remove_marker_button.clicked.connect(self._on_remove_marker)
        extra_group.addWidget(self.remove_marker_button)

        # Split video button
        self.split_video_button = QtWidgets.QPushButton("Split")
        self.split_video_button.setFixedSize(60, 44)
        self.split_video_button.setToolTip("Split Video at Markers (Ctrl+K)")
        self.split_video_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff9a56, stop:1 #ff7b29);
                border: 1px solid #ff6a19;
                border-radius: 4px;
                color: white;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffaa66, stop:1 #ff8b39);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff8a46, stop:1 #ff6b19);
            }
            QPushButton:disabled {
                background: #e0e0e0;
                color: #a0a0a0;
                border: 1px solid #d0d0d0;
            }
        """)
        self.split_video_button.clicked.connect(self._on_split_video)
        extra_group.addWidget(self.split_video_button)

        extra_group.addSpacing(10)

        # Fullscreen button
        self.fullscreen_button = QtWidgets.QPushButton()
        self.fullscreen_button.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_TitleBarMaxButton))
        self.fullscreen_button.setIconSize(QtCore.QSize(24, 24))
        self.fullscreen_button.setFixedSize(44, 44)
        self.fullscreen_button.setToolTip("Toggle Fullscreen (F)")
        self.fullscreen_button.clicked.connect(self._on_toggle_fullscreen)
        extra_group.addWidget(self.fullscreen_button)

        controls_layout.addLayout(extra_group)
        controls_layout.addStretch()

        main_layout.addLayout(controls_layout)

        # Initialize mute state
        self._is_muted = False
        self._volume_before_mute = 100

        return panel

    def _setup_menu(self):
        """Setup menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        open_action = file_menu.addAction("Open Video...")
        open_action.setShortcut(QtGui.QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._on_open_file)

        file_menu.addSeparator()

        delete_action = file_menu.addAction("Move to Trash")
        delete_action.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key.Key_Delete))
        delete_action.triggered.connect(self._on_delete_file)

        file_menu.addSeparator()

        quit_action = file_menu.addAction("Quit")
        quit_action.setShortcut(QtGui.QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)

        # Playback menu
        playback_menu = menubar.addMenu("Playback")

        play_pause_action = playback_menu.addAction("Play/Pause")
        play_pause_action.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key.Key_Space))
        play_pause_action.triggered.connect(self._on_play_pause)

        seek_forward_action = playback_menu.addAction("Seek Forward")
        seek_forward_action.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key.Key_Right))
        seek_forward_action.triggered.connect(lambda: self._seek_relative(5))

        seek_backward_action = playback_menu.addAction("Seek Backward")
        seek_backward_action.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key.Key_Left))
        seek_backward_action.triggered.connect(lambda: self._seek_relative(-5))

        playback_menu.addSeparator()

        fullscreen_action = playback_menu.addAction("Toggle Fullscreen")
        fullscreen_action.setShortcut(QtGui.QKeySequence("F"))
        fullscreen_action.triggered.connect(self._on_toggle_fullscreen)

        # Subtitle menu
        subtitle_menu = menubar.addMenu("Subtitles")

        toggle_sub_action = subtitle_menu.addAction("Toggle Subtitles")
        toggle_sub_action.setShortcut(QtGui.QKeySequence("S"))
        toggle_sub_action.triggered.connect(self._on_toggle_subtitles)

        subtitle_menu.addSeparator()

        increase_size_action = subtitle_menu.addAction("Increase Size")
        increase_size_action.setShortcut(QtGui.QKeySequence("Ctrl+="))
        increase_size_action.triggered.connect(self._on_increase_subtitle_size)

        decrease_size_action = subtitle_menu.addAction("Decrease Size")
        decrease_size_action.setShortcut(QtGui.QKeySequence("Ctrl+-"))
        decrease_size_action.triggered.connect(self._on_decrease_subtitle_size)

        subtitle_menu.addSeparator()

        regenerate_action = subtitle_menu.addAction("Regenerate Subtitles")
        regenerate_action.triggered.connect(self._on_regenerate_subtitles)

        # Playlist menu
        playlist_menu = menubar.addMenu("Playlist")

        next_video_action = playlist_menu.addAction("Next Video")
        next_video_action.setShortcut(QtGui.QKeySequence("N"))
        next_video_action.triggered.connect(self._on_next_video)

        prev_video_action = playlist_menu.addAction("Previous Video")
        prev_video_action.setShortcut(QtGui.QKeySequence("P"))
        prev_video_action.triggered.connect(self._on_previous_video)

        playlist_menu.addSeparator()

        toggle_playlist_action = playlist_menu.addAction("Toggle Playlist")
        toggle_playlist_action.setShortcut(QtGui.QKeySequence("L"))
        toggle_playlist_action.triggered.connect(self._on_toggle_playlist)

        playlist_menu.addSeparator()

        clear_playlist_action = playlist_menu.addAction("Clear Playlist")
        clear_playlist_action.triggered.connect(lambda: self.playlist.clear_playlist())

    def _setup_shortcuts(self):
        """Setup additional keyboard shortcuts."""
        # Volume mute toggle
        mute_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+M"), self)
        mute_shortcut.activated.connect(self._on_toggle_mute)

        # Generate subtitles
        generate_shortcut = QtGui.QShortcut(QtGui.QKeySequence("G"), self)
        generate_shortcut.activated.connect(self._on_generate_subtitles)

        # Stop playback
        stop_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+."), self)
        stop_shortcut.activated.connect(self._on_stop)

        # Delete with Delete/Backspace keys
        delete_shortcut1 = QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key.Key_Delete), self)
        delete_shortcut1.activated.connect(self._on_delete_file)

        delete_shortcut2 = QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key.Key_Backspace), self)
        delete_shortcut2.activated.connect(self._on_delete_file)

        # Add marker
        add_marker_shortcut = QtGui.QShortcut(QtGui.QKeySequence("M"), self)
        add_marker_shortcut.activated.connect(self._on_add_marker)

        # Remove marker
        remove_marker_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Shift+M"), self)
        remove_marker_shortcut.activated.connect(self._on_remove_marker)

        # Split video
        split_video_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+K"), self)
        split_video_shortcut.activated.connect(self._on_split_video)

    def _load_settings(self):
        """Load settings from config."""
        if self.player:
            volume = self.config.get('player.volume', 100)
            self.player.set_volume(volume)

    def _on_open_file(self):
        """Handle open file action."""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Open Video File",
            "",
            "Video Files (*.mp4 *.mkv *.avi *.mov *.m4v *.webm);;All Files (*.*)"
        )

        if file_path:
            self._load_video(file_path)

    def _load_video(self, video_path: str):
        """
        Load and play video file.

        Args:
            video_path: Path to video file
        """
        if not self.player:
            QtWidgets.QMessageBox.critical(
                self,
                "Error",
                "Player not initialized"
            )
            return

        self.current_video_path = video_path
        self.statusBar().showMessage(f"Loading: {Path(video_path).name}")

        # Load playlist from directory
        self.playlist.load_directory(video_path)

        # Check for cached subtitles
        subtitle_path = self.subtitle_pipeline.get_cached_subtitle_path(video_path)

        if subtitle_path:
            # Use cached subtitles
            self.current_subtitle_path = subtitle_path
            self.player.load_file(video_path, subtitle_path)
            # Hide subtitles by default
            self.player.subtitle_label.hide()
            self.statusBar().showMessage(f"Playing: {Path(video_path).name} (cached subtitles)")

            # Enable subtitle controls
            self._enable_subtitle_controls()
            self.generate_subtitle_button.setText("Regen")
            self.generate_subtitle_button.setToolTip("Regenerate Subtitles (G)")
        else:
            # Load video without subtitles
            self.player.load_file(video_path)
            self.statusBar().showMessage(f"Playing: {Path(video_path).name} (no subtitles)")

            # Disable subtitle controls and enable generate button
            self._disable_subtitle_controls()
            self.generate_subtitle_button.setText("Gen Sub")
            self.generate_subtitle_button.setToolTip("Generate Subtitles (G)")
            self.generate_subtitle_button.setEnabled(True)

    def _generate_subtitles(self, video_path: str, use_cache: bool = True):
        """
        Generate subtitles for video.

        Args:
            video_path: Path to video file
            use_cache: Whether to use cache
        """
        # Create progress dialog
        progress_dialog = ProgressDialog(self)
        progress_dialog.set_title(f"Processing: {Path(video_path).name}")

        # Create worker thread
        self.worker_thread = WorkerThread(
            self.subtitle_pipeline,
            video_path,
            use_cache
        )

        # Connect signals
        self.worker_thread.progress_updated.connect(progress_dialog.update_progress)
        self.worker_thread.finished_success.connect(
            lambda path: self._on_subtitles_generated(path, video_path, progress_dialog)
        )
        self.worker_thread.finished_error.connect(
            lambda error: self._on_subtitle_error(error, progress_dialog)
        )
        progress_dialog.cancelled.connect(self.worker_thread.cancel)

        # Start generation
        self.worker_thread.start()
        progress_dialog.exec()

    def _on_subtitles_generated(self, subtitle_path: str, video_path: str, dialog: ProgressDialog):
        """Handle successful subtitle generation."""
        self.current_subtitle_path = subtitle_path

        if self.player:
            self.player.load_file(video_path, subtitle_path)
            # Hide subtitles by default
            self.player.subtitle_label.hide()

        # Enable subtitle controls
        self._enable_subtitle_controls()
        self.generate_subtitle_button.setText("Regen")
        self.generate_subtitle_button.setToolTip("Regenerate Subtitles (G)")

        dialog.accept()
        self.statusBar().showMessage(f"Subtitles generated: {Path(subtitle_path).name}")

        QtWidgets.QMessageBox.information(
            self,
            "Success",
            f"Subtitles generated successfully!\n\nSaved to: {subtitle_path}\n\nClick the CC button to show subtitles."
        )

    def _on_subtitle_error(self, error_message: str, dialog: ProgressDialog):
        """Handle subtitle generation error."""
        dialog.reject()
        self.statusBar().showMessage("Subtitle generation failed")

        QtWidgets.QMessageBox.critical(
            self,
            "Error",
            f"Failed to generate subtitles:\n\n{error_message}"
        )

    def _on_play_pause(self):
        """Handle play/pause action."""
        if self.player:
            self.player.toggle_pause()
            style = self.style()
            if self.player.is_playing():
                self.play_button.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaPause))
            else:
                self.play_button.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaPlay))

    def _on_stop(self):
        """Handle stop action."""
        if self.player:
            self.player.stop()
            style = self.style()
            self.play_button.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaPlay))
            self.position_slider.setValue(0)
            self.time_label.setText("00:00 / 00:00")

    def _on_toggle_mute(self):
        """Handle mute/unmute action."""
        if not self.player:
            return

        style = self.style()
        if self._is_muted:
            # Unmute
            self.volume_slider.setValue(self._volume_before_mute)
            self.player.set_volume(self._volume_before_mute)
            self.volume_button.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaVolume))
            self._is_muted = False
        else:
            # Mute
            self._volume_before_mute = self.volume_slider.value()
            self.volume_slider.setValue(0)
            self.player.set_volume(0)
            self.volume_button.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaVolumeMuted))
            self._is_muted = True

    def _on_speed_changed(self, speed_text: str):
        """Handle playback speed change."""
        if not self.player:
            return

        try:
            # Extract speed value (e.g., "1.5x" -> 1.5)
            speed = float(speed_text.replace('x', ''))
            self.player.set_playback_speed(speed)
            self.statusBar().showMessage(f"Playback speed: {speed_text}", 2000)
        except ValueError:
            logging.error(f"Invalid speed value: {speed_text}")

    def _on_slider_moved(self, position: int):
        """Handle slider movement."""
        if self.player:
            duration = self.player.get_duration()
            if duration > 0:
                time_pos = (position / 1000) * duration
                self.player.seek(time_pos, relative=False)

    def _on_position_changed(self, position: float):
        """Handle playback position change."""
        duration = self.player.get_duration() if self.player else 0

        if duration > 0:
            # Update slider
            slider_pos = int((position / duration) * 1000)
            self.position_slider.setValue(slider_pos)

            # Update time label
            pos_str = format_duration(position)
            dur_str = format_duration(duration)
            self.time_label.setText(f"{pos_str} / {dur_str}")

    def _on_duration_changed(self, duration: float):
        """Handle duration change."""
        logging.info(f"Duration: {duration:.2f}s")

    def _on_volume_changed(self, volume: int):
        """Handle volume change."""
        if self.player:
            self.player.set_volume(volume)
            self.config.set('player.volume', volume)

            # Update volume label
            self.volume_label.setText(f"{volume}%")

            # Update volume button icon based on level
            style = self.style()
            if volume == 0:
                self.volume_button.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaVolumeMuted))
                self._is_muted = True
            else:
                self.volume_button.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaVolume))
                self._is_muted = False

    def _seek_relative(self, seconds: float):
        """Seek relative to current position."""
        if self.player:
            self.player.seek(seconds, relative=True)

    def _on_toggle_fullscreen(self):
        """Handle fullscreen toggle."""
        if self.player:
            self.player.toggle_fullscreen()

    def _on_toggle_subtitles(self):
        """Handle subtitle toggle."""
        if self.player:
            self.player.toggle_subtitles()

    def _on_increase_subtitle_size(self):
        """Handle subtitle size increase."""
        if self.player:
            self.player.increase_subtitle_size()

    def _on_decrease_subtitle_size(self):
        """Handle subtitle size decrease."""
        if self.player:
            self.player.decrease_subtitle_size()

    def _on_generate_subtitles(self):
        """Handle generate/regenerate subtitles button click."""
        if not self.current_video_path:
            QtWidgets.QMessageBox.warning(
                self,
                "No Video",
                "Please open a video file first."
            )
            return

        # Check if subtitles already exist
        if self.current_subtitle_path:
            reply = QtWidgets.QMessageBox.question(
                self,
                "Regenerate Subtitles",
                "Subtitles already exist. Regenerate from scratch?",
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
            )

            if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                self._generate_subtitles(self.current_video_path, use_cache=False)
        else:
            # Generate new subtitles
            self._generate_subtitles(self.current_video_path, use_cache=True)

    def _on_regenerate_subtitles(self):
        """Handle regenerate subtitles action from menu."""
        if not self.current_video_path:
            QtWidgets.QMessageBox.warning(
                self,
                "No Video",
                "Please open a video file first."
            )
            return

        reply = QtWidgets.QMessageBox.question(
            self,
            "Regenerate Subtitles",
            "This will regenerate subtitles from scratch.\nContinue?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            self._generate_subtitles(self.current_video_path, use_cache=False)

    def _enable_subtitle_controls(self):
        """Enable subtitle controls when subtitles are available."""
        self.subtitle_button.setEnabled(True)
        self.subtitle_button.setChecked(False)  # Start with subtitles OFF
        self.subtitle_decrease_button.setEnabled(True)
        self.subtitle_increase_button.setEnabled(True)
        self.generate_subtitle_button.setEnabled(True)

    def _disable_subtitle_controls(self):
        """Disable subtitle controls when no subtitles are available."""
        self.subtitle_button.setEnabled(False)
        self.subtitle_button.setChecked(False)
        self.subtitle_decrease_button.setEnabled(False)
        self.subtitle_increase_button.setEnabled(False)

    def _on_delete_file(self):
        """Handle delete file action."""
        if not self.current_video_path:
            QtWidgets.QMessageBox.warning(
                self,
                "No Video",
                "No video file is currently loaded."
            )
            return

        # Stop playback
        if self.player:
            self.player.stop()

        # Get current playlist index before deletion
        current_index = self.playlist.current_index

        # Move to trash without confirmation
        if move_to_trash(self.current_video_path):
            self.statusBar().showMessage(f"Moved to trash: {Path(self.current_video_path).name}")

            # Remove from playlist
            if current_index >= 0:
                self.playlist.remove_video(current_index)

            # Play next video if available (after removal, same index points to next video)
            if 0 <= current_index < self.playlist.get_video_count():
                # Play video at same index (which is now the next video)
                next_video = self.playlist.videos[current_index]
                self.playlist.set_current_index(current_index)
                self._load_video(str(next_video))
            elif self.playlist.get_video_count() > 0:
                # Play last video if we deleted the last one
                last_index = self.playlist.get_video_count() - 1
                last_video = self.playlist.videos[last_index]
                self.playlist.set_current_index(last_index)
                self._load_video(str(last_video))
            else:
                # No more videos in playlist
                self.current_video_path = None
                self.current_subtitle_path = None
        else:
            QtWidgets.QMessageBox.critical(
                self,
                "Error",
                "Failed to move file to trash."
            )

    def _on_player_error(self, error_message: str):
        """Handle player error."""
        logging.error(f"Player error: {error_message}")
        self.statusBar().showMessage(f"Player error: {error_message}")

    def _on_playback_ended(self):
        """Handle playback ended."""
        logging.info("Playback ended")

        # Auto-play next video if enabled and available
        if self.config.get('player.auto_play_next', True) and self.playlist.has_next():
            logging.info("Auto-playing next video")
            self.playlist.play_next()

    def _on_next_video(self):
        """Play next video in playlist."""
        if self.playlist.has_next():
            self.playlist.play_next()
        else:
            self.statusBar().showMessage("No next video in playlist")

    def _on_previous_video(self):
        """Play previous video in playlist."""
        if self.playlist.has_previous():
            self.playlist.play_previous()
        else:
            self.statusBar().showMessage("No previous video in playlist")

    def _on_toggle_playlist(self):
        """Toggle playlist visibility."""
        is_visible = self.playlist.isVisible()
        self.playlist.setVisible(not is_visible)

        if not is_visible:
            self.statusBar().showMessage("Playlist shown")
        else:
            self.statusBar().showMessage("Playlist hidden")

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            for url in urls:
                file_path = url.toLocalFile()
                if file_path and Path(file_path).exists():
                    suffix = Path(file_path).suffix.lower()
                    if suffix in ['.mp4', '.mkv', '.avi', '.mov', '.m4v', '.webm']:
                        event.acceptProposedAction()
                        return
        event.ignore()

    def dropEvent(self, event: QtGui.QDropEvent):
        """Handle drop event."""
        urls = event.mimeData().urls()
        if not urls:
            event.ignore()
            return

        for url in urls:
            file_path = url.toLocalFile()
            logging.info(f"Dropped file: {file_path}")

            if not file_path:
                continue

            path_obj = Path(file_path)
            if not path_obj.exists():
                logging.warning(f"File does not exist: {file_path}")
                continue

            suffix = path_obj.suffix.lower()
            if suffix in ['.mp4', '.mkv', '.avi', '.mov', '.m4v', '.webm']:
                self._load_video(file_path)
                event.acceptProposedAction()
                return
            else:
                logging.warning(f"Unsupported file format: {suffix}")

        event.ignore()

    def _on_add_marker(self):
        """Handle add marker action."""
        if not self.player:
            return

        position = self.player.get_current_position()
        self.player.add_marker(position)

        markers = self.player.get_markers()
        self.statusBar().showMessage(f"Added marker at {format_duration(position)} ({len(markers)} markers total)")

    def _on_remove_marker(self):
        """Handle remove marker action."""
        if not self.player:
            return

        if self.player.remove_nearest_marker():
            markers = self.player.get_markers()
            self.statusBar().showMessage(f"Removed marker ({len(markers)} markers remaining)")
        else:
            self.statusBar().showMessage("No markers to remove")

    def _on_split_video(self):
        """Handle split video action."""
        if not self.current_video_path:
            QtWidgets.QMessageBox.warning(
                self,
                "No Video",
                "Please open a video file first."
            )
            return

        if not self.player:
            return

        markers = self.player.get_markers()

        if not markers:
            QtWidgets.QMessageBox.warning(
                self,
                "No Markers",
                "Please add at least one marker before splitting the video."
            )
            return

        # Confirm split
        reply = QtWidgets.QMessageBox.question(
            self,
            "Split Video",
            f"Split video at {len(markers)} marker(s)?\n\nThis will create {len(markers) + 1} video segments.",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )

        if reply != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        # Check if ffmpeg is installed
        if not VideoEditor.check_ffmpeg_installed():
            QtWidgets.QMessageBox.critical(
                self,
                "FFmpeg Not Found",
                "FFmpeg is not installed or not in PATH.\n\nPlease install FFmpeg to use video editing features."
            )
            return

        # Pause playback
        if self.player.is_playing():
            self.player.pause()

        # Create video markers
        video_markers = [VideoMarker(time_seconds=m, label="") for m in markers]

        try:
            self.statusBar().showMessage("Splitting video...")

            # Get output directory
            output_dir = Path(self.current_video_path).parent / f"{Path(self.current_video_path).stem}_split"

            # Split video
            output_files = VideoEditor.split_video_at_markers(
                input_path=self.current_video_path,
                markers=video_markers,
                output_dir=str(output_dir)
            )

            self.statusBar().showMessage(f"Video split completed: {len(output_files)} segments created")

            QtWidgets.QMessageBox.information(
                self,
                "Split Complete",
                f"Video split successfully!\n\nCreated {len(output_files)} segments in:\n{output_dir}"
            )

            # Clear markers
            self.player.clear_markers()
            self.statusBar().showMessage("Markers cleared after split")

        except Exception as e:
            logging.error(f"Failed to split video: {e}")
            QtWidgets.QMessageBox.critical(
                self,
                "Split Failed",
                f"Failed to split video:\n\n{str(e)}"
            )
            self.statusBar().showMessage("Video split failed")

    def closeEvent(self, event):
        """Handle window close event."""
        # Stop worker thread if running
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.cancel()
            self.worker_thread.wait()

        # Cleanup pipeline
        self.subtitle_pipeline.cleanup()

        # Save settings
        self.config.save_settings()

        event.accept()
