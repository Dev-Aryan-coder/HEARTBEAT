"""
Unit and integration tests for SPARK 24/7 Sentinel, Wake Word perception,
Autosave on hard shutdown, and Windows autostart configuration.
"""

import os
import sys
import json
import time

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

from spark_sentinel_daemon import (
    check_for_wake_phrase,
    autosave_all_state,
    restore_session_state,
    CHECKPOINT_FILE
)
from setup_spark_autostart import (
    STARTUP_FOLDER,
    VBS_PATH,
    REG_NAME
)

def test_wake_phrase_detection():
    print("Testing Wake Word Greetings...")
    test_cases = [
        ("hey spark what time is it", True, "what time is it"),
        ("hello spark open chrome", True, "open chrome"),
        ("yo spark how are you doing", True, "how are you doing"),
        ("hi spark", True, ""),
        ("ok spark clean temp files", True, "clean temp files"),
        ("okay spark take screenshot", True, "take screenshot"),
        ("wake up spark", True, ""),
        ("spark tell me a joke", True, "tell me a joke"),
        ("just talking about something else", False, ""),
    ]

    for phrase, expected_match, expected_cmd in test_cases:
        matched, cmd = check_for_wake_phrase(phrase)
        assert matched == expected_match, f"Failed match on: '{phrase}', got {matched}"
        if expected_match:
            assert cmd == expected_cmd, f"Failed cmd extraction on: '{phrase}', expected '{expected_cmd}', got '{cmd}'"
    print("✅ All wake word phrases passed!")

def test_autosave_and_restore():
    print("Testing Autosave and Persistence...")
    autosave_all_state(reason="test_power_cut_verification")
    assert os.path.exists(CHECKPOINT_FILE), "Checkpoint file was not created!"

    with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["master"] == "Aryan"
    assert data["status"] == "persistent_online"
    assert data["reason"] == "test_power_cut_verification"

    restored = restore_session_state()
    assert restored is not None
    assert restored["master"] == "Aryan"
    print("✅ Autosave and restore passed!")

def test_autostart_files():
    print("Testing Windows Autostart Registration...")
    assert os.path.exists(VBS_PATH), f"Startup VBScript not found at {VBS_PATH}"
    with open(VBS_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    assert "pythonw.exe" in content
    assert "spark_sentinel_daemon.py" in content
    print("✅ Windows Startup VBScript verified!")

if __name__ == "__main__":
    test_wake_phrase_detection()
    test_autosave_and_restore()
    test_autostart_files()
    print("\n🎉 ALL 24/7 SENTINEL PERSISTENCE TESTS PASSED!")
