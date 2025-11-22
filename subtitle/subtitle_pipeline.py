"""
Subtitle Generation Pipeline
Integrates ASR → Translation → SRT generation workflow.
"""
from typing import Optional, Callable, Dict, Any
from pathlib import Path
import logging

from asr.asr_engine import ASREngine, create_asr_engine
from translation.translation_engine import TranslationEngine, create_translation_engine
from subtitle.subtitle_builder import SubtitleBuilder, create_srt_from_segments
from core.cache_manager import CacheManager
from core.config import get_config


class SubtitlePipeline:
    """
    Integrated pipeline for subtitle generation.
    Handles ASR → Translation → SRT generation workflow.
    """

    def __init__(
        self,
        asr_engine: Optional[ASREngine] = None,
        translation_engine: Optional[TranslationEngine] = None,
        cache_manager: Optional[CacheManager] = None
    ):
        """
        Initialize subtitle pipeline.

        Args:
            asr_engine: ASR engine instance (optional, will create from config)
            translation_engine: Translation engine instance (optional, will create from config)
            cache_manager: Cache manager instance (optional, will create from config)
        """
        self.config = get_config()

        # Initialize or use provided engines
        self.asr_engine = asr_engine
        self.translation_engine = translation_engine
        self.cache_manager = cache_manager or CacheManager(self.config.cache_dir)

        logging.info("SubtitlePipeline initialized")

    def _ensure_asr_engine(self):
        """Ensure ASR engine is initialized."""
        if self.asr_engine is None:
            asr_config = self.config.get('asr')
            self.asr_engine = create_asr_engine(
                model_size=asr_config.get('model_size', 'medium'),
                device=asr_config.get('device', 'cpu')
            )
            self.asr_engine.load_model()

    def _ensure_translation_engine(self):
        """Ensure translation engine is initialized."""
        if self.translation_engine is None:
            trans_config = self.config.get('translation')
            model_path = self.config.models_dir / trans_config.get('model_name', 'nllb-200-distilled-600M')

            if not model_path.exists():
                raise FileNotFoundError(
                    f"Translation model not found: {model_path}\n"
                    f"Please download and convert NLLB model to CTranslate2 format."
                )

            # Get device from ASR config (translation uses same device preference)
            device = self.config.get('asr.device', 'auto')

            self.translation_engine = create_translation_engine(
                model_path=str(model_path),
                source_lang=trans_config.get('source_lang', 'jpn_Jpan'),
                target_lang=trans_config.get('target_lang', 'kor_Hang'),
                beam_size=trans_config.get('beam_size', 4),
                batch_size=trans_config.get('batch_size', 32),
                device=device
            )
            self.translation_engine.load_model()

    def generate_subtitles(
        self,
        video_path: str,
        use_cache: bool = True,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> str:
        """
        Generate subtitles for a video file.

        Args:
            video_path: Path to video file
            use_cache: Whether to use cached subtitles if available
            progress_callback: Optional callback(stage: str, progress: float)

        Returns:
            Path to generated SRT file
        """
        video_path = str(Path(video_path).absolute())

        # Check cache first
        if use_cache and self.cache_manager.has_cached_subtitles(video_path):
            logging.info(f"Using cached subtitles for: {video_path}")
            srt_path = self.cache_manager.get_srt_path(video_path)
            if progress_callback:
                progress_callback("cache", 100.0)
            return str(srt_path)

        logging.info(f"Generating subtitles for: {video_path}")

        try:
            # Step 1: ASR (Speech-to-Text)
            if progress_callback:
                progress_callback("asr_init", 0.0)

            self._ensure_asr_engine()

            def asr_progress(prog):
                if progress_callback:
                    progress_callback("asr", prog)

            asr_config = self.config.get('asr')
            asr_segments = self.asr_engine.transcribe(
                audio_path=video_path,
                language=asr_config.get('language', 'ja'),
                progress_callback=asr_progress
            )

            if not asr_segments:
                raise ValueError("No speech detected in video")

            logging.info(f"ASR completed: {len(asr_segments)} segments")

            # Step 2: Translation (Japanese → Korean)
            if progress_callback:
                progress_callback("translation_init", 0.0)

            self._ensure_translation_engine()

            def translation_progress(prog):
                if progress_callback:
                    progress_callback("translation", prog)

            # Extract texts from ASR segments
            texts_to_translate = [seg.text for seg in asr_segments]

            # Translate batch
            translated_texts = self.translation_engine.translate_batch(
                texts=texts_to_translate,
                progress_callback=translation_progress
            )

            logging.info(f"Translation completed: {len(translated_texts)} texts")

            # Step 3: Build SRT
            if progress_callback:
                progress_callback("srt_build", 0.0)

            subtitle_config = self.config.get('subtitle')

            # Create translated segments
            translated_segments = []
            for i, (asr_seg, translated_text) in enumerate(zip(asr_segments, translated_texts)):
                translated_seg = type('obj', (object,), {
                    'start': asr_seg.start,
                    'end': asr_seg.end,
                    'text': translated_text
                })()
                translated_segments.append(translated_seg)

            # Generate SRT content
            srt_content = create_srt_from_segments(
                segments=translated_segments,
                max_line_length=subtitle_config.get('max_line_length', 42),
                min_segment_duration=subtitle_config.get('min_segment_duration', 1.0),
                merge_short=True
            )

            # Save to cache
            self.cache_manager.save_cached_subtitles(video_path, srt_content)

            # Save metadata
            metadata = {
                'video_path': video_path,
                'num_segments': len(asr_segments),
                'asr_model': self.asr_engine.model_size,
                'translation_model': self.translation_engine.model_path.name,
                'source_language': asr_config.get('language', 'ja'),
                'target_language': subtitle_config.get('target_lang', 'ko'),
            }
            self.cache_manager.save_metadata(video_path, metadata)

            if progress_callback:
                progress_callback("complete", 100.0)

            srt_path = self.cache_manager.get_srt_path(video_path)
            logging.info(f"Subtitles generated successfully: {srt_path}")

            return str(srt_path)

        except Exception as e:
            error_msg = f"Failed to generate subtitles: {e}"
            logging.error(error_msg)
            raise RuntimeError(error_msg) from e

    def generate_subtitles_batch(
        self,
        video_paths: list,
        use_cache: bool = True,
        progress_callback: Optional[Callable[[int, int, str, float], None]] = None
    ) -> Dict[str, str]:
        """
        Generate subtitles for multiple videos.

        Args:
            video_paths: List of video file paths
            use_cache: Whether to use cached subtitles if available
            progress_callback: Optional callback(current: int, total: int, stage: str, progress: float)

        Returns:
            Dictionary mapping video paths to SRT file paths
        """
        results = {}
        total = len(video_paths)

        for i, video_path in enumerate(video_paths):
            try:
                def single_progress(stage, prog):
                    if progress_callback:
                        progress_callback(i + 1, total, stage, prog)

                srt_path = self.generate_subtitles(
                    video_path=video_path,
                    use_cache=use_cache,
                    progress_callback=single_progress
                )
                results[video_path] = srt_path

            except Exception as e:
                logging.error(f"Failed to process {video_path}: {e}")
                results[video_path] = None

        return results

    def clear_cache(self):
        """Clear all cached subtitles."""
        self.cache_manager.clear_all_cache()

    def get_cached_subtitle_path(self, video_path: str) -> Optional[str]:
        """
        Get path to cached subtitle for a video.

        Args:
            video_path: Path to video file

        Returns:
            Path to cached SRT file, or None if not cached
        """
        if self.cache_manager.has_cached_subtitles(video_path):
            return str(self.cache_manager.get_srt_path(video_path))
        return None

    def cleanup(self):
        """Clean up resources."""
        if self.asr_engine:
            self.asr_engine.unload_model()
        if self.translation_engine:
            self.translation_engine.unload_model()
        logging.info("SubtitlePipeline cleaned up")


def create_subtitle_pipeline(
    asr_model_size: str = "medium",
    translation_model_path: Optional[str] = None
) -> SubtitlePipeline:
    """
    Factory function to create subtitle pipeline.

    Args:
        asr_model_size: Whisper model size
        translation_model_path: Path to translation model (optional)

    Returns:
        SubtitlePipeline instance
    """
    config = get_config()

    # Create ASR engine
    asr_engine = create_asr_engine(
        model_size=asr_model_size,
        device=config.get('asr.device', 'cpu')
    )

    # Create translation engine if model path provided
    translation_engine = None
    if translation_model_path:
        trans_config = config.get('translation')
        device = config.get('asr.device', 'auto')
        translation_engine = create_translation_engine(
            model_path=translation_model_path,
            source_lang=trans_config.get('source_lang', 'jpn_Jpan'),
            target_lang=trans_config.get('target_lang', 'kor_Hang'),
            device=device
        )

    # Create cache manager
    cache_manager = CacheManager(config.cache_dir)

    return SubtitlePipeline(
        asr_engine=asr_engine,
        translation_engine=translation_engine,
        cache_manager=cache_manager
    )
