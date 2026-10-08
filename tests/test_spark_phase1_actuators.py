"""
Unit & Integration Tests for SPARK Phase 1 Actuators:
1. Dynamic Code Execution (Infinite Automation)
2. Cursor Gliding & Mouse Control
3. Ghost Typing
4. Skill Crystallization Registry
5. Active Word Document Hook
"""

import os
import sys
sys.path.insert(0, os.path.abspath("."))
import json
import pytest
from spark_voice_assistant import (
    tool_get_cursor_position,
    tool_mouse_move,
    tool_ghost_type,
    tool_execute_dynamic_automation,
    tool_save_crystallized_skill,
    tool_read_active_word_document,
    TOOL_DISPATCHER,
    TOOL_SCHEMAS
)

def test_cursor_position_query():
    pos_str = tool_get_cursor_position()
    assert "Cursor Position:" in pos_str
    assert "Primary Screen Resolution:" in pos_str

def test_smooth_mouse_move():
    res = tool_mouse_move(500, 500, duration=0.1)
    assert "navigated to (500, 500)" in res or "relocated to (500, 500)" in res

def test_ghost_typing():
    res = tool_ghost_type("test", interval=0.01)
    assert "characters dispatched" in res or "Typed via SendKeys" in res

def test_execute_dynamic_automation():
    # Dynamic self-contained Python script
    sample_code = """
import os
print("SPARK_DYNAMIC_SUCCESS_TEST")
"""
    output = tool_execute_dynamic_automation(sample_code)
    assert "SPARK_DYNAMIC_SUCCESS_TEST" in output
    # Ensure temporary execution file is cleaned up
    assert not os.path.exists("spark_dynamic_execution.py")

def test_skill_crystallization():
    sample_func = """def add_numbers(a, b):
    return a + b
"""
    res = tool_save_crystallized_skill("test_math_skill", sample_func, "Adds two numbers together")
    assert "successfully crystallized" in res
    
    # Verify file was created in skills/
    skill_path = os.path.join("skills", "test_math_skill.py")
    assert os.path.exists(skill_path)
    
    # Verify manifest
    manifest_path = os.path.join("skills", "skills_manifest.json")
    assert os.path.exists(manifest_path)
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert "test_math_skill" in manifest
    assert manifest["test_math_skill"]["description"] == "Adds two numbers together"
    
    # Clean up test artifact
    if os.path.exists(skill_path):
        os.remove(skill_path)

def test_read_active_word_document_graceful_notice():
    # If Word is not open, it must return a clean notice without crashing
    res = tool_read_active_word_document()
    assert isinstance(res, str)
    assert len(res) > 5

def test_dispatcher_and_schemas_integrity():
    assert "execute_dynamic_automation" in TOOL_DISPATCHER
    assert "mouse_move" in TOOL_DISPATCHER
    assert "mouse_click" in TOOL_DISPATCHER
    assert "ghost_type" in TOOL_DISPATCHER
    assert "read_active_word_document" in TOOL_DISPATCHER
    assert "save_crystallized_skill" in TOOL_DISPATCHER
    
    schema_names = [s["function"]["name"] for s in TOOL_SCHEMAS]
    assert "execute_dynamic_automation" in schema_names
    assert "mouse_move" in schema_names
    assert "ghost_type" in schema_names
    assert "read_active_word_document" in schema_names
    assert "save_crystallized_skill" in schema_names

if __name__ == "__main__":
    tests = [
        test_cursor_position_query,
        test_smooth_mouse_move,
        test_ghost_typing,
        test_execute_dynamic_automation,
        test_skill_crystallization,
        test_read_active_word_document_graceful_notice,
        test_dispatcher_and_schemas_integrity
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"PASS: {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"FAIL: {t.__name__} -> {e}")
    print(f"\nTOTAL: {passed}/{len(tests)} TESTS PASSED.")
