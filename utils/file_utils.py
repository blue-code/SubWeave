"""
File Management Utilities
Handles file operations including moving files to trash.
"""
from pathlib import Path
from typing import Optional, List
import logging

try:
    from send2trash import send2trash
except ImportError:
    send2trash = None
    logging.warning("send2trash not installed. Delete functionality will be disabled.")


def move_to_trash(file_path: str, confirm: bool = True) -> bool:
    """
    Move file to system trash/recycle bin.

    Args:
        file_path: Path to file to delete
        confirm: If True, will be confirmed by caller

    Returns:
        True if successful, False otherwise
    """
    if send2trash is None:
        logging.error("send2trash is not installed. Cannot move file to trash.")
        return False

    try:
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            logging.warning(f"File does not exist: {file_path}")
            return False

        # Move to trash
        send2trash(str(file_path_obj))
        logging.info(f"Moved to trash: {file_path}")
        return True

    except Exception as e:
        logging.error(f"Failed to move to trash: {e}")
        return False


def get_video_files(directory: str, extensions: Optional[List[str]] = None) -> List[Path]:
    """
    Get list of video files in directory.

    Args:
        directory: Directory to search
        extensions: List of file extensions to match (default: common video formats)

    Returns:
        List of video file paths
    """
    if extensions is None:
        extensions = ['.mp4', '.mkv', '.avi', '.mov', '.m4v', '.webm', '.flv', '.wmv']

    directory_path = Path(directory)
    if not directory_path.exists():
        logging.warning(f"Directory does not exist: {directory}")
        return []

    video_files = []
    for ext in extensions:
        video_files.extend(directory_path.glob(f"*{ext}"))
        video_files.extend(directory_path.glob(f"*{ext.upper()}"))

    return sorted(video_files)


def get_file_size_mb(file_path: str) -> float:
    """
    Get file size in megabytes.

    Args:
        file_path: Path to file

    Returns:
        File size in MB
    """
    try:
        file_path_obj = Path(file_path)
        if file_path_obj.exists():
            size_bytes = file_path_obj.stat().st_size
            return size_bytes / (1024 * 1024)
    except Exception as e:
        logging.error(f"Failed to get file size: {e}")
    return 0.0


def ensure_directory(directory: str) -> bool:
    """
    Ensure directory exists, create if it doesn't.

    Args:
        directory: Directory path

    Returns:
        True if directory exists or was created successfully
    """
    try:
        directory_path = Path(directory)
        directory_path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logging.error(f"Failed to create directory: {e}")
        return False


def get_safe_filename(filename: str) -> str:
    """
    Convert filename to safe format (remove invalid characters).

    Args:
        filename: Original filename

    Returns:
        Safe filename
    """
    # Characters to remove or replace
    invalid_chars = '<>:"/\\|?*'
    safe_name = filename

    for char in invalid_chars:
        safe_name = safe_name.replace(char, '_')

    # Remove leading/trailing spaces and dots
    safe_name = safe_name.strip(' .')

    return safe_name


def get_unique_filepath(file_path: str) -> Path:
    """
    Get unique file path by appending number if file already exists.

    Args:
        file_path: Original file path

    Returns:
        Unique file path
    """
    file_path_obj = Path(file_path)

    if not file_path_obj.exists():
        return file_path_obj

    # File exists, find unique name
    stem = file_path_obj.stem
    suffix = file_path_obj.suffix
    parent = file_path_obj.parent

    counter = 1
    while True:
        new_path = parent / f"{stem}_{counter}{suffix}"
        if not new_path.exists():
            return new_path
        counter += 1


def is_video_file(file_path: str) -> bool:
    """
    Check if file is a video file based on extension.

    Args:
        file_path: Path to file

    Returns:
        True if file appears to be a video
    """
    video_extensions = {
        '.mp4', '.mkv', '.avi', '.mov', '.m4v',
        '.webm', '.flv', '.wmv', '.mpg', '.mpeg',
        '.3gp', '.ogv', '.ts', '.m2ts'
    }

    file_path_obj = Path(file_path)
    return file_path_obj.suffix.lower() in video_extensions


def get_relative_path(file_path: str, base_path: str) -> str:
    """
    Get relative path from base path.

    Args:
        file_path: File path
        base_path: Base directory path

    Returns:
        Relative path string
    """
    try:
        file_path_obj = Path(file_path)
        base_path_obj = Path(base_path)
        return str(file_path_obj.relative_to(base_path_obj))
    except ValueError:
        # Paths are not relative to each other
        return str(file_path)


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string (HH:MM:SS)
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"
