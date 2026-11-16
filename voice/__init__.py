"""
Voice symptom extraction pipeline.

Multilingual transcription (Whisper) + symptom extraction (LLM).
"""

from .symptom_extractor import transcribe_audio, extract_symptoms

__all__ = ['transcribe_audio', 'extract_symptoms']
