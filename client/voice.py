"""
JARVIS Voice System

Handles both Speech-to-Text (STT) and Text-to-Speech (TTS) for the CLI client.

STT: Records from mic -> sends to OpenAI Whisper API -> returns text
TTS: Two modes:
  - Local (free): pyttsx3 offline engine, works without internet
  - Premium: OpenAI TTS API with 'onyx' voice (deep, JARVIS-like)

Voice is toggle-based to save costs:
  - /voice on|off  -> toggles mic input (Whisper STT)
  - /speak on|off  -> toggles voice output (TTS)
  - /speak premium -> switches to OpenAI TTS (costs money)
  - /speak local   -> switches to pyttsx3 (free)
"""

import io
import os
import tempfile
import threading
from pathlib import Path
from typing import Optional

# Audio recording
try:
    import sounddevice as sd
    import soundfile as sf
    import numpy as np
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

# Local TTS
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

# OpenAI (for Whisper STT and premium TTS)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SAMPLE_RATE = 16000          # 16kHz mono -- optimal for Whisper
SILENCE_THRESHOLD = 0.02     # RMS threshold for silence detection
SILENCE_DURATION = 1.5       # Seconds of silence before auto-stop
MAX_RECORD_SECONDS = 30      # Safety cap on recording length
CHANNELS = 1                 # Mono audio


