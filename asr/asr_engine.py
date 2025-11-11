"""
Automatic Speech Recognition (ASR) Engine
Uses faster-whisper for efficient Japanese speech-to-text transcription.
"""
from typing import List, Dict, Optional, Callable
from pathlib import Path
import logging

try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None
    logging.warning("faster-whisper not installed. ASR functionality will be disabled.")


class ASRSegment:
    """Represents a single transcribed audio segment."""

    def __init__(self, start: float, end: float, text: str, language: str = "ja"):
        """
        Initialize ASR segment.

        Args:
            start: Start time in seconds
            end: End time in seconds
            text: Transcribed text
            language: Detected or specified language code
        """
        self.start = start
        self.end = end
        self.text = text
        self.language = language

    def __repr__(self):
        return f"ASRSegment(start={self.start:.2f}, end={self.end:.2f}, text='{self.text[:50]}...')"

    def to_dict(self) -> Dict:
        """Convert segment to dictionary."""
        return {
            'start': self.start,
            'end': self.end,
            'text': self.text,
            'language': self.language
        }


class ASREngine:
    """Automatic Speech Recognition engine using faster-whisper."""

    def __init__(
        self,
        model_size: str = "medium",
        compute_type: str = "int8",
        device: str = "cpu",
        device_index: int = 0
    ):
        """
        Initialize ASR engine.

        Args:
            model_size: Whisper model size (tiny, base, small, medium, large-v2, large-v3)
            compute_type: Computation type (int8, float16, float32)
            device: Device to use (cpu, cuda, auto)
            device_index: Device index for multi-GPU setups
        """
        if WhisperModel is None:
            raise ImportError(
                "faster-whisper is not installed. "
                "Please install it with: pip install faster-whisper"
            )

        self.model_size = model_size
        self.compute_type = compute_type
        self.device = device
        self.device_index = device_index
        self.model: Optional[WhisperModel] = None

        logging.info(f"Initializing ASR Engine with model: {model_size}, compute: {compute_type}")

    def load_model(self):
        """Load the Whisper model."""
        if self.model is None:
            try:
                self.model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type,
                    device_index=self.device_index
                )
                logging.info(f"Loaded Whisper model: {self.model_size}")
            except Exception as e:
                logging.error(f"Failed to load Whisper model: {e}")
                raise

    def transcribe(
        self,
        audio_path: str,
        language: str = "ja",
        vad_filter: bool = True,
        beam_size: int = 5,
        initial_prompt: Optional[str] = None,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> List[ASRSegment]:
        """
        Transcribe audio file to text segments.

        Args:
            audio_path: Path to audio/video file
            language: Language code (ja for Japanese)
            vad_filter: Enable Voice Activity Detection filter
            beam_size: Beam size for decoding
            initial_prompt: Optional initial prompt to guide transcription
            progress_callback: Optional callback for progress updates

        Returns:
            List of ASRSegment objects with transcribed text
        """
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Load model if not already loaded
        if self.model is None:
            self.load_model()

        logging.info(f"Starting transcription: {audio_path}")

        try:
            # Transcribe with faster-whisper
            segments, info = self.model.transcribe(
                audio_path,
                language=language,
                beam_size=beam_size,
                vad_filter=vad_filter,
                initial_prompt=initial_prompt
            )

            # Convert to ASRSegment objects
            result_segments = []
            total_duration = info.duration if hasattr(info, 'duration') else None

            for segment in segments:
                asr_segment = ASRSegment(
                    start=segment.start,
                    end=segment.end,
                    text=segment.text.strip(),
                    language=language
                )
                result_segments.append(asr_segment)

                # Call progress callback if provided
                if progress_callback and total_duration:
                    progress = (segment.end / total_duration) * 100
                    progress_callback(progress)

            logging.info(f"Transcription completed: {len(result_segments)} segments")
            return result_segments

        except Exception as e:
            logging.error(f"Transcription failed: {e}")
            raise

    def transcribe_with_language_detection(
        self,
        audio_path: str,
        vad_filter: bool = True,
        beam_size: int = 5,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> List[ASRSegment]:
        """
        Transcribe audio with automatic language detection.

        Args:
            audio_path: Path to audio/video file
            vad_filter: Enable Voice Activity Detection filter
            beam_size: Beam size for decoding
            progress_callback: Optional callback for progress updates

        Returns:
            List of ASRSegment objects with transcribed text
        """
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Load model if not already loaded
        if self.model is None:
            self.load_model()

        logging.info(f"Starting transcription with language detection: {audio_path}")

        try:
            # Transcribe without specifying language (auto-detect)
            segments, info = self.model.transcribe(
                audio_path,
                beam_size=beam_size,
                vad_filter=vad_filter
            )

            detected_language = info.language if hasattr(info, 'language') else 'unknown'
            logging.info(f"Detected language: {detected_language}")

            # Convert to ASRSegment objects
            result_segments = []
            total_duration = info.duration if hasattr(info, 'duration') else None

            for segment in segments:
                asr_segment = ASRSegment(
                    start=segment.start,
                    end=segment.end,
                    text=segment.text.strip(),
                    language=detected_language
                )
                result_segments.append(asr_segment)

                # Call progress callback if provided
                if progress_callback and total_duration:
                    progress = (segment.end / total_duration) * 100
                    progress_callback(progress)

            logging.info(f"Transcription completed: {len(result_segments)} segments")
            return result_segments

        except Exception as e:
            logging.error(f"Transcription failed: {e}")
            raise

    def unload_model(self):
        """Unload the model to free memory."""
        if self.model is not None:
            del self.model
            self.model = None
            logging.info("Whisper model unloaded")

    def is_model_loaded(self) -> bool:
        """Check if model is loaded."""
        return self.model is not None


def create_asr_engine(
    model_size: str = "medium",
    compute_type: str = "int8",
    device: str = "cpu"
) -> ASREngine:
    """
    Factory function to create ASR engine.

    Args:
        model_size: Whisper model size
        compute_type: Computation type
        device: Device to use

    Returns:
        ASREngine instance
    """
    return ASREngine(
        model_size=model_size,
        compute_type=compute_type,
        device=device
    )
