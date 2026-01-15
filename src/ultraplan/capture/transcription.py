"""Real-time Whisper transcription worker."""

from typing import Callable, Optional

import numpy as np


class TranscriptionWorker:
    """Handles real-time audio transcription using faster-whisper."""

    def __init__(
        self,
        model_size: str = "base",
        on_transcript: Optional[Callable[[str, float, bool], None]] = None,
        buffer_duration: float = 3.0,  # Accumulate audio before transcribing
        sample_rate: int = 16000,
        vocabulary_boost: Optional[list[str]] = None,  # Words to boost recognition
    ):
        self.model_size = model_size
        self.on_transcript = on_transcript
        self.buffer_duration = buffer_duration
        self.sample_rate = sample_rate
        self.vocabulary_boost = vocabulary_boost or []

        self.model = None
        self.audio_buffer: list[np.ndarray] = []
        self.buffer_samples = 0
        self.target_samples = int(sample_rate * buffer_duration)

        # Build initial prompt to bias Whisper toward our vocabulary
        self.initial_prompt = self._build_initial_prompt()

    def _build_initial_prompt(self) -> str:
        """Build an initial prompt that biases Whisper toward our vocabulary.

        The initial_prompt tells Whisper what kind of words/style to expect,
        which significantly improves recognition of uncommon words.
        """
        if not self.vocabulary_boost:
            return ""

        # Create a prompt that includes the words naturally
        # Whisper works best when words appear in context
        words = ", ".join(self.vocabulary_boost)
        prompt = f"Voice commands include: {words}. "
        return prompt

    def load_model(self):
        """Load Whisper model - call once at startup."""
        from faster_whisper import WhisperModel

        # Determine device and compute type
        device = "cpu"
        compute_type = "int8"

        try:
            import torch

            if torch.cuda.is_available():
                device = "cuda"
                compute_type = "float16"
            # Note: faster-whisper doesn't support MPS yet, use CPU for Apple Silicon
        except ImportError:
            pass

        self.model = WhisperModel(
            self.model_size,
            device=device,
            compute_type=compute_type,
        )

    def add_audio(self, chunk: np.ndarray):
        """Add audio chunk to buffer.

        When buffer has enough audio, triggers transcription.
        """
        self.audio_buffer.append(chunk)
        self.buffer_samples += len(chunk)

        # Check if we have enough audio to transcribe
        if self.buffer_samples >= self.target_samples:
            self._transcribe_buffer()

    def flush(self):
        """Transcribe any remaining audio in buffer."""
        if self.audio_buffer and self.buffer_samples > self.sample_rate * 0.5:
            # Only transcribe if at least 0.5 seconds of audio
            self._transcribe_buffer()

    def _transcribe_buffer(self):
        """Transcribe accumulated audio buffer."""
        if not self.audio_buffer or self.model is None:
            return

        # Concatenate audio chunks
        audio = np.concatenate(self.audio_buffer, axis=0)
        audio = audio.flatten().astype(np.float32)

        # Clear buffer
        self.audio_buffer = []
        self.buffer_samples = 0

        # Skip if audio is too quiet (likely silence)
        if np.abs(audio).max() < 0.01:
            return

        # Transcribe
        try:
            segments, info = self.model.transcribe(
                audio,
                beam_size=1,  # Faster for real-time
                language="en",
                vad_filter=True,  # Filter silence
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                ),
                initial_prompt=self.initial_prompt if self.initial_prompt else None,
            )

            # Collect segments
            text_parts = []
            for segment in segments:
                text = segment.text.strip()
                if text:
                    text_parts.append(text)

            if text_parts and self.on_transcript:
                full_text = " ".join(text_parts)
                self.on_transcript(full_text, info.language_probability, False)

        except Exception as e:
            # Don't crash on transcription errors
            print(f"Transcription error: {e}")
