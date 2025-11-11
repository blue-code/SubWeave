"""
Machine Translation Engine
Uses CTranslate2 with NLLB-200 for Japanese to Korean translation.
"""
from typing import List, Optional, Callable
from pathlib import Path
import logging

try:
    import ctranslate2
    import sentencepiece as spm
except ImportError:
    ctranslate2 = None
    spm = None
    logging.warning("ctranslate2 or sentencepiece not installed. Translation functionality will be disabled.")


class TranslationEngine:
    """Machine translation engine using CTranslate2 and NLLB-200."""

    def __init__(
        self,
        model_path: str,
        source_lang: str = "jpn_Jpan",
        target_lang: str = "kor_Hang",
        beam_size: int = 4,
        batch_size: int = 32
    ):
        """
        Initialize translation engine.

        Args:
            model_path: Path to CTranslate2 converted model
            source_lang: Source language code (FLORES-200)
            target_lang: Target language code (FLORES-200)
            beam_size: Beam size for decoding
            batch_size: Batch size for translation
        """
        if ctranslate2 is None or spm is None:
            raise ImportError(
                "ctranslate2 or sentencepiece not installed. "
                "Please install them with: pip install ctranslate2 sentencepiece"
            )

        self.model_path = Path(model_path)
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.beam_size = beam_size
        self.batch_size = batch_size

        self.translator: Optional[ctranslate2.Translator] = None
        self.sp_src: Optional[spm.SentencePieceProcessor] = None
        self.sp_tgt: Optional[spm.SentencePieceProcessor] = None

        logging.info(f"Initializing Translation Engine: {source_lang} → {target_lang}")

    def load_model(self):
        """Load translation model and tokenizers."""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {self.model_path}")

        try:
            # Load CTranslate2 model
            self.translator = ctranslate2.Translator(str(self.model_path))
            logging.info(f"Loaded CTranslate2 model from: {self.model_path}")

            # Load SentencePiece tokenizers
            source_spm_path = self.model_path / "source.spm"
            target_spm_path = self.model_path / "target.spm"

            # Try loading tokenizers (may not exist for some models)
            if source_spm_path.exists():
                self.sp_src = spm.SentencePieceProcessor(model_file=str(source_spm_path))
                logging.info(f"Loaded source tokenizer: {source_spm_path}")
            else:
                # Use shared tokenizer if source-specific doesn't exist
                shared_spm_path = self.model_path / "sentencepiece.model"
                if shared_spm_path.exists():
                    self.sp_src = spm.SentencePieceProcessor(model_file=str(shared_spm_path))
                    logging.info(f"Loaded shared tokenizer: {shared_spm_path}")

            if target_spm_path.exists():
                self.sp_tgt = spm.SentencePieceProcessor(model_file=str(target_spm_path))
                logging.info(f"Loaded target tokenizer: {target_spm_path}")
            else:
                # Use shared tokenizer if target-specific doesn't exist
                shared_spm_path = self.model_path / "sentencepiece.model"
                if shared_spm_path.exists():
                    self.sp_tgt = spm.SentencePieceProcessor(model_file=str(shared_spm_path))

        except Exception as e:
            logging.error(f"Failed to load translation model: {e}")
            raise

    def translate_text(self, text: str) -> str:
        """
        Translate a single text string.

        Args:
            text: Text to translate

        Returns:
            Translated text
        """
        if not text or text.strip() == "":
            return ""

        results = self.translate_batch([text])
        return results[0] if results else ""

    def translate_batch(
        self,
        texts: List[str],
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> List[str]:
        """
        Translate a batch of texts.

        Args:
            texts: List of texts to translate
            progress_callback: Optional callback for progress updates

        Returns:
            List of translated texts
        """
        if not texts:
            return []

        # Load model if not already loaded
        if self.translator is None:
            self.load_model()

        logging.info(f"Translating {len(texts)} texts...")

        try:
            # Filter out empty texts and keep track of indices
            non_empty_texts = []
            non_empty_indices = []
            for i, text in enumerate(texts):
                if text and text.strip():
                    non_empty_texts.append(text.strip())
                    non_empty_indices.append(i)

            if not non_empty_texts:
                return ["" for _ in texts]

            # Tokenize source texts
            if self.sp_src:
                source_tokens = [
                    self.sp_src.encode_as_pieces(text) + ["</s>", self.source_lang]
                    for text in non_empty_texts
                ]
            else:
                # Fallback: use simple whitespace tokenization
                source_tokens = [
                    text.split() + ["</s>", self.source_lang]
                    for text in non_empty_texts
                ]

            # Translate in batches
            all_translations = []
            total_batches = (len(source_tokens) + self.batch_size - 1) // self.batch_size

            for batch_idx in range(total_batches):
                start_idx = batch_idx * self.batch_size
                end_idx = min(start_idx + self.batch_size, len(source_tokens))
                batch_tokens = source_tokens[start_idx:end_idx]

                # Translate batch
                results = self.translator.translate_batch(
                    batch_tokens,
                    beam_size=self.beam_size,
                    target_prefix=[[self.target_lang]] * len(batch_tokens)
                )

                # Decode results
                for result in results:
                    if self.sp_tgt:
                        # Remove target language token and decode
                        hypothesis = result.hypotheses[0]
                        tokens = [t for t in hypothesis if t != self.target_lang]
                        translated = self.sp_tgt.decode(tokens)
                    else:
                        # Fallback: simple join
                        hypothesis = result.hypotheses[0]
                        translated = " ".join([t for t in hypothesis if t != self.target_lang])

                    all_translations.append(translated.strip())

                # Call progress callback
                if progress_callback:
                    progress = ((batch_idx + 1) / total_batches) * 100
                    progress_callback(progress)

            # Reconstruct full results with empty strings where needed
            final_results = [""] * len(texts)
            for i, translation in zip(non_empty_indices, all_translations):
                final_results[i] = translation

            logging.info(f"Translation completed: {len(non_empty_texts)} texts")
            return final_results

        except Exception as e:
            logging.error(f"Translation failed: {e}")
            raise

    def unload_model(self):
        """Unload the model to free memory."""
        if self.translator is not None:
            del self.translator
            self.translator = None
        if self.sp_src is not None:
            del self.sp_src
            self.sp_src = None
        if self.sp_tgt is not None:
            del self.sp_tgt
            self.sp_tgt = None
        logging.info("Translation model unloaded")

    def is_model_loaded(self) -> bool:
        """Check if model is loaded."""
        return self.translator is not None


def create_translation_engine(
    model_path: str,
    source_lang: str = "jpn_Jpan",
    target_lang: str = "kor_Hang",
    beam_size: int = 4,
    batch_size: int = 32
) -> TranslationEngine:
    """
    Factory function to create translation engine.

    Args:
        model_path: Path to CTranslate2 model
        source_lang: Source language code
        target_lang: Target language code
        beam_size: Beam size for decoding
        batch_size: Batch size for translation

    Returns:
        TranslationEngine instance
    """
    return TranslationEngine(
        model_path=model_path,
        source_lang=source_lang,
        target_lang=target_lang,
        beam_size=beam_size,
        batch_size=batch_size
    )
