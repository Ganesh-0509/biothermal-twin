"""
Multilingual voice symptom extraction for heat stress triage.

Uses:
- Faster-Whisper (local) for speech-to-text (Hindi/Arabic)
- GPT-4o-mini for symptom extraction (fallback if Med42 unavailable)
"""

import os
import json
from pathlib import Path
from typing import Dict, Optional
import openai

# Try to import faster_whisper (local Whisper)
try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("[WARNING] faster-whisper not installed. Using OpenAI Whisper API as fallback.")


# Global Whisper model (lazy loaded)
_whisper_model = None


def get_whisper_model():
    """
    Get or initialize local Whisper model.

    Uses 'base' model (74M params, good balance of speed/accuracy).
    Runs on CPU or GPU automatically.
    """
    global _whisper_model

    if _whisper_model is None:
        if not WHISPER_AVAILABLE:
            raise RuntimeError("faster-whisper not installed. Install with: pip install faster-whisper")

        print("[*] Loading Whisper model (base)...")

        # Try GPU first, fallback to CPU
        try:
            _whisper_model = WhisperModel("base", device="cuda", compute_type="float16")
            print("    Using GPU (CUDA)")
        except:
            _whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
            print("    Using CPU (int8)")

    return _whisper_model


def transcribe_audio(
    audio_path: str,
    language: Optional[str] = None
) -> Dict[str, any]:
    """
    Transcribe audio file to text.

    Args:
        audio_path: Path to audio file (WAV, MP3, M4A)
        language: Language code ('hi' for Hindi, 'ar' for Arabic, None for auto-detect)

    Returns:
        Dict with:
            text: Transcribed text
            language: Detected/specified language code
            confidence: Transcription confidence (0-1)
            segments: List of timestamped segments

    Supported languages:
        - 'hi': Hindi
        - 'ar': Arabic
        - 'ur': Urdu
        - 'ml': Malayalam
        - 'tl': Tagalog
        - 'en': English
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    if WHISPER_AVAILABLE:
        # Use local Whisper model
        model = get_whisper_model()

        segments, info = model.transcribe(
            audio_path,
            language=language,
            beam_size=5,
            vad_filter=True  # Voice activity detection (remove silence)
        )

        # Collect all segments
        segment_list = []
        full_text = []

        for segment in segments:
            segment_list.append({
                'start': segment.start,
                'end': segment.end,
                'text': segment.text.strip()
            })
            full_text.append(segment.text.strip())

        return {
            'text': ' '.join(full_text),
            'language': info.language,
            'confidence': info.language_probability,
            'segments': segment_list,
            'duration': info.duration
        }

    else:
        # Fallback to OpenAI Whisper API
        print("[*] Using OpenAI Whisper API (fallback)")

        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set in environment")

        openai.api_key = api_key

        with open(audio_path, 'rb') as audio_file:
            response = openai.Audio.transcribe(
                model="whisper-1",
                file=audio_file,
                language=language
            )

        return {
            'text': response['text'],
            'language': language or 'unknown',
            'confidence': 1.0,  # API doesn't return confidence
            'segments': [],
            'duration': None
        }


def extract_symptoms(
    transcription: str,
    language: str = 'hi'
) -> Dict[str, any]:
    """
    Extract heat stress symptoms from transcribed text.

    Uses LLM to identify clinical symptoms from worker's statement.

    Args:
        transcription: Transcribed text from worker
        language: Language code (for context)

    Returns:
        Dict with:
            dark_urine: bool (oliguria/dark urine indicator)
            muscle_cramps: bool (muscle fasciculations/cramps)
            dizziness: bool (dizziness/confusion)
            fatigue: str ('NONE', 'MILD', 'MODERATE', 'SEVERE')
            headache: bool
            risk_score: float (0-1, overall symptom severity)
            raw_response: str (LLM full response)
    """
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set in environment")

    openai.api_key = api_key

    # Language name mapping
    lang_names = {
        'hi': 'Hindi',
        'ar': 'Arabic',
        'ur': 'Urdu',
        'ml': 'Malayalam',
        'tl': 'Tagalog',
        'en': 'English'
    }
    lang_name = lang_names.get(language, language)

    # Prompt for symptom extraction
    prompt = f"""You are a medical triage assistant for occupational heat stress.

Worker statement (in {lang_name}): "{transcription}"

