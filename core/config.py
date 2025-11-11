"""
Configuration Management Module
Manages application settings, paths, and user preferences.
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """Application configuration manager."""

    # Application Info
    APP_NAME = "SubWeave"
    APP_VERSION = "1.0.0"

    # Default Settings
    DEFAULT_SETTINGS = {
        # ASR Settings
        "asr": {
            "model_size": "medium",  # tiny, base, small, medium, large-v2, large-v3
            "compute_type": "int8",  # int8, float16, float32
            "language": "ja",  # Japanese
            "vad_filter": True,
            "beam_size": 5,
        },
        # Translation Settings
        "translation": {
            "model_name": "nllb-200-distilled-600M",
            "source_lang": "jpn_Jpan",  # Japanese (FLORES-200 code)
            "target_lang": "kor_Hang",  # Korean (FLORES-200 code)
            "beam_size": 4,
            "batch_size": 32,
        },
        # Subtitle Settings
        "subtitle": {
            "font_size": 24,
            "font_name": "Arial",
            "font_color": "#FFFFFF",
            "background_color": "#000000",
            "background_opacity": 0.7,
            "position": "bottom",  # top, middle, bottom
            "max_line_length": 42,
            "min_segment_duration": 1.0,  # seconds
        },
        # Player Settings
        "player": {
            "volume": 100,
            "seek_step": 5,  # seconds
            "subtitle_enabled": True,
            "fullscreen": False,
            "auto_play_next": True,  # Auto-play next video in playlist
        },
        # File Management
        "file": {
            "confirm_delete": True,
            "cache_enabled": True,
            "auto_process_on_open": True,
        },
        # UI Settings
        "ui": {
            "window_width": 1280,
            "window_height": 720,
            "theme": "dark",
        }
    }

    def __init__(self):
        """Initialize configuration manager."""
        self.app_dir = self._get_app_dir()
        self.cache_dir = self.app_dir / "cache"
        self.models_dir = self.app_dir / "models"
        self.subs_dir = self.app_dir / "subs"
        self.config_file = self.app_dir / "config.json"

        # Create directories if they don't exist
        self._create_directories()

        # Load or create configuration
        self.settings = self._load_settings()

    def _get_app_dir(self) -> Path:
        """Get application directory path (relative to program location)."""
        # Get the directory where this module is located
        current_file = Path(__file__).resolve()
        # Go up to the project root (assuming config.py is in core/)
        project_root = current_file.parent.parent
        # Create data directory in project root
        app_dir = project_root / "data"
        return app_dir

    def _create_directories(self):
        """Create necessary application directories."""
        for directory in [self.app_dir, self.cache_dir, self.models_dir, self.subs_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from config file or create default."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                # Merge with defaults to ensure all keys exist
                return self._merge_settings(self.DEFAULT_SETTINGS, settings)
            except Exception as e:
                print(f"Error loading config: {e}. Using defaults.")
                return self.DEFAULT_SETTINGS.copy()
        else:
            # Create default config
            self.save_settings(self.DEFAULT_SETTINGS)
            return self.DEFAULT_SETTINGS.copy()

    def _merge_settings(self, defaults: Dict, loaded: Dict) -> Dict:
        """Recursively merge loaded settings with defaults."""
        result = defaults.copy()
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_settings(result[key], value)
            else:
                result[key] = value
        return result

    def save_settings(self, settings: Optional[Dict[str, Any]] = None):
        """Save settings to config file."""
        if settings is None:
            settings = self.settings

        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get setting value using dot notation.
        Example: config.get('asr.model_size')
        """
        keys = key_path.split('.')
        value = self.settings
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def set(self, key_path: str, value: Any):
        """
        Set setting value using dot notation.
        Example: config.set('asr.model_size', 'large')
        """
        keys = key_path.split('.')
        settings = self.settings
        for key in keys[:-1]:
            if key not in settings:
                settings[key] = {}
            settings = settings[key]
        settings[keys[-1]] = value
        self.save_settings()

    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        self.settings = self.DEFAULT_SETTINGS.copy()
        self.save_settings()

    def get_cache_path(self, video_path: str) -> Path:
        """Get cache directory path for a specific video."""
        from hashlib import md5
        video_hash = md5(video_path.encode()).hexdigest()[:8]
        video_name = Path(video_path).stem
        cache_name = f"{video_name}_{video_hash}"
        return self.cache_dir / cache_name

    def get_srt_path(self, video_path: str) -> Path:
        """Get SRT file path for a specific video."""
        video_path_obj = Path(video_path)
        return self.subs_dir / f"{video_path_obj.stem}.srt"


# Global configuration instance
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """Get global configuration instance (singleton pattern)."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


def reset_config():
    """Reset global configuration instance."""
    global _config_instance
    _config_instance = None
