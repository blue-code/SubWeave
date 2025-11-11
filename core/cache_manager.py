"""
Cache Management Module
Handles caching of generated subtitles and video processing metadata.
"""
import os
import json
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime


class CacheManager:
    """Manages subtitle cache and processing metadata."""

    def __init__(self, cache_dir: Path):
        """
        Initialize cache manager.

        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_video_hash(self, video_path: str) -> str:
        """
        Generate a unique hash for a video file.
        Combines file path and modification time for uniqueness.

        Args:
            video_path: Path to video file

        Returns:
            8-character hash string
        """
        video_path_obj = Path(video_path)
        if not video_path_obj.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Combine path and modification time for hash
        mtime = os.path.getmtime(video_path)
        hash_input = f"{video_path}_{mtime}".encode('utf-8')
        return hashlib.md5(hash_input).hexdigest()[:8]

    def _get_cache_key(self, video_path: str) -> str:
        """
        Generate cache key for a video.

        Args:
            video_path: Path to video file

        Returns:
            Cache key string
        """
        video_name = Path(video_path).stem
        video_hash = self._get_video_hash(video_path)
        return f"{video_name}_{video_hash}"

    def get_srt_path(self, video_path: str) -> Path:
        """
        Get path to SRT file for a video (same directory as video).

        Args:
            video_path: Path to video file

        Returns:
            Path to SRT file in the same directory as the video
        """
        video_path_obj = Path(video_path)
        video_dir = video_path_obj.parent
        video_stem = video_path_obj.stem
        return video_dir / f"{video_stem}.srt"

    def get_metadata_path(self, video_path: str) -> Path:
        """
        Get path to cached metadata file for a video.

        Args:
            video_path: Path to video file

        Returns:
            Path to metadata JSON file
        """
        cache_key = self._get_cache_key(video_path)
        return self.cache_dir / f"{cache_key}.json"

    def has_cached_subtitles(self, video_path: str) -> bool:
        """
        Check if subtitles are cached for a video.

        Args:
            video_path: Path to video file

        Returns:
            True if cached subtitles exist
        """
        try:
            srt_path = self.get_srt_path(video_path)
            return srt_path.exists() and srt_path.stat().st_size > 0
        except:
            return False

    def load_cached_subtitles(self, video_path: str) -> Optional[str]:
        """
        Load cached subtitles for a video.

        Args:
            video_path: Path to video file

        Returns:
            SRT content string, or None if not cached
        """
        try:
            srt_path = self.get_srt_path(video_path)
            if srt_path.exists():
                with open(srt_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            print(f"Error loading cached subtitles: {e}")
        return None

    def save_cached_subtitles(self, video_path: str, srt_content: str):
        """
        Save subtitles to cache.

        Args:
            video_path: Path to video file
            srt_content: SRT subtitle content
        """
        try:
            srt_path = self.get_srt_path(video_path)
            with open(srt_path, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            print(f"Cached subtitles saved: {srt_path}")
        except Exception as e:
            print(f"Error saving cached subtitles: {e}")

    def load_metadata(self, video_path: str) -> Optional[Dict[str, Any]]:
        """
        Load processing metadata for a video.

        Args:
            video_path: Path to video file

        Returns:
            Metadata dictionary, or None if not cached
        """
        try:
            metadata_path = self.get_metadata_path(video_path)
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading metadata: {e}")
        return None

    def save_metadata(self, video_path: str, metadata: Dict[str, Any]):
        """
        Save processing metadata to cache.

        Args:
            video_path: Path to video file
            metadata: Metadata dictionary
        """
        try:
            # Add timestamp
            metadata['cached_at'] = datetime.now().isoformat()
            metadata['video_path'] = str(video_path)

            metadata_path = self.get_metadata_path(video_path)
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            print(f"Metadata saved: {metadata_path}")
        except Exception as e:
            print(f"Error saving metadata: {e}")

    def delete_cache(self, video_path: str):
        """
        Delete cached files for a video.

        Args:
            video_path: Path to video file
        """
        try:
            srt_path = self.get_srt_path(video_path)
            metadata_path = self.get_metadata_path(video_path)

            if srt_path.exists():
                srt_path.unlink()
                print(f"Deleted cached SRT: {srt_path}")

            if metadata_path.exists():
                metadata_path.unlink()
                print(f"Deleted metadata: {metadata_path}")
        except Exception as e:
            print(f"Error deleting cache: {e}")

    def clear_all_cache(self):
        """Delete all cached files."""
        try:
            for file_path in self.cache_dir.glob("*"):
                if file_path.is_file():
                    file_path.unlink()
            print(f"Cleared all cache in: {self.cache_dir}")
        except Exception as e:
            print(f"Error clearing cache: {e}")

    def get_cache_size(self) -> int:
        """
        Get total size of cache directory in bytes.

        Returns:
            Total cache size in bytes
        """
        total_size = 0
        try:
            for file_path in self.cache_dir.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except Exception as e:
            print(f"Error calculating cache size: {e}")
        return total_size

    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about cached files.

        Returns:
            Dictionary with cache statistics
        """
        info = {
            'total_files': 0,
            'srt_files': 0,
            'metadata_files': 0,
            'total_size_bytes': 0,
            'total_size_mb': 0.0,
        }

        try:
            for file_path in self.cache_dir.glob("*"):
                if file_path.is_file():
                    info['total_files'] += 1
                    size = file_path.stat().st_size
                    info['total_size_bytes'] += size

                    if file_path.suffix == '.srt':
                        info['srt_files'] += 1
                    elif file_path.suffix == '.json':
                        info['metadata_files'] += 1

            info['total_size_mb'] = round(info['total_size_bytes'] / (1024 * 1024), 2)
        except Exception as e:
            print(f"Error getting cache info: {e}")

        return info
