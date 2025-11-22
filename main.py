"""
Main Application Entry Point
Launches the SubWeave application.
"""
import sys
import os
import logging
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from PySide6 import QtWidgets, QtCore

from gui.main_window import MainWindow
from core.config import get_config
from utils.device_utils import log_device_info


def setup_logging():
    """Setup application logging."""
    config = get_config()
    log_dir = config.app_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "subweave.log"

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

    logging.info("=" * 60)
    logging.info("SubWeave Application Started")
    logging.info(f"Version: {config.APP_VERSION}")
    logging.info(f"Log file: {log_file}")
    logging.info("=" * 60)

    # Log device information (GPU/CPU detection)
    log_device_info()


def main():
    """Main application entry point."""
    # Setup logging first
    setup_logging()

    # Create Qt application
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("SubWeave")
    app.setOrganizationName("SubWeave")

    # Set application style
    app.setStyle("Fusion")

    # Create and show main window
    try:
        window = MainWindow()
        window.show()

        # Handle command line arguments
        if len(sys.argv) > 1:
            video_path = sys.argv[1]
            if Path(video_path).exists():
                logging.info(f"Opening video from command line: {video_path}")
                window._load_video(video_path)

        # Run application
        exit_code = app.exec()

        logging.info("Application exiting normally")
        sys.exit(exit_code)

    except Exception as e:
        logging.exception(f"Fatal error: {e}")
        QtWidgets.QMessageBox.critical(
            None,
            "Fatal Error",
            f"Application failed to start:\n\n{e}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
