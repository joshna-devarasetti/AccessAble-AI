"""
Speech Service
Helper utilities for text chunking, speech rate normalization,
and browser Web Speech API capability metadata.
"""

import re
from typing import List, Dict, Any


class SpeechService:
    # Recommended Web Speech API chunk size (characters) to prevent browser TTS silent cutoff
    MAX_CHUNK_CHARS = 220

    @classmethod
    def chunk_text_for_speech(cls, text: str) -> List[str]:
        """
        Splits text into naturally paced sentence chunks so browser SpeechSynthesis
        does not truncate long text or drop utterances.
        """
        if not text or not text.strip():
            return []

        # Split along sentence boundaries (. ! ?) while preserving punctuation
        raw_sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        chunks: List[str] = []
        current_chunk = ""

        for s in raw_sentences:
            s = s.strip()
            if not s:
                continue

            if len(s) > cls.MAX_CHUNK_CHARS:
                # If a single sentence is extra long, split along commas or clauses
                sub_parts = re.split(r"(?<=[,;:])\s+", s)
                for part in sub_parts:
                    if len(current_chunk) + len(part) + 1 <= cls.MAX_CHUNK_CHARS:
                        current_chunk = f"{current_chunk} {part}".strip()
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = part
            else:
                if len(current_chunk) + len(s) + 1 <= cls.MAX_CHUNK_CHARS:
                    current_chunk = f"{current_chunk} {s}".strip()
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = s

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    @staticmethod
    def get_speech_capabilities() -> Dict[str, Any]:
        """
        Returns reference metadata for client Web Speech API implementation.
        """
        return {
            "tts": {
                "engine": "Browser Web Speech API (window.speechSynthesis)",
                "rate_range": {"min": 0.5, "max": 2.0, "default": 1.0},
                "pitch_range": {"min": 0.5, "max": 1.5, "default": 1.0},
                "supported_events": ["start", "pause", "resume", "end", "error"]
            },
            "stt": {
                "engine": "Browser SpeechRecognition (webkitSpeechRecognition)",
                "requires_mic": True,
                "privacy_note": "Speech recognition is performed via your browser's native speech engine. No audio is stored or sent to AccessAble AI servers."
            }
        }
