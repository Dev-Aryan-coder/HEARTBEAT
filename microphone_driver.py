"""
=============================================================================
⚡ SPARK NATIVE HARDWARE MICROPHONE DRIVER (SOUNDDEVICE + WASAPI / MME)
=============================================================================
Zero-dependency native Windows microphone stream capture for Python 3.14.
Bypasses PyAudio build errors by using hardware-accelerated sounddevice
to stream directly from Master Aryan's Realtek(R) Audio microphone.
=============================================================================
"""

import time
import math
import numpy as np
import sounddevice as sd
import speech_recognition as sr
from typing import Optional, Tuple

SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_DURATION = 0.15  # 150ms audio chunk
CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_DURATION)

def is_microphone_available() -> Tuple[bool, str]:
    """Checks if a valid physical microphone is connected and active."""
    try:
        devices = sd.query_devices()
        default_in = sd.default.device[0]
        if default_in is not None and default_in >= 0:
            dev_name = devices[default_in]["name"]
            return True, dev_name
        # Search for Realtek
        for d in devices:
            if d.get("max_input_channels", 0) > 0 and "realtek" in d.get("name", "").lower():
                return True, d.get("name")
        return False, "No active input device found"
    except Exception as e:
        return False, str(e)

_AMBIENT_BASELINE = 150.0

def capture_phrase_from_mic(
    timeout: float = 5.0,
    phrase_time_limit: float = 8.0,
    silence_limit: float = 0.7
) -> Optional[sr.AudioData]:
    """
    Zero-delay streaming microphone capture with rolling ambient baseline.
    Instantly detects speech start without 0.3s blocking gap.
    """
    global _AMBIENT_BASELINE
    recorded_chunks = []
    speaking_started = False
    silence_chunks_count = 0
    max_silence_chunks = int(silence_limit / CHUNK_DURATION)
    max_total_chunks = int(phrase_time_limit / CHUNK_DURATION)

    start_wait = time.time()

    try:
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='int16') as stream:
            while True:
                chunk, overflowed = stream.read(CHUNK_SAMPLES)
                rms = float(np.sqrt(np.mean(np.square(chunk.astype(np.float32)))))

                if not speaking_started:
                    # Update rolling noise floor
                    _AMBIENT_BASELINE = 0.85 * _AMBIENT_BASELINE + 0.15 * min(rms, 400.0)
                    trigger_threshold = max(_AMBIENT_BASELINE * 1.45, 180.0)

                    if rms > trigger_threshold:
                        speaking_started = True
                        recorded_chunks.append(chunk.copy())
                    else:
                        if timeout and (time.time() - start_wait) > timeout:
                            return None
                else:
                    recorded_chunks.append(chunk.copy())
                    if rms < max(_AMBIENT_BASELINE * 1.25, 150.0):
                        silence_chunks_count += 1
                        if silence_chunks_count >= max_silence_chunks:
                            break
                    else:
                        silence_chunks_count = 0

                    if len(recorded_chunks) >= max_total_chunks:
                        break

    except Exception as e:
        print(f"[Mic Driver Stream Notice: {e}]")
        return None

    if not recorded_chunks or len(recorded_chunks) < 2:
        return None

    full_audio = np.concatenate(recorded_chunks, axis=0)
    raw_bytes = full_audio.tobytes()
    return sr.AudioData(raw_bytes, SAMPLE_RATE, 2)

def recognize_live_speech(
    timeout: float = 5.0,
    phrase_time_limit: float = 8.0,
    verify_speaker: bool = False
) -> Optional[str]:
    """
    Captures live microphone audio, transcribes it, and optionally validates speaker voiceprint.
    """
    audio = capture_phrase_from_mic(timeout=timeout, phrase_time_limit=phrase_time_limit)
    if not audio:
        return None

    if verify_speaker:
        try:
            from speaker_biometrics import verify_speaker_is_aryan
            raw = np.frombuffer(audio.get_raw_data(), dtype=np.int16).astype(np.float32) / 32768.0
            is_aryan, score = verify_speaker_is_aryan(raw, sr=SAMPLE_RATE, threshold=0.52)
            if not is_aryan:
                print(f"🚫 [BIOMETRIC FILTER]: Voice similarity {score*100:.1f}% below threshold. Ignored.")
                return None
            else:
                print(f"✅ [BIOMETRIC MATCH]: Master Aryan verified (Similarity: {score*100:.1f}%)")
        except Exception:
            pass

    try:
        r = sr.Recognizer()
        text = r.recognize_google(audio)
        return text.strip()
    except Exception:
        return None
