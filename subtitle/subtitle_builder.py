"""
Subtitle Builder Module
Creates and manages SRT subtitle files from transcription and translation segments.
"""
from typing import List, Optional
from datetime import timedelta
import re


class SubtitleSegment:
    """Represents a single subtitle segment."""

    def __init__(
        self,
        index: int,
        start_time: float,
        end_time: float,
        text: str
    ):
        """
        Initialize subtitle segment.

        Args:
            index: Segment index (1-based)
            start_time: Start time in seconds
            end_time: End time in seconds
            text: Subtitle text
        """
        self.index = index
        self.start_time = start_time
        self.end_time = end_time
        self.text = text

    @staticmethod
    def format_time(seconds: float) -> str:
        """
        Format time in SRT format (HH:MM:SS,mmm).

        Args:
            seconds: Time in seconds

        Returns:
            Formatted time string
        """
        td = timedelta(seconds=seconds)
        hours = int(td.total_seconds() // 3600)
        minutes = int((td.total_seconds() % 3600) // 60)
        secs = int(td.total_seconds() % 60)
        milliseconds = int((td.total_seconds() % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"

    def to_srt_block(self) -> str:
        """
        Convert segment to SRT format block.

        Returns:
            SRT formatted string block
        """
        start = self.format_time(self.start_time)
        end = self.format_time(self.end_time)
        return f"{self.index}\n{start} --> {end}\n{self.text}\n"

    def __repr__(self):
        return f"SubtitleSegment(index={self.index}, start={self.start_time:.2f}, end={self.end_time:.2f})"


class SubtitleBuilder:
    """Builds SRT subtitle files from transcription and translation data."""

    def __init__(
        self,
        max_line_length: int = 42,
        min_segment_duration: float = 1.0
    ):
        """
        Initialize subtitle builder.

        Args:
            max_line_length: Maximum characters per line
            min_segment_duration: Minimum duration for a segment in seconds
        """
        self.max_line_length = max_line_length
        self.min_segment_duration = min_segment_duration
        self.segments: List[SubtitleSegment] = []

    def add_segment(
        self,
        start_time: float,
        end_time: float,
        text: str
    ):
        """
        Add a subtitle segment.

        Args:
            start_time: Start time in seconds
            end_time: End time in seconds
            text: Subtitle text
        """
        # Ensure minimum duration
        if end_time - start_time < self.min_segment_duration:
            end_time = start_time + self.min_segment_duration

        # Wrap long text
        wrapped_text = self._wrap_text(text)

        # Create segment with 1-based index
        index = len(self.segments) + 1
        segment = SubtitleSegment(index, start_time, end_time, wrapped_text)
        self.segments.append(segment)

    def _wrap_text(self, text: str) -> str:
        """
        Wrap text to fit within max_line_length.

        Args:
            text: Text to wrap

        Returns:
            Wrapped text with line breaks
        """
        if len(text) <= self.max_line_length:
            return text

        # Split into words
        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            word_length = len(word)
            # Account for space
            if current_line:
                word_length += 1

            if current_length + word_length <= self.max_line_length:
                current_line.append(word)
                current_length += word_length
            else:
                # Start new line
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
                current_length = len(word)

        # Add remaining words
        if current_line:
            lines.append(" ".join(current_line))

        return "\n".join(lines)

    def merge_short_segments(self, merge_threshold: float = 2.0):
        """
        Merge segments that are shorter than the threshold.

        Args:
            merge_threshold: Minimum duration in seconds
        """
        if len(self.segments) <= 1:
            return

        merged = []
        i = 0
        while i < len(self.segments):
            current = self.segments[i]
            duration = current.end_time - current.start_time

            # If current segment is too short, try to merge with next
            if duration < merge_threshold and i < len(self.segments) - 1:
                next_seg = self.segments[i + 1]
                # Merge texts
                merged_text = current.text + " " + next_seg.text
                merged_text = self._wrap_text(merged_text)

                # Create merged segment
                merged_seg = SubtitleSegment(
                    len(merged) + 1,
                    current.start_time,
                    next_seg.end_time,
                    merged_text
                )
                merged.append(merged_seg)
                i += 2  # Skip next segment
            else:
                # Keep current segment, update index
                current.index = len(merged) + 1
                merged.append(current)
                i += 1

        self.segments = merged

    def clear(self):
        """Clear all segments."""
        self.segments = []

    def to_srt(self) -> str:
        """
        Convert all segments to SRT format.

        Returns:
            Complete SRT subtitle string
        """
        if not self.segments:
            return ""

        srt_blocks = [segment.to_srt_block() for segment in self.segments]
        return "\n".join(srt_blocks)

    def save_srt(self, output_path: str):
        """
        Save subtitles to SRT file.

        Args:
            output_path: Path to output SRT file
        """
        srt_content = self.to_srt()
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)

    @staticmethod
    def load_srt(srt_path: str) -> 'SubtitleBuilder':
        """
        Load subtitles from SRT file.

        Args:
            srt_path: Path to SRT file

        Returns:
            SubtitleBuilder instance with loaded segments
        """
        builder = SubtitleBuilder()

        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse SRT format
        # Pattern: index \n time_range \n text \n\n
        pattern = r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\Z)'
        matches = re.findall(pattern, content, re.DOTALL)

        for match in matches:
            index = int(match[0])
            start_str = match[1]
            end_str = match[2]
            text = match[3].strip()

            # Parse time
            start_time = SubtitleBuilder._parse_srt_time(start_str)
            end_time = SubtitleBuilder._parse_srt_time(end_str)

            # Add segment
            segment = SubtitleSegment(index, start_time, end_time, text)
            builder.segments.append(segment)

        return builder

    @staticmethod
    def _parse_srt_time(time_str: str) -> float:
        """
        Parse SRT time format to seconds.

        Args:
            time_str: Time string in format HH:MM:SS,mmm

        Returns:
            Time in seconds
        """
        # Format: HH:MM:SS,mmm
        time_parts = time_str.replace(',', '.').split(':')
        hours = int(time_parts[0])
        minutes = int(time_parts[1])
        seconds = float(time_parts[2])

        return hours * 3600 + minutes * 60 + seconds


def create_srt_from_segments(
    segments: List,
    max_line_length: int = 42,
    min_segment_duration: float = 1.0,
    merge_short: bool = True
) -> str:
    """
    Create SRT content from transcription/translation segments.

    Args:
        segments: List of segments with start, end, text attributes
        max_line_length: Maximum characters per line
        min_segment_duration: Minimum duration for a segment
        merge_short: Whether to merge short segments

    Returns:
        SRT formatted string
    """
    builder = SubtitleBuilder(max_line_length, min_segment_duration)

    for segment in segments:
        builder.add_segment(
            start_time=segment.start if hasattr(segment, 'start') else segment['start'],
            end_time=segment.end if hasattr(segment, 'end') else segment['end'],
            text=segment.text if hasattr(segment, 'text') else segment['text']
        )

    if merge_short:
        builder.merge_short_segments()

    return builder.to_srt()
