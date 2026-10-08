"""
Unit & Integration Tests for SPARK Phase 2 Elite Pillars:
1. Semantic Window Anchoring
2. Undo & Rollback Checkpoint System
3. Autonomous Daily Morning Briefing
4. Visual Grounding via Set-of-Marks (SoM)
5. Multi-Model Cognitive Router
"""

import os
import sys
import time
sys.path.insert(0, os.path.abspath("."))
import json
import pytest

from spark_voice_assistant import (
    tool_create_checkpoint,
    tool_undo_last_action,
    tool_generate_morning_briefing,
    tool_take_marked_screenshot,
    route_task_to_optimal_model,
    tool_write_workspace_file,
    TOOL_DISPATCHER,
    TOOL_SCHEMAS
)

def test_checkpoint_and_undo():
    test_file = os.path.abspath("test_phase2_checkpoint_target.txt")
    initial_content = "ORIGINAL_MASTER_ARYAN_DATA_V1"
    modified_content = "MODIFIED_DATA_BY_AUTOMATION_V2"
    
    # 1. Write initial file
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(initial_content)
        
    # 2. Create checkpoint
    cp_res = tool_create_checkpoint(test_file)
    assert "Safety checkpoint created" in cp_res
    
    # 3. Overwrite file
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(modified_content)
    with open(test_file, "r", encoding="utf-8") as f:
        assert f.read() == modified_content
        
    # 4. Undo last action
    undo_res = tool_undo_last_action()
    assert "Action successfully undone!" in undo_res
    
    # 5. Verify restored content matches original
    with open(test_file, "r", encoding="utf-8") as f:
        restored = f.read()
    assert restored == initial_content
    
    # Cleanup
    if os.path.exists(test_file):
        os.remove(test_file)

def test_automatic_checkpoint_on_workspace_write():
    test_file = os.path.abspath("test_auto_cp_file.txt")
    v1_content = "VERSION_1_AUTOMATIC_CHECKPOINT"
    v2_content = "VERSION_2_OVERWRITTEN_CONTENT"
    
    # Initial write
    tool_write_workspace_file(test_file, v1_content)
    
    # Second write triggers automatic checkpoint
    tool_write_workspace_file(test_file, v2_content)
    with open(test_file, "r", encoding="utf-8") as f:
        assert f.read() == v2_content
        
    # Call undo
    undo_res = tool_undo_last_action()
    assert "Action successfully undone!" in undo_res
    with open(test_file, "r", encoding="utf-8") as f:
        assert f.read() == v1_content
        
    # Cleanup
    if os.path.exists(test_file):
        os.remove(test_file)

def test_morning_briefing_generation():
    briefing = tool_generate_morning_briefing()
    assert isinstance(briefing, str)
    assert "Master Aryan" in briefing
    assert "System hardware status:" in briefing
    assert "learned skills library" in briefing

def test_marked_screenshot_som():
    out_img = "test_spark_som_sample.png"
    if os.path.exists(out_img):
        os.remove(out_img)
        
    res = tool_take_marked_screenshot(filename=out_img, grid_step=300)
    assert "Set-of-Marks visual screenshot saved" in res
    assert os.path.exists(out_img)
    assert os.path.getsize(out_img) > 1000  # Valid non-empty PNG
    
    # Cleanup
    if os.path.exists(out_img):
        os.remove(out_img)

def test_cognitive_model_routing():
    # Vision queries
    assert route_task_to_optimal_model("Look at screen and click the submit button") == "qwen2.5vl:3b"
    assert route_task_to_optimal_model("Find button on screen with marked screen grid") == "qwen2.5vl:3b"
    
    # Complex reasoning / debugging queries
    assert route_task_to_optimal_model("Debug this crash traceback and complex logic") == "deepseek-r1:7b"
    assert route_task_to_optimal_model("Diagnose error why script failed") == "deepseek-r1:7b"
    
    # Massive document / Cloud queries
    assert route_task_to_optimal_model("Read this 100 page massive document and summarize it") == "opencode/nemotron-3.5-lightning-free"
    assert route_task_to_optimal_model("Analyze this huge pdf book") == "opencode/nemotron-3.5-lightning-free"
    
    # Fast reflex queries
    assert route_task_to_optimal_model("Set volume to 50%") == "qwen2.5:3b"
    assert route_task_to_optimal_model("What is the battery level?") == "qwen2.5:3b"

def test_phase2_tool_registry():
    assert "create_checkpoint" in TOOL_DISPATCHER
    assert "undo_last_action" in TOOL_DISPATCHER
    assert "generate_morning_briefing" in TOOL_DISPATCHER
    assert "take_marked_screenshot" in TOOL_DISPATCHER
    
    schema_names = [s["function"]["name"] for s in TOOL_SCHEMAS]
    assert "create_checkpoint" in schema_names
    assert "undo_last_action" in schema_names
    assert "generate_morning_briefing" in schema_names
    assert "take_marked_screenshot" in schema_names

if __name__ == "__main__":
    tests = [
        test_checkpoint_and_undo,
        test_automatic_checkpoint_on_workspace_write,
        test_morning_briefing_generation,
        test_marked_screenshot_som,
        test_cognitive_model_routing,
        test_phase2_tool_registry
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"PASS: {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"FAIL: {t.__name__} -> {e}")
    print(f"\nTOTAL: {passed}/{len(tests)} PHASE 2 TESTS PASSED.")