Extract the following heat stress symptoms:
1. Dark urine or reduced urination (oliguria): YES or NO
2. Muscle cramps or fasciculations: YES or NO
3. Dizziness or confusion: YES or NO
4. Severe fatigue: NONE, MILD, MODERATE, or SEVERE
5. Headache: YES or NO

Calculate an overall risk score (0.0 to 1.0) based on symptom severity:
- 0.0-0.3: Low risk (no significant symptoms)
- 0.3-0.6: Moderate risk (some symptoms present)
- 0.6-0.8: High risk (multiple symptoms)
- 0.8-1.0: Critical risk (severe/multiple symptoms)

Return ONLY valid JSON in this exact format (no other text):
{{
  "dark_urine": true/false,
  "muscle_cramps": true/false,
  "dizziness": true/false,
  "fatigue": "NONE|MILD|MODERATE|SEVERE",
  "headache": true/false,
  "risk_score": 0.0-1.0
}}"""

    try:
        # Call GPT-4o-mini (fast, cheap, good for structured output)
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a medical triage assistant. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Low temperature for consistent structured output
            max_tokens=150
        )

        raw_response = response.choices[0].message.content.strip()

        # Parse JSON response
        symptoms = json.loads(raw_response)

        # Validate required fields
        required_fields = ['dark_urine', 'muscle_cramps', 'dizziness', 'fatigue', 'headache', 'risk_score']
        for field in required_fields:
            if field not in symptoms:
                raise ValueError(f"Missing required field: {field}")

        # Add metadata
        symptoms['raw_response'] = raw_response
        symptoms['transcription'] = transcription
        symptoms['language'] = language

        return symptoms

    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse LLM response as JSON: {e}")
        print(f"Raw response: {raw_response}")

        # Return safe default
        return {
            'dark_urine': False,
            'muscle_cramps': False,
            'dizziness': False,
            'fatigue': 'NONE',
            'headache': False,
            'risk_score': 0.0,
            'raw_response': raw_response,
            'transcription': transcription,
            'language': language,
            'error': str(e)
        }


def process_voice_checkin(audio_path: str, language: Optional[str] = None) -> Dict[str, any]:
    """
    Complete voice check-in pipeline: transcribe + extract symptoms.

    Args:
        audio_path: Path to audio file
        language: Language code (None for auto-detect)

    Returns:
        Dict with transcription and symptoms
    """
    print(f"[*] Processing voice check-in: {audio_path}")

    # Step 1: Transcribe
    transcription_result = transcribe_audio(audio_path, language)
    print(f"    Transcribed ({transcription_result['language']}): {transcription_result['text'][:100]}...")

    # Step 2: Extract symptoms
    symptoms = extract_symptoms(
        transcription_result['text'],
        transcription_result['language']
    )
    print(f"    Risk score: {symptoms['risk_score']:.2f}")

    # Combine results
    return {
        'transcription': transcription_result,
        'symptoms': symptoms,
        'timestamp': None,  # Will be added by backend
        'worker_id': None   # Will be added by backend
    }


if __name__ == "__main__":
    # Test script
    print("\n" + "=" * 60)
    print("VOICE SYMPTOM EXTRACTION TEST")
    print("=" * 60 + "\n")

    # Test with sample text (no audio file needed for testing extraction)
    test_cases = [
        {
            'text': "मुझे चक्कर आ रहा है और बहुत थकान महसूस हो रही है",
            'language': 'hi',
            'expected': 'dizziness + severe fatigue'
        },
        {
            'text': "أشعر بتشنجات في العضلات والبول داكن اللون",
            'language': 'ar',
            'expected': 'muscle cramps + dark urine'
        },
        {
            'text': "I'm fine, no problems",
            'language': 'en',
            'expected': 'no symptoms'
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['expected']}")
        print(f"  Input ({test['language']}): {test['text']}")

        try:
            symptoms = extract_symptoms(test['text'], test['language'])
            print(f"  Dark urine: {symptoms['dark_urine']}")
            print(f"  Muscle cramps: {symptoms['muscle_cramps']}")
            print(f"  Dizziness: {symptoms['dizziness']}")
            print(f"  Fatigue: {symptoms['fatigue']}")
            print(f"  Risk score: {symptoms['risk_score']:.2f}")
            print(f"  [SUCCESS]")
        except Exception as e:
            print(f"  [ERROR] {e}")

        print()

    print("[*] Voice pipeline test complete")
