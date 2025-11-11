"""
Playlist Widget
Displays and manages video playlist.
"""
from PySide6 import QtWidgets, QtCore, QtGui
from pathlib import Path
from typing import List, Optional

from utils.file_utils import get_video_files, format_file_size, get_file_size_mb


class PlaylistWidget(QtWidgets.QWidget):
    """Playlist widget for managing video queue."""

    # Signals
    video_selected = QtCore.Signal(str)  # Emitted when user selects a video
    playlist_changed = QtCore.Signal()   # Emitted when playlist changes

    def __init__(self, parent=None):
        """
        Initialize playlist widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.videos: List[Path] = []
        self.current_index: int = -1
        self._setup_ui()

    def _setup_ui(self):
        """Setup user interface."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Apply modern styling to the widget
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #fafafa, stop:1 #f0f0f0);
                border-left: 1px solid #d0d0d0;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f0f0f0);
                border: 1px solid #c0c0c0;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: 500;
                min-height: 24px;
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
                background: #e8e8e8;
                color: #a0a0a0;
                border: 1px solid #d0d0d0;
            }
            QListWidget {
                background: white;
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                padding: 4px;
                outline: none;
            }
            QListWidget::item {
                border-radius: 4px;
                padding: 8px;
                margin: 2px;
            }
            QListWidget::item:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f5f9ff, stop:1 #e8f2ff);
            }
            QListWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6ab0ff, stop:1 #4a90e2);
                color: white;
                border: 1px solid #3a80d2;
            }
            QLabel {
                background: transparent;
                border: none;
            }
        """)

        # Header
        header_layout = QtWidgets.QHBoxLayout()
        header_layout.setSpacing(8)

        title_label = QtWidgets.QLabel("📋 Playlist")
        title_label.setStyleSheet("""
            font-weight: bold;
            font-size: 13px;
            color: #333333;
            padding: 4px 0px;
        """)
        header_layout.addWidget(title_label)

        self.count_label = QtWidgets.QLabel("0 videos")
        self.count_label.setStyleSheet("""
            color: #666666;
            font-size: 11px;
            padding: 4px 0px;
        """)
        header_layout.addWidget(self.count_label)

        header_layout.addStretch()

        # Clear button
        clear_btn = QtWidgets.QPushButton("✕ Clear")
        clear_btn.setFixedWidth(70)
        clear_btn.setToolTip("Clear all videos from playlist")
        clear_btn.clicked.connect(self.clear_playlist)
        header_layout.addWidget(clear_btn)

        layout.addLayout(header_layout)

        # List widget
        self.list_widget = QtWidgets.QListWidget()
        self.list_widget.setAlternatingRowColors(False)
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.list_widget.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.list_widget)

        # Controls
        controls_layout = QtWidgets.QHBoxLayout()
        controls_layout.setSpacing(6)

        self.prev_btn = QtWidgets.QPushButton("⏮ Previous")
        self.prev_btn.setToolTip("Play previous video (P)")
        self.prev_btn.clicked.connect(self.play_previous)
        controls_layout.addWidget(self.prev_btn)

        self.next_btn = QtWidgets.QPushButton("Next ⏭")
        self.next_btn.setToolTip("Play next video (N)")
        self.next_btn.clicked.connect(self.play_next)
        controls_layout.addWidget(self.next_btn)

        layout.addLayout(controls_layout)

        self._update_buttons()

    def load_directory(self, video_path: str):
        """
        Load all videos from the directory containing the given video.

        Args:
            video_path: Path to a video file
        """
        video_path_obj = Path(video_path)
        if not video_path_obj.exists():
            return

        # Get directory
        directory = video_path_obj.parent

        # Get all video files in directory
        video_files = get_video_files(str(directory))

        if not video_files:
            return

        # Sort by name
        video_files = sorted(video_files, key=lambda p: p.name.lower())

        # Clear existing playlist
        self.clear_playlist()

        # Add videos
        for video_file in video_files:
            self.add_video(str(video_file))

        # Set current video
        try:
            current_idx = video_files.index(video_path_obj)
            self.set_current_index(current_idx)
        except ValueError:
            # Video not in list, add it
            self.add_video(video_path)
            self.set_current_index(len(self.videos) - 1)

    def add_video(self, video_path: str):
        """
        Add video to playlist.

        Args:
            video_path: Path to video file
        """
        video_path_obj = Path(video_path)
        if not video_path_obj.exists():
            return

        # Check if already in playlist
        if video_path_obj in self.videos:
            return

        self.videos.append(video_path_obj)

        # Add to list widget
        item = QtWidgets.QListWidgetItem()

        # Format display text
        name = video_path_obj.name
        size_mb = get_file_size_mb(str(video_path_obj))
        size_str = format_file_size(int(size_mb * 1024 * 1024))

        item.setText(f"{name}\n{size_str}")
        item.setData(QtCore.Qt.ItemDataRole.UserRole, str(video_path_obj))

        # Set icon based on file extension
        icon = self._get_file_icon(video_path_obj.suffix)
        item.setIcon(icon)

        self.list_widget.addItem(item)

        self._update_count()
        self._update_buttons()
        self.playlist_changed.emit()

    def remove_video(self, index: int):
        """
        Remove video from playlist.

        Args:
            index: Index of video to remove
        """
        if 0 <= index < len(self.videos):
            self.videos.pop(index)
            self.list_widget.takeItem(index)

            # Adjust current index
            if index < self.current_index:
                self.current_index -= 1
            elif index == self.current_index:
                self.current_index = -1

            self._update_count()
            self._update_buttons()
            self.playlist_changed.emit()

    def clear_playlist(self):
        """Clear all videos from playlist."""
        self.videos.clear()
        self.list_widget.clear()
        self.current_index = -1
        self._update_count()
        self._update_buttons()
        self.playlist_changed.emit()

    def set_current_index(self, index: int):
        """
        Set current playing video index.

        Args:
            index: Index of current video
        """
        if 0 <= index < len(self.videos):
            # Clear previous highlight
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                font = item.font()
                font.setBold(False)
                item.setFont(font)
                item.setBackground(QtGui.QColor(255, 255, 255, 0))
                # Reset foreground color
                item.setForeground(QtGui.QColor(0, 0, 0))

                # Remove playing indicator
                current_text = item.text()
                if current_text.startswith("▶ "):
                    item.setText(current_text[2:])

            # Highlight current
            self.current_index = index
            item = self.list_widget.item(index)
            font = item.font()
            font.setBold(True)
            item.setFont(font)
            # Modern gradient-like highlight
            item.setBackground(QtGui.QColor(74, 144, 226, 80))
            item.setForeground(QtGui.QColor(0, 0, 0))

            # Add playing indicator to text
            current_text = item.text()
            if not current_text.startswith("▶ "):
                item.setText("▶ " + current_text)

            # Scroll to item
            self.list_widget.scrollToItem(item)

            self._update_buttons()

    def get_current_video(self) -> Optional[str]:
        """
        Get path to current video.

        Returns:
            Path to current video, or None
        """
        if 0 <= self.current_index < len(self.videos):
            return str(self.videos[self.current_index])
        return None

    def play_next(self):
        """Play next video in playlist."""
        if self.has_next():
            next_index = self.current_index + 1
            self.set_current_index(next_index)
            self.video_selected.emit(str(self.videos[next_index]))

    def play_previous(self):
        """Play previous video in playlist."""
        if self.has_previous():
            prev_index = self.current_index - 1
            self.set_current_index(prev_index)
            self.video_selected.emit(str(self.videos[prev_index]))

    def has_next(self) -> bool:
        """Check if there is a next video."""
        return self.current_index < len(self.videos) - 1

    def has_previous(self) -> bool:
        """Check if there is a previous video."""
        return self.current_index > 0

    def get_video_count(self) -> int:
        """Get number of videos in playlist."""
        return len(self.videos)

    def _on_item_double_clicked(self, item: QtWidgets.QListWidgetItem):
        """Handle item double click."""
        index = self.list_widget.row(item)
        self.set_current_index(index)
        self.video_selected.emit(str(self.videos[index]))

    def _show_context_menu(self, position):
        """Show context menu for playlist item."""
        item = self.list_widget.itemAt(position)
        if not item:
            return

        index = self.list_widget.row(item)

        menu = QtWidgets.QMenu(self)

        play_action = menu.addAction("Play")
        play_action.triggered.connect(lambda: self._on_item_double_clicked(item))

        menu.addSeparator()

        remove_action = menu.addAction("Remove from Playlist")
        remove_action.triggered.connect(lambda: self.remove_video(index))

        menu.addSeparator()

        reveal_action = menu.addAction("Reveal in Finder")
        reveal_action.triggered.connect(lambda: self._reveal_in_finder(index))

        menu.exec(self.list_widget.mapToGlobal(position))

    def _reveal_in_finder(self, index: int):
        """Reveal video file in Finder."""
        if 0 <= index < len(self.videos):
            import subprocess
            subprocess.run(['open', '-R', str(self.videos[index])])

    def _update_count(self):
        """Update video count label."""
        count = len(self.videos)
        self.count_label.setText(f"{count} video{'s' if count != 1 else ''}")

    def _update_buttons(self):
        """Update button states."""
        self.prev_btn.setEnabled(self.has_previous())
        self.next_btn.setEnabled(self.has_next())

    def _get_file_icon(self, extension: str) -> QtGui.QIcon:
        """Get icon for file type."""
        # Use built-in Qt icons
        return self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileIcon)
