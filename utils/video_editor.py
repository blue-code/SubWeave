"""
Video Editor Utility
Provides video editing functions including splitting videos at marker positions.
"""
from typing import List, Tuple, Optional
from pathlib import Path
import logging
import subprocess
import ffmpeg


class VideoMarker:
    """Represents a time marker in a video."""

    def __init__(self, time_seconds: float, label: str = ""):
        """
        Initialize a video marker.

        Args:
            time_seconds: Time position in seconds
            label: Optional label for the marker
        """
        self.time = time_seconds
        self.label = label

    def __repr__(self):
        return f"VideoMarker(time={self.time:.2f}s, label='{self.label}')"

    def __lt__(self, other):
        """Enable sorting markers by time."""
        return self.time < other.time


class VideoEditor:
    """Video editing utility for splitting and trimming videos."""

    @staticmethod
    def split_video_at_markers(
        input_path: str,
        markers: List[VideoMarker],
        output_dir: Optional[str] = None,
        include_full_segments: bool = True
    ) -> List[str]:
        """
        Split video at marker positions.

        Args:
            input_path: Path to input video file
            markers: List of VideoMarker objects
            output_dir: Output directory (defaults to input file's directory)
            include_full_segments: If True, creates video segments between markers

        Returns:
            List of paths to created video files
        """
        input_path = Path(input_path)
        if not input_path.exists():
            raise FileNotFoundError(f"Video file not found: {input_path}")

        # Sort markers by time
        markers = sorted(markers)

        # Setup output directory
        if output_dir is None:
            output_dir = input_path.parent
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

        # Get video duration
        duration = VideoEditor.get_video_duration(str(input_path))
        if duration is None:
            raise ValueError(f"Could not determine video duration: {input_path}")

        output_files = []

        if include_full_segments:
            # Create segments between markers
            segments = []

            # Add segment from start to first marker
            if markers and markers[0].time > 0:
                segments.append((0, markers[0].time, "00_start"))

            # Add segments between markers
            for i in range(len(markers) - 1):
                start = markers[i].time
                end = markers[i + 1].time
                label = f"{i+1:02d}_{markers[i].label}" if markers[i].label else f"{i+1:02d}_segment"
                segments.append((start, end, label))

            # Add segment from last marker to end
            if markers and markers[-1].time < duration:
                label = f"{len(markers):02d}_end"
                segments.append((markers[-1].time, duration, label))

            # Create video files for each segment
            for start, end, label in segments:
                output_name = f"{input_path.stem}_{label}{input_path.suffix}"
                output_path = output_dir / output_name

                success = VideoEditor.trim_video(
                    input_path=str(input_path),
                    output_path=str(output_path),
                    start_time=start,
                    end_time=end
                )

                if success:
                    output_files.append(str(output_path))
                    logging.info(f"Created segment: {output_path.name}")

        return output_files

    @staticmethod
    def trim_video(
        input_path: str,
        output_path: str,
        start_time: float,
        end_time: Optional[float] = None
    ) -> bool:
        """
        Trim video to specific time range.

        Args:
            input_path: Path to input video file
            output_path: Path to output video file
            start_time: Start time in seconds
            end_time: End time in seconds (None = to end of video)

        Returns:
            True if successful, False otherwise
        """
        try:
            input_stream = ffmpeg.input(input_path)

            # Build ffmpeg command
            if end_time is not None:
                duration = end_time - start_time
                output_stream = input_stream.trim(start=start_time, duration=duration).setpts('PTS-STARTPTS')
            else:
                output_stream = input_stream.trim(start=start_time).setpts('PTS-STARTPTS')

            # Output with copy codec for fast processing
            output_stream = ffmpeg.output(
                output_stream,
                output_path,
                codec='copy',
                **{'avoid_negative_ts': 'make_zero'}
            )

            # Run ffmpeg
            ffmpeg.run(output_stream, overwrite_output=True, quiet=True)
            logging.info(f"Trimmed video: {output_path}")
            return True

        except ffmpeg.Error as e:
            logging.error(f"FFmpeg error while trimming video: {e.stderr.decode() if e.stderr else str(e)}")

            # Try with re-encoding if copy fails
            try:
                logging.info("Retrying with re-encoding...")
                input_stream = ffmpeg.input(input_path, ss=start_time)

                if end_time is not None:
                    duration = end_time - start_time
                    input_stream = ffmpeg.input(input_path, ss=start_time, t=duration)

                output_stream = ffmpeg.output(
                    input_stream,
                    output_path,
                    **{'c:v': 'libx264', 'c:a': 'aac', 'strict': 'experimental'}
                )

                ffmpeg.run(output_stream, overwrite_output=True, quiet=True)
                logging.info(f"Trimmed video with re-encoding: {output_path}")
                return True

            except ffmpeg.Error as e2:
                logging.error(f"FFmpeg error during re-encoding: {e2.stderr.decode() if e2.stderr else str(e2)}")
                return False

        except Exception as e:
            logging.error(f"Unexpected error while trimming video: {e}")
            return False

    @staticmethod
    def get_video_duration(video_path: str) -> Optional[float]:
        """
        Get video duration in seconds.

        Args:
            video_path: Path to video file

        Returns:
            Duration in seconds, or None if failed
        """
        try:
            probe = ffmpeg.probe(video_path)
            duration = float(probe['format']['duration'])
            return duration
        except Exception as e:
            logging.error(f"Failed to get video duration: {e}")
            return None

    @staticmethod
    def get_video_info(video_path: str) -> Optional[dict]:
        """
        Get video information.

        Args:
            video_path: Path to video file

        Returns:
            Dictionary with video info, or None if failed
        """
        try:
            probe = ffmpeg.probe(video_path)
            video_info = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)

            if video_info:
                return {
                    'duration': float(probe['format']['duration']),
                    'width': int(video_info.get('width', 0)),
                    'height': int(video_info.get('height', 0)),
                    'fps': eval(video_info.get('r_frame_rate', '0/1')),
                    'codec': video_info.get('codec_name', 'unknown'),
                    'bitrate': int(probe['format'].get('bit_rate', 0))
                }
        except Exception as e:
            logging.error(f"Failed to get video info: {e}")
            return None

    @staticmethod
    def check_ffmpeg_installed() -> bool:
        """
        Check if ffmpeg is installed and accessible.

        Returns:
            True if ffmpeg is available, False otherwise
        """
        try:
            subprocess.run(
                ['ffmpeg', '-version'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False


def format_time(seconds: float) -> str:
    """
    Format time in seconds to HH:MM:SS format.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted time string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"