class VoiceManager:
    """
    Manages voice input (STT) and output (TTS) for the JARVIS CLI.
    
    Usage:
        voice = VoiceManager(openai_api_key="sk-...")
        voice.voice_input_enabled = True   # enable mic
        voice.voice_output_enabled = True  # enable speaking
        
        text = voice.listen()              # record and transcribe
        voice.speak("Hello, Sir.")         # speak text aloud
    """

    def __init__(self, openai_api_key: str = ""):
        # State
        self.voice_input_enabled = False
        self.voice_output_enabled = False
        self.tts_mode = "local"  # "local" (free) or "premium" (OpenAI)

        # OpenAI client for Whisper STT and premium TTS
        self._openai_key = openai_api_key
        self._openai: Optional[OpenAI] = None
        if openai_api_key and OPENAI_AVAILABLE:
            self._openai = OpenAI(api_key=openai_api_key)

        # Local TTS engine (pyttsx3)
        self._local_tts = None
        if PYTTSX3_AVAILABLE:
            try:
                self._local_tts = pyttsx3.init()
                # Configure voice -- slower rate, deeper pitch for JARVIS feel
                self._local_tts.setProperty("rate", 170)  # Default ~200, slower = more deliberate
                self._local_tts.setProperty("volume", 0.9)
                # Try to pick a male voice
                voices = self._local_tts.getProperty("voices")
                for v in voices:
                    if "male" in v.name.lower() or "david" in v.name.lower() or "alex" in v.name.lower():
                        self._local_tts.setProperty("voice", v.id)
                        break
            except Exception:
                self._local_tts = None

    # ------------------------------------------------------------------
    # Capability checks
    # ------------------------------------------------------------------

    @property
    def can_record(self) -> bool:
        """Can we record audio from the mic?"""
        return AUDIO_AVAILABLE

    @property
    def can_transcribe(self) -> bool:
        """Can we transcribe audio (Whisper)?"""
        return self._openai is not None

    @property
    def can_speak_local(self) -> bool:
        """Can we use local TTS?"""
        return self._local_tts is not None

    @property
    def can_speak_premium(self) -> bool:
        """Can we use OpenAI TTS?"""
        return self._openai is not None

    def get_status(self) -> dict:
        """Return voice system status for /voice status."""
        return {
            "voice_input": "ON" if self.voice_input_enabled else "OFF",
            "voice_output": "ON" if self.voice_output_enabled else "OFF",
            "tts_mode": self.tts_mode,
            "mic_available": self.can_record,
            "whisper_available": self.can_transcribe,
            "local_tts_available": self.can_speak_local,
            "premium_tts_available": self.can_speak_premium,
        }

    # ------------------------------------------------------------------
    # Speech-to-Text (STT) -- Mic recording + Whisper transcription
    # ------------------------------------------------------------------

    def listen(self) -> Optional[str]:
        """
        Record audio from the mic until silence is detected,
        then transcribe via OpenAI Whisper.
        
        Returns:
            Transcribed text, or None if recording/transcription failed.
        """
        if not self.can_record:
            return None
        if not self.can_transcribe:
            return None

        audio_data = self._record_until_silence()
        if audio_data is None or len(audio_data) == 0:
            return None

        return self._transcribe(audio_data)

    def _record_until_silence(self) -> Optional[np.ndarray]:
        """
        Record from the default mic until silence is detected.
        Uses a simple RMS-based voice activity detector.
        """
        try:
            frames = []
            silent_frames = 0
            frames_per_chunk = int(SAMPLE_RATE * 0.1)  # 100ms chunks
            silence_chunks_needed = int(SILENCE_DURATION / 0.1)
            max_chunks = int(MAX_RECORD_SECONDS / 0.1)
            started_speaking = False

            with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS,
                                dtype="float32", blocksize=frames_per_chunk) as stream:
                for _ in range(max_chunks):
                    chunk, _ = stream.read(frames_per_chunk)
                    rms = float(np.sqrt(np.mean(chunk ** 2)))

                    if rms > SILENCE_THRESHOLD:
                        started_speaking = True
                        silent_frames = 0
                        frames.append(chunk.copy())
                    elif started_speaking:
                        silent_frames += 1
                        frames.append(chunk.copy())  # Keep trailing silence
                        if silent_frames >= silence_chunks_needed:
                            break
                    # If haven't started speaking yet, keep waiting

            if not frames:
                return None

            return np.concatenate(frames, axis=0)

        except Exception as e:
            print(f"[Voice] Recording error: {e}")
            return None

    def _transcribe(self, audio_data: np.ndarray) -> Optional[str]:
        """Send recorded audio to OpenAI Whisper for transcription."""
        try:
            # Write to a temp WAV file (Whisper API needs a file)
            temp_path = os.path.join(tempfile.gettempdir(), "jarvis_voice.wav")
            sf.write(temp_path, audio_data, SAMPLE_RATE)

            with open(temp_path, "rb") as audio_file:
                transcript = self._openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="en"
                )

            # Clean up
            try:
                os.remove(temp_path)
            except OSError:
                pass

            text = transcript.text.strip()
            return text if text else None

        except Exception as e:
            print(f"[Voice] Transcription error: {e}")
            return None

    # ------------------------------------------------------------------
    # Text-to-Speech (TTS) -- Local (free) or Premium (OpenAI)
    # ------------------------------------------------------------------

    def speak(self, text: str):
        """
        Speak text aloud using the current TTS mode.
        Runs in a separate thread to not block the CLI.
        """
        if not self.voice_output_enabled:
            return

        if not text or not text.strip():
            return

        # Clean text for speech -- remove markdown formatting
        clean = self._clean_for_speech(text)

        if self.tts_mode == "premium" and self.can_speak_premium:
            thread = threading.Thread(target=self._speak_premium, args=(clean,), daemon=True)
            thread.start()
            thread.join(timeout=30)  # Wait but don't block forever
        elif self.can_speak_local:
            # pyttsx3 must run on its own thread due to event loop
            thread = threading.Thread(target=self._speak_local, args=(clean,), daemon=True)
            thread.start()
            thread.join(timeout=30)
        else:
            pass  # No TTS available, silently skip

    def _speak_local(self, text: str):
        """Speak using pyttsx3 (free, offline)."""
        try:
            # pyttsx3 can be finicky with threads, create fresh engine
            engine = pyttsx3.init()
            engine.setProperty("rate", 170)
            engine.setProperty("volume", 0.9)
            # Pick male voice
            voices = engine.getProperty("voices")
            for v in voices:
                if "male" in v.name.lower() or "david" in v.name.lower() or "alex" in v.name.lower():
                    engine.setProperty("voice", v.id)
                    break
            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception as e:
            print(f"[Voice] Local TTS error: {e}")

    def _speak_premium(self, text: str):
        """Speak using OpenAI TTS API (paid, high quality)."""
        try:
            # Truncate to avoid huge bills -- max 4096 chars per request
            if len(text) > 4096:
                text = text[:4096]

            response = self._openai.audio.speech.create(
                model="tts-1",
                voice="onyx",  # Deep male voice -- closest to JARVIS
                input=text,
                response_format="mp3"
            )

            # Save to temp file and play
            temp_path = os.path.join(tempfile.gettempdir(), "jarvis_speak.mp3")
            response.stream_to_file(temp_path)

            # Play using sounddevice + soundfile
            data, samplerate = sf.read(temp_path)
            sd.play(data, samplerate)
            sd.wait()  # Block until playback is done

            try:
                os.remove(temp_path)
            except OSError:
                pass

        except Exception as e:
            print(f"[Voice] Premium TTS error: {e}")

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _clean_for_speech(text: str) -> str:
        """Remove markdown and formatting that sounds weird when spoken."""
        import re
        # Remove code blocks
        text = re.sub(r"```[\s\S]*?```", "code block omitted", text)
        # Remove inline code
        text = re.sub(r"`([^`]+)`", r"\1", text)
        # Remove markdown bold/italic
        text = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", text)
        # Remove markdown headers
        text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
        # Remove markdown links [text](url) -> text
        text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
        # Remove bullet points
        text = re.sub(r"^\s*[-*]\s+", "", text, flags=re.MULTILINE)
        # Collapse multiple newlines
        text = re.sub(r"\n{2,}", ". ", text)
        text = re.sub(r"\n", " ", text)
        # Clean up multiple spaces
        text = re.sub(r"\s{2,}", " ", text)
        return text.strip()
