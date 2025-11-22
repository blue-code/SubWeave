"""
Video Player Widget
Qt Multimedia-based video player with subtitle support for Qt/PySide6.
Stable and native implementation using Qt's multimedia framework.
"""
from PySide6 import QtWidgets, QtCore, QtMultimedia, QtMultimediaWidgets, QtGui
from typing import Optional, List
import logging
from pathlib import Path


class PlayerWidget(QtWidgets.QWidget):
    """Video player widget using Qt Multimedia (stable, native implementation)."""

    # Qt signals
    playback_started = QtCore.Signal()
    playback_paused = QtCore.Signal()
    playback_ended = QtCore.Signal()
    time_position_changed = QtCore.Signal(float)  # Current position in seconds
    duration_changed = QtCore.Signal(float)  # Total duration in seconds
    error_occurred = QtCore.Signal(str)  # Error message

    def __init__(self, parent=None):
        """
        Initialize player widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Create layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create media player
        self.player = QtMultimedia.QMediaPlayer(self)
        self.audio_output = QtMultimedia.QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)

        # Create video widget
        self.video_widget = QtMultimediaWidgets.QVideoWidget(self)
        self.player.setVideoOutput(self.video_widget)
        layout.addWidget(self.video_widget)

        # State tracking
        self._current_file: Optional[str] = None
        self._subtitle_path: Optional[str] = None
        self._subtitle_text: str = ""

        # Subtitle overlay label
        self.subtitle_label = QtWidgets.QLabel(self.video_widget)
        self.subtitle_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: rgba(0, 0, 0, 180);
                padding: 8px 16px;
                font-size: 18px;
                font-weight: bold;
                border-radius: 4px;
            }
        """)
        self.subtitle_label.hide()

        # Connect signals
        self.player.playbackStateChanged.connect(self._on_playback_state_changed)
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.player.errorOccurred.connect(self._on_error_occurred)
        self.player.mediaStatusChanged.connect(self._on_media_status_changed)

        # Timer for position updates
        self.position_timer = QtCore.QTimer(self)
        self.position_timer.timeout.connect(self._update_position)
        self.position_timer.setInterval(100)  # Update every 100ms

        # Timer for subtitle updates
        self.subtitle_timer = QtCore.QTimer(self)
        self.subtitle_timer.timeout.connect(self._update_subtitle)
        self.subtitle_timer.setInterval(100)  # Check subtitles every 100ms

        # Subtitle data (parsed from SRT)
        self.subtitle_entries = []

        # Video markers for splitting
        self.markers: List[float] = []  # List of marker positions in seconds

        logging.info("PlayerWidget initialized with Qt Multimedia")

    def resizeEvent(self, event):
        """Handle widget resize to position subtitle label."""
        super().resizeEvent(event)
        # Position subtitle label at the bottom
        if self.subtitle_label.isVisible():
            label_height = self.subtitle_label.sizeHint().height()
            label_width = self.subtitle_label.sizeHint().width()
            x = (self.video_widget.width() - label_width) // 2
            y = self.video_widget.height() - label_height - 40
            self.subtitle_label.move(x, y)

    def load_file(self, file_path: str, subtitle_path: Optional[str] = None):
        """
        Load and play a video file.

        Args:
            file_path: Path to video file
            subtitle_path: Optional path to subtitle file
        """
        try:
            self._current_file = file_path
            self._subtitle_path = subtitle_path

            # Load video
            self.player.setSource(QtCore.QUrl.fromLocalFile(file_path))

            # Load subtitle if provided
            if subtitle_path:
                self.add_subtitle(subtitle_path)

            # Start playback
            self.player.play()
            self.position_timer.start()
            self.subtitle_timer.start()

            logging.info(f"Loaded file: {file_path}")

        except Exception as e:
            error_msg = f"Failed to load file: {e}"
            logging.error(error_msg)
            self.error_occurred.emit(error_msg)

    def add_subtitle(self, subtitle_path: str):
        """
        Add subtitle file to current video.

        Args:
            subtitle_path: Path to subtitle file (SRT format)
        """
        try:
            self._subtitle_path = subtitle_path
            self.subtitle_entries = self._parse_srt(subtitle_path)
            # Hide subtitles by default - user must enable with CC button
            self.subtitle_label.hide()
            logging.info(f"Added subtitle: {subtitle_path} ({len(self.subtitle_entries)} entries)")
        except Exception as e:
            error_msg = f"Failed to add subtitle: {e}"
            logging.error(error_msg)
            self.error_occurred.emit(error_msg)

    def _parse_srt(self, srt_path: str) -> list:
        """
        Parse SRT subtitle file.

        Args:
            srt_path: Path to SRT file

        Returns:
            List of subtitle entries with start, end, and text
        """
        entries = []
        try:
            with open(srt_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Split by double newlines
            blocks = content.strip().split('\n\n')

            for block in blocks:
                lines = block.strip().split('\n')
                if len(lines) >= 3:
                    # Parse timestamp line (format: 00:00:00,000 --> 00:00:05,000)
                    timestamp_line = lines[1]
                    if '-->' in timestamp_line:
                        start_str, end_str = timestamp_line.split('-->')
                        start_ms = self._parse_timestamp(start_str.strip())
                        end_ms = self._parse_timestamp(end_str.strip())

                        # Get subtitle text (lines after timestamp)
                        text = '\n'.join(lines[2:])

                        entries.append({
                            'start': start_ms,
                            'end': end_ms,
                            'text': text
                        })

        except Exception as e:
            logging.error(f"Failed to parse SRT: {e}")

        return entries

    def _parse_timestamp(self, timestamp: str) -> int:
        """
        Parse SRT timestamp to milliseconds.

        Args:
            timestamp: Timestamp string (HH:MM:SS,mmm)

        Returns:
            Time in milliseconds
        """
        # Format: 00:00:00,000
        time_part, ms_part = timestamp.split(',')
        h, m, s = map(int, time_part.split(':'))
        ms = int(ms_part)
        return (h * 3600000) + (m * 60000) + (s * 1000) + ms

    def _update_subtitle(self):
        """Update subtitle display based on current position."""
        if not self.subtitle_entries:
            return

        current_pos = self.player.position()  # milliseconds

        # Find current subtitle
        current_subtitle = None
        for entry in self.subtitle_entries:
            if entry['start'] <= current_pos <= entry['end']:
                current_subtitle = entry['text']
                break

        # Update subtitle label
        if current_subtitle:
            self.subtitle_label.setText(current_subtitle)
            self.subtitle_label.adjustSize()
            self.subtitle_label.show()
            # Re-center subtitle
            label_width = self.subtitle_label.width()
            label_height = self.subtitle_label.height()
            x = (self.video_widget.width() - label_width) // 2
            y = self.video_widget.height() - label_height - 40
            self.subtitle_label.move(x, y)
        else:
            self.subtitle_label.hide()

    def play(self):
        """Start or resume playback."""
        self.player.play()
        self.position_timer.start()
        self.subtitle_timer.start()

    def pause(self):
        """Pause playback."""
        self.player.pause()
        self.position_timer.stop()

    def toggle_pause(self):
        """Toggle play/pause state."""
        if self.player.playbackState() == QtMultimedia.QMediaPlayer.PlaybackState.PlayingState:
            self.pause()
        else:
            self.play()

    def stop(self):
        """Stop playback."""
        self.player.stop()
        self.position_timer.stop()
        self.subtitle_timer.stop()
        self._current_file = None

    def seek(self, seconds: float, relative: bool = True):
        """
        Seek to a position.

        Args:
            seconds: Position in seconds
            relative: If True, seek relative to current position
        """
        if relative:
            new_pos = self.player.position() + int(seconds * 1000)
        else:
            new_pos = int(seconds * 1000)

        self.player.setPosition(new_pos)

    def set_volume(self, volume: int):
        """
        Set playback volume.

        Args:
            volume: Volume level (0-100)
        """
        # Qt uses 0.0 to 1.0
        normalized_volume = max(0.0, min(1.0, volume / 100.0))
        self.audio_output.setVolume(normalized_volume)

    def get_volume(self) -> int:
        """
        Get current volume.

        Returns:
            Volume level (0-100)
        """
        return int(self.audio_output.volume() * 100)

    def set_playback_speed(self, speed: float):
        """
        Set playback speed.

        Args:
            speed: Playback speed (0.5 to 2.0, 1.0 is normal)
        """
        # Clamp speed to reasonable range
        speed = max(0.25, min(4.0, speed))
        self.player.setPlaybackRate(speed)
        logging.info(f"Playback speed set to {speed}x")

    def get_playback_speed(self) -> float:
        """
        Get current playback speed.

        Returns:
            Current playback speed
        """
        return self.player.playbackRate()

    def toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        if self.video_widget.isFullScreen():
            self.video_widget.setFullScreen(False)
        else:
            self.video_widget.setFullScreen(True)

    def toggle_subtitles(self):
        """Toggle subtitle visibility."""
        if self.subtitle_label.isVisible():
            self.subtitle_label.hide()
        else:
            if self.subtitle_entries:
                self.subtitle_label.show()

    def set_subtitle_size(self, size: int):
        """
        Set subtitle font size.

        Args:
            size: Font size
        """
        current_style = self.subtitle_label.styleSheet()
        # Update font-size in stylesheet
        new_style = current_style.replace(
            "font-size: 18px",
            f"font-size: {size}px"
        )
        self.subtitle_label.setStyleSheet(new_style)

    def increase_subtitle_size(self):
        """Increase subtitle font size."""
        # Extract current size from stylesheet
        style = self.subtitle_label.styleSheet()
        import re
        match = re.search(r'font-size:\s*(\d+)px', style)
        if match:
            current_size = int(match.group(1))
            self.set_subtitle_size(int(current_size * 1.1))

    def decrease_subtitle_size(self):
        """Decrease subtitle font size."""
        style = self.subtitle_label.styleSheet()
        import re
        match = re.search(r'font-size:\s*(\d+)px', style)
        if match:
            current_size = int(match.group(1))
            self.set_subtitle_size(int(current_size * 0.9))

    def is_playing(self) -> bool:
        """
        Check if currently playing.

        Returns:
            True if playing
        """
        return self.player.playbackState() == QtMultimedia.QMediaPlayer.PlaybackState.PlayingState

    def get_current_position(self) -> float:
        """
        Get current playback position.

        Returns:
            Position in seconds
        """
        return self.player.position() / 1000.0

    def get_duration(self) -> float:
        """
        Get total duration.

        Returns:
            Duration in seconds
        """
        return self.player.duration() / 1000.0

    def get_current_file(self) -> Optional[str]:
        """
        Get path to currently loaded file.

        Returns:
            File path or None
        """
        return self._current_file

    def _on_playback_state_changed(self, state):
        """Handle playback state changes."""
        if state == QtMultimedia.QMediaPlayer.PlaybackState.PlayingState:
            self.playback_started.emit()
        elif state == QtMultimedia.QMediaPlayer.PlaybackState.PausedState:
            self.playback_paused.emit()
        elif state == QtMultimedia.QMediaPlayer.PlaybackState.StoppedState:
            self.playback_ended.emit()

    def _on_position_changed(self, position):
        """Handle position changes."""
        # Position is in milliseconds
        self.time_position_changed.emit(position / 1000.0)

    def _on_duration_changed(self, duration):
        """Handle duration changes."""
        # Duration is in milliseconds
        if duration > 0:
            self.duration_changed.emit(duration / 1000.0)

    def _on_error_occurred(self, error, error_string):
        """Handle errors."""
        error_msg = f"Player error: {error_string}"
        logging.error(error_msg)
        self.error_occurred.emit(error_msg)

    def _on_media_status_changed(self, status):
        """Handle media status changes."""
        if status == QtMultimedia.QMediaPlayer.MediaStatus.EndOfMedia:
            self.playback_ended.emit()
            self.position_timer.stop()
            self.subtitle_timer.stop()

    def _update_position(self):
        """Update current playback position."""
        if self.player.playbackState() == QtMultimedia.QMediaPlayer.PlaybackState.PlayingState:
            pos = self.player.position() / 1000.0
            self.time_position_changed.emit(pos)

    def add_marker(self, position: Optional[float] = None):
        """
        Add a marker at specified position or current playback position.

        Args:
            position: Position in seconds (None = current position)
        """
        if position is None:
            position = self.get_current_position()

        if position not in self.markers:
            self.markers.append(position)
            self.markers.sort()
            logging.info(f"Added marker at {position:.2f}s")

    def remove_marker(self, position: float, tolerance: float = 0.5):
        """
        Remove marker at specified position.

        Args:
            position: Position in seconds
            tolerance: Tolerance range for matching markers
        """
        for marker in self.markers:
            if abs(marker - position) <= tolerance:
                self.markers.remove(marker)
                logging.info(f"Removed marker at {marker:.2f}s")
                return True
        return False

    def remove_nearest_marker(self):
        """Remove marker nearest to current playback position."""
        if not self.markers:
            return False

        current_pos = self.get_current_position()
        nearest = min(self.markers, key=lambda m: abs(m - current_pos))
        self.markers.remove(nearest)
        logging.info(f"Removed nearest marker at {nearest:.2f}s")
        return True

    def clear_markers(self):
        """Clear all markers."""
        self.markers.clear()
        logging.info("Cleared all markers")

    def get_markers(self) -> List[float]:
        """
        Get all markers.

        Returns:
            List of marker positions in seconds
        """
        return self.markers.copy()

    def closeEvent(self, event):
        """Handle widget close event."""
        self.stop()
        super().closeEvent(event)
