"""System audio capture using sounddevice."""

import queue
from typing import Optional

import numpy as np
import sounddevice as sd


class AudioCapture:
    """Captures system audio using sounddevice (PortAudio bindings)."""

    def __init__(
        self,
        device: Optional[str] = None,
        sample_rate: int = 16000,
        channels: int = 1,
        chunk_duration: float = 0.5,  # seconds
    ):
        self.device = device
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = int(sample_rate * chunk_duration)
        self.audio_queue: queue.Queue[np.ndarray] = queue.Queue()
        self.stream: Optional[sd.InputStream] = None

    def _find_device_index(self) -> Optional[int]:
        """Find the device index by name."""
        if self.device is None:
            return None

        devices = sd.query_devices()
        for i, d in enumerate(devices):
            if self.device.lower() in d["name"].lower() and d["max_input_channels"] > 0:
                return i

        return None

    def _audio_callback(self, indata, frames, time_info, status):
        """Called by sounddevice for each audio chunk."""
        if status:
            # Log status but don't crash
            pass
        # Copy data to queue for processing
        self.audio_queue.put(indata.copy())

    def start(self):
        """Start audio capture."""
        device_index = self._find_device_index()

        self.stream = sd.InputStream(
            device=device_index,
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="float32",
            blocksize=self.chunk_size,
            callback=self._audio_callback,
        )
        self.stream.start()

    def stop(self):
        """Stop audio capture."""
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    def get_chunk(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        """Get an audio chunk from the queue.

        Returns None if no chunk is available within timeout.
        """
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None
