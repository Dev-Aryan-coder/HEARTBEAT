"""
Unit & Integration Tests for SPARK Phase 4: Voice & Speech Presence:
1. Low-Latency Native Speech Engine (SAPI5 with Async Mode)
2. Barge-In Interruption Detection (stop_speaking)
3. Sci-Fi Acoustic Feedback Chimes (play_chime)
4. Dispatcher & Schema Integrity for Phase 4
"""

import os
import sys
import time
sys.path.insert(0, os.path.abspath("."))

from spark_voice_assistant import (
    speak,
    stop_speaking,
    play_chime,
    TOOL_DISPATCHER,
    TOOL_SCHEMAS
)

def test_play_chimes():
    # Should play in daemon thread without throwing exceptions
    play_chime("wake")
    time.sleep(0.1)
    play_chime("success")
    time.sleep(0.1)
    play_chime("interrupt")
    time.sleep(0.1)

def test_stop_speaking_barge_in():
    res = stop_speaking()
    assert "Speech output successfully halted" in res or "Speech engine inactive" in res

def test_speak_async_and_barge_in_purge():
    # Speak in async non-blocking mode
    speak("This is an extended status broadcast that will be immediately interrupted by Master Aryan.", async_mode=True, chime="wake")
    time.sleep(0.05)
    # Trigger instant Barge-In interruption
    res = stop_speaking()
    assert "Speech output successfully halted" in res or "Speech engine inactive" in res

def test_neural_voice_selection():
    from spark_voice_assistant import tool_set_jarvis_voice, ACTIVE_NEURAL_VOICE, NEURAL_VOICE_MAP
    # Test setting to christopher
    res = tool_set_jarvis_voice("christopher")
    assert "Neural voice profile switched to en-US-ChristopherNeural" in res
    # Switch back to true jarvis
    res_jarvis = tool_set_jarvis_voice("jarvis")
    assert "Neural voice profile switched to en-GB-RyanNeural" in res_jarvis

def test_phase4_dispatcher_and_schemas():
    assert "stop_speaking" in TOOL_DISPATCHER
    assert "play_chime" in TOOL_DISPATCHER
    assert "set_jarvis_voice" in TOOL_DISPATCHER

    schema_names = [s["function"]["name"] for s in TOOL_SCHEMAS]
    assert "stop_speaking" in schema_names
    assert "play_chime" in schema_names
    assert "set_jarvis_voice" in schema_names

if __name__ == "__main__":
    tests = [
        test_play_chimes,
        test_stop_speaking_barge_in,
        test_speak_async_and_barge_in_purge,
        test_neural_voice_selection,
        test_phase4_dispatcher_and_schemas
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"PASS: {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"FAIL: {t.__name__} -> {e}")
    print(f"\nTOTAL: {passed}/{len(tests)} PHASE 4 TESTS PASSED.")
