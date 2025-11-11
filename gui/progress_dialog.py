"""
Progress Dialog
Shows progress of subtitle generation process.
"""
from PySide6 import QtWidgets, QtCore, QtGui


class ProgressDialog(QtWidgets.QDialog):
    """Dialog for displaying subtitle generation progress."""

    # Signal to cancel operation
    cancelled = QtCore.Signal()

    def __init__(self, parent=None):
        """
        Initialize progress dialog.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        self.setWindowTitle("Generating Subtitles")
        self.setModal(True)
        self.setMinimumWidth(500)

        self._setup_ui()
        self._is_cancelled = False

    def _setup_ui(self):
        """Setup user interface."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Apply modern dialog styling
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f5f5f5);
                border: 1px solid #d0d0d0;
                border-radius: 8px;
            }
            QLabel {
                color: #333333;
                background: transparent;
            }
            QProgressBar {
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                background: #f0f0f0;
                text-align: center;
                height: 24px;
                font-weight: 500;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4a90e2, stop:1 #5aa0f2);
                border-radius: 5px;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f0f0f0);
                border: 1px solid #c0c0c0;
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 80px;
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
        """)

        # Title label
        self.title_label = QtWidgets.QLabel("Processing video...")
        self.title_label.setStyleSheet("""
            font-size: 15px;
            font-weight: bold;
            color: #2c3e50;
            padding: 4px 0px;
        """)
        layout.addWidget(self.title_label)

        # Status label
        self.status_label = QtWidgets.QLabel("Initializing...")
        self.status_label.setStyleSheet("""
            font-size: 13px;
            color: #555555;
            padding: 2px 0px;
        """)
        layout.addWidget(self.status_label)

        # Main progress bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Detail label
        self.detail_label = QtWidgets.QLabel("")
        self.detail_label.setStyleSheet("""
            color: #777777;
            font-size: 11px;
            padding: 2px 0px;
        """)
        layout.addWidget(self.detail_label)

        # Spacer
        layout.addSpacing(10)

        # Button box
        button_box = QtWidgets.QDialogButtonBox()
        self.cancel_button = button_box.addButton(
            "Cancel",
            QtWidgets.QDialogButtonBox.ButtonRole.RejectRole
        )
        self.cancel_button.clicked.connect(self._on_cancel)
        layout.addWidget(button_box)

    def set_title(self, title: str):
        """
        Set dialog title text.

        Args:
            title: Title text
        """
        self.title_label.setText(title)

    def set_status(self, status: str):
        """
        Set status text.

        Args:
            status: Status text
        """
        self.status_label.setText(status)

    def set_progress(self, value: int):
        """
        Set progress value (0-100).

        Args:
            value: Progress percentage
        """
        self.progress_bar.setValue(max(0, min(100, value)))

    def set_detail(self, detail: str):
        """
        Set detail text.

        Args:
            detail: Detail text
        """
        self.detail_label.setText(detail)

    def update_progress(self, stage: str, progress: float):
        """
        Update progress with stage information.

        Args:
            stage: Current stage name
            progress: Progress percentage (0-100)
        """
        stage_names = {
            "cache": "Loading cached subtitles",
            "asr_init": "Initializing speech recognition",
            "asr": "Transcribing audio",
            "translation_init": "Initializing translation",
            "translation": "Translating to Korean",
            "srt_build": "Building subtitle file",
            "complete": "Complete"
        }

        status = stage_names.get(stage, stage.replace('_', ' ').title())
        self.set_status(status)
        self.set_progress(int(progress))

        if stage == "complete":
            self.cancel_button.setText("Close")
            self.cancel_button.setEnabled(True)

    def _on_cancel(self):
        """Handle cancel button click."""
        if self.progress_bar.value() < 100:
            # Still processing
            reply = QtWidgets.QMessageBox.question(
                self,
                "Cancel Operation",
                "Are you sure you want to cancel subtitle generation?",
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
            )
            if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                self._is_cancelled = True
                self.cancelled.emit()
                self.reject()
        else:
            # Completed
            self.accept()

    def is_cancelled(self) -> bool:
        """
        Check if operation was cancelled.

        Returns:
            True if cancelled
        """
        return self._is_cancelled

    def reset(self):
        """Reset dialog to initial state."""
        self._is_cancelled = False
        self.set_title("Processing video...")
        self.set_status("Initializing...")
        self.set_progress(0)
        self.set_detail("")
        self.cancel_button.setText("Cancel")
        self.cancel_button.setEnabled(True)


class WorkerThread(QtCore.QThread):
    """Worker thread for running subtitle generation in background."""

    # Signals
    progress_updated = QtCore.Signal(str, float)  # stage, progress
    finished_success = QtCore.Signal(str)  # result_path
    finished_error = QtCore.Signal(str)  # error_message

    def __init__(self, pipeline, video_path, use_cache=True):
        """
        Initialize worker thread.

        Args:
            pipeline: SubtitlePipeline instance
            video_path: Path to video file
            use_cache: Whether to use cache
        """
        super().__init__()
        self.pipeline = pipeline
        self.video_path = video_path
        self.use_cache = use_cache
        self._is_cancelled = False

    def run(self):
        """Run subtitle generation in thread."""
        try:
            def progress_callback(stage, progress):
                if not self._is_cancelled:
                    self.progress_updated.emit(stage, progress)

            result_path = self.pipeline.generate_subtitles(
                video_path=self.video_path,
                use_cache=self.use_cache,
                progress_callback=progress_callback
            )

            if not self._is_cancelled:
                self.finished_success.emit(result_path)

        except Exception as e:
            if not self._is_cancelled:
                self.finished_error.emit(str(e))

    def cancel(self):
        """Cancel the operation."""
        self._is_cancelled = True
