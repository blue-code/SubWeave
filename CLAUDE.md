# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SubWeave is a macOS desktop application that generates Korean subtitles from Japanese video content. It uses OpenAI Whisper (open-source) for speech recognition, NLLB-200 for machine translation, and Qt-based media player for video playback. The application also includes video editing features for splitting videos at marker positions.

## Development Commands

### Running the Application

```bash
# Run with Conda environment (recommended)
./run_conda.sh

# Run with a video file
./run_conda.sh /path/to/video.mp4

# Run directly with Python
python main.py
python main.py /path/to/video.mp4
```

### Installation

```bash
# Install dependencies with Conda
./install_conda.sh

# Setup translation model (required before first use)
./setup_model_conda.sh

# Install dependencies with pip
pip install -r requirements.txt
```

### Building

```bash
# Build macOS .app bundle
./build.sh
# Output: dist/SubWeave.app
```

## Architecture

### Data Flow Pipeline

The application follows a strict data flow for subtitle generation:

1. **ASR (Automatic Speech Recognition)** - `asr/asr_engine.py`
   - Uses OpenAI Whisper (open-source, not API)
   - Extracts Japanese speech from video → segments with timestamps
   - Returns `ASRSegment` objects with `start`, `end`, `text`, `language`

2. **Translation** - `translation/translation_engine.py`
   - Uses CTranslate2 + NLLB-200 model
   - Translates Japanese text → Korean
   - Batch processing for efficiency

3. **Subtitle Building** - `subtitle/subtitle_builder.py`
   - Combines ASR segments with translations
   - Generates SRT format files
   - Handles line breaking and timing optimization

4. **Pipeline Orchestration** - `subtitle/subtitle_pipeline.py`
   - Coordinates ASR → Translation → SRT workflow
   - Manages caching via `CacheManager`
   - Progress callbacks for UI updates

### Configuration & Caching

**Project-Local Configuration** (`core/config.py`):
- Configuration is stored in `data/config.json` (project directory)
- Cache stored in `data/cache/` (project directory)
- Subtitles stored in `data/subs/` (project directory)
- This is **project-local**, not user-global

**Cache Strategy** (`core/cache_manager.py`):
- SRT files are saved in the **same directory as the video file** (not in cache dir)
- Metadata (processing info) stored in `data/cache/{video_name}_{hash}.json`
- Cache key combines filename + modification time for uniqueness
- Method: `has_cached_subtitles()` checks if `.srt` exists next to video

### GUI Architecture

**Main Window** (`gui/main_window.py`):
- Qt-based application using PySide6
- Splitter layout: Player (left) + Playlist (right)
- Control panel with playback, subtitle, marker, and video editing controls
- Signal/slot pattern for event handling

**Player Widget** (`player/player_widget.py`):
- Qt Multimedia-based player (not MPV - this was changed from the README description)
- Subtitle overlay using QLabel
- Marker management for video editing (`markers: List[float]`)
- Methods: `add_marker()`, `remove_marker()`, `get_markers()`

**Video Editing** (`utils/video_editor.py`):
- FFmpeg-based video processing
- `VideoMarker` class represents split points
- `split_video_at_markers()` creates segments between markers
- Requires FFmpeg installed on system

### Worker Thread Pattern

**Background Processing** (`gui/progress_dialog.py`):
- `WorkerThread` runs subtitle generation in background
- Signals: `progress_updated`, `finished_success`, `finished_error`
- `ProgressDialog` displays progress with stage indicators
- Prevents UI freezing during long operations

## Important Implementation Details

### ASR Engine Configuration

The application uses **OpenAI Whisper (open-source)**, not the API version:
- Import: `import whisper` (not `from faster_whisper import WhisperModel`)
- Model loading: `whisper.load_model(model_size, device=device)`
- No API key required
- Config in `config.py`: `asr.model_size` and `asr.device`

### Subtitle File Location

Subtitles are saved **next to the video file**, not in a central cache:
```python
# In cache_manager.py
def get_srt_path(self, video_path: str) -> Path:
    video_path_obj = Path(video_path)
    video_dir = video_path_obj.parent
    video_stem = video_path_obj.stem
    return video_dir / f"{video_stem}.srt"
```

### Video Editing Workflow

1. User adds markers during playback with "M" key or "M+" button
2. Markers stored as float timestamps in `player.markers`
3. "Split" button calls `VideoEditor.split_video_at_markers()`
4. Output saved to `{video_name}_split/` directory next to original
5. Segments named: `{video_name}_00_start.mp4`, `{video_name}_01_segment.mp4`, etc.

### Keyboard Shortcuts

Video editing shortcuts:
- `M` - Add marker at current position
- `Shift+M` - Remove nearest marker
- `Ctrl+K` - Split video at markers

## Configuration Changes from README

Note: The README mentions `faster-whisper` and `python-mpv`, but the actual implementation uses:
- **ASR**: `openai-whisper` (open-source Whisper)
- **Player**: Qt Multimedia (`QtMultimedia.QMediaPlayer`)

When making changes, update both the code and README to stay synchronized.

## Adding New Features

### Adding New Subtitle Processing Steps

Modify `subtitle/subtitle_pipeline.py`:
1. Add step in `generate_subtitles()` method
2. Add progress callback: `progress_callback("step_name", progress_percent)`
3. Update `ProgressDialog` stage mapping in `gui/progress_dialog.py`

### Adding New Player Features

Modify `player/player_widget.py`:
1. Add methods to PlayerWidget class
2. Emit signals for UI updates
3. Connect signals in `gui/main_window.py`
4. Add UI controls in `_create_control_panel()`

### Adding New Video Editing Features

Modify `utils/video_editor.py`:
1. Add static methods to `VideoEditor` class
2. All methods should use FFmpeg via `ffmpeg-python` library
3. Check FFmpeg availability with `VideoEditor.check_ffmpeg_installed()`
