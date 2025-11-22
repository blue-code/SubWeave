"""
Automatic Speech Recognition (ASR) Engine
Uses OpenAI Whisper (open-source) for efficient Japanese speech-to-text transcription.
"""
from typing import List, Dict, Optional, Callable
from pathlib import Path
import logging

try:
    import whisper
except ImportError:
    whisper = None
    logging.warning("openai-whisper not installed. ASR functionality will be disabled.")


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
    """Automatic Speech Recognition engine using OpenAI Whisper (open-source)."""

    def __init__(
        self,
        model_size: str = "medium",
        device: str = "cpu"
    ):
        """
        Initialize ASR engine.

        Args:
            model_size: Whisper model size (tiny, base, small, medium, large, large-v2, large-v3)
            device: Device to use (cpu, cuda, or mps for Apple Silicon GPU)
        """
        if whisper is None:
            raise ImportError(
                "openai-whisper is not installed. "
                "Please install it with: pip install openai-whisper"
            )

        self.model_size = model_size
        self.device = self._validate_device(device)
        self.model: Optional[object] = None

        logging.info(f"Initializing ASR Engine with model: {model_size}, device: {self.device}")

    def _validate_device(self, device: str) -> str:
        """
        Validate and adjust device setting based on availability.

        Args:
            device: Requested device (cpu, cuda, mps)

        Returns:
            Valid device string
        """
        if device == "mps":
            try:
                import torch
                if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                    logging.info("Using Apple Silicon GPU (MPS) for acceleration")
                    return "mps"
                else:
                    logging.warning("MPS requested but not available, falling back to CPU")
                    return "cpu"
            except ImportError:
                logging.warning("PyTorch not available, falling back to CPU")
                return "cpu"
        elif device == "cuda":
            try:
                import torch
                if torch.cuda.is_available():
                    logging.info(f"Using CUDA GPU: {torch.cuda.get_device_name(0)}")
                    return "cuda"
                else:
                    logging.warning("CUDA requested but not available, falling back to CPU")
                    return "cpu"
            except ImportError:
                logging.warning("PyTorch not available, falling back to CPU")
                return "cpu"
        else:
            return "cpu"

    def load_model(self):
        """Load the Whisper model."""
        if self.model is None:
            try:
                self.model = whisper.load_model(self.model_size, device=self.device)
                logging.info(f"Loaded Whisper model: {self.model_size}")
            except Exception as e:
                logging.error(f"Failed to load Whisper model: {e}")
                raise

    def transcribe(
        self,
        audio_path: str,
        language: str = "ja",
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> List[ASRSegment]:
        """
        Transcribe audio file to text segments.

        Args:
            audio_path: Path to audio/video file
            language: Language code (ja for Japanese)
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
            # Transcribe with openai-whisper
            result = self.model.transcribe(
                audio_path,
                language=language,
                verbose=False
            )

            # Convert to ASRSegment objects
            result_segments = []
            total_duration = None

            # Get duration from segments if available
            if result.get('segments'):
                last_segment = result['segments'][-1]
                total_duration = last_segment.get('end', 0)

            for segment in result.get('segments', []):
                asr_segment = ASRSegment(
                    start=segment['start'],
                    end=segment['end'],
                    text=segment['text'].strip(),
                    language=language
                )
                result_segments.append(asr_segment)

                # Call progress callback if provided
                if progress_callback and total_duration:
                    progress = (segment['end'] / total_duration) * 100
                    progress_callback(progress)

            logging.info(f"Transcription completed: {len(result_segments)} segments")
            return result_segments

        except Exception as e:
            logging.error(f"Transcription failed: {e}")
            raise

    def transcribe_with_language_detection(
        self,
        audio_path: str,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> List[ASRSegment]:
        """
        Transcribe audio with automatic language detection.

        Args:
            audio_path: Path to audio/video file
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
            result = self.model.transcribe(
                audio_path,
                verbose=False
            )

            detected_language = result.get('language', 'unknown')
            logging.info(f"Detected language: {detected_language}")

            # Convert to ASRSegment objects
            result_segments = []
            total_duration = None

            # Get duration from segments if available
            if result.get('segments'):
                last_segment = result['segments'][-1]
                total_duration = last_segment.get('end', 0)

            for segment in result.get('segments', []):
                asr_segment = ASRSegment(
                    start=segment['start'],
                    end=segment['end'],
                    text=segment['text'].strip(),
                    language=detected_language
                )
                result_segments.append(asr_segment)

                # Call progress callback if provided
                if progress_callback and total_duration:
                    progress = (segment['end'] / total_duration) * 100
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
    device: str = "cpu"
) -> ASREngine:
    """
    Factory function to create ASR engine.

    Args:
        model_size: Whisper model size
        device: Device to use

    Returns:
        ASREngine instance
    """
    return ASREngine(
        model_size=model_size,
        device=device
    )
