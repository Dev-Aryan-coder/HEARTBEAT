"""
Unit & Integration Tests for SPARK Phase 3: The Multi-Step Brain:
1. Task Execution DAG & Topological Wave Sorting
2. Multi-Step DAG Plan Execution (tool_execute_dag_plan)
3. Autonomous Code Self-Healing & Diagnosis (tool_diagnose_and_heal_script)
4. Dispatcher & Schema Integrity for Phase 3
"""

import os
import sys
import json
import pytest
sys.path.insert(0, os.path.abspath("."))

from cells.memory_structures import TaskExecutionDAG
from spark_voice_assistant import (
    tool_execute_dag_plan,
    tool_diagnose_and_heal_script,
    tool_execute_dynamic_automation,
    heal_code_with_llm,
    TOOL_DISPATCHER,
    TOOL_SCHEMAS
)

def test_dag_topological_wave_sorting():
    dag = TaskExecutionDAG()
    # Diamond graph structure:
    #      task_root
    #      /       \
    # task_left   task_right
    #      \       /
    #      task_sink
    dag.add_task("task_root", "get_current_time", {})
    dag.add_task("task_left", "get_system_vitals", {}, depends_on=["task_root"])
    dag.add_task("task_right", "get_cursor_position", {}, depends_on=["task_root"])
    dag.add_task("task_sink", "get_current_time", {}, depends_on=["task_left", "task_right"])

    batches = dag.topological_sort()
    assert len(batches) == 3
    assert batches[0] == ["task_root"]
    assert set(batches[1]) == {"task_left", "task_right"}
    assert batches[2] == ["task_sink"]

    exec_result = dag.execute_plan(TOOL_DISPATCHER, halt_on_failure=True)
    assert exec_result["success"] is True
    assert exec_result["batches_executed"] == 3
    assert "task_root" in exec_result["results"]
    assert "task_sink" in exec_result["results"]

def test_execute_dag_plan_tool():
    test_filepath = os.path.abspath("test_phase3_dag_output.txt")
    if os.path.exists(test_filepath):
        os.remove(test_filepath)

    plan = [
        {"id": "step_1", "tool": "get_current_time", "args": {}},
        {"id": "step_2", "tool": "get_system_vitals", "args": {}},
        {
            "id": "step_3",
            "tool": "write_workspace_file",
            "args": {
                "filepath": test_filepath,
                "content": "Phase 3 Multi-Step DAG Execution Verified."
            },
            "depends_on": ["step_1", "step_2"]
        }
    ]

    res = tool_execute_dag_plan(json.dumps(plan))
    assert "DAG Multi-Step Plan Executed" in res
    assert "Overall Status: SUCCESS" in res
    assert os.path.exists(test_filepath)
    with open(test_filepath, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Phase 3 Multi-Step DAG Execution Verified." in content

    # Cleanup
    if os.path.exists(test_filepath):
        os.remove(test_filepath)

def test_autonomous_diagnosis_and_healing():
    broken_script = """
import sys
# Bug: intentional typo in function call
sys.stdout.writ("Missing letter e in write")
"""
    error_traceback = "AttributeError: 'TextIOWrapper' object has no attribute 'writ'. Did you mean: 'write'?"

    # Diagnose & heal tool
    healed = tool_diagnose_and_heal_script(broken_script, error_traceback)
    assert isinstance(healed, str)
    assert len(healed) > 10

def test_phase3_dispatcher_and_schemas():
    assert "diagnose_and_heal_script" in TOOL_DISPATCHER
    assert "execute_dag_plan" in TOOL_DISPATCHER

    schema_names = [s["function"]["name"] for s in TOOL_SCHEMAS]
    assert "diagnose_and_heal_script" in schema_names
    assert "execute_dag_plan" in schema_names

if __name__ == "__main__":
    tests = [
        test_dag_topological_wave_sorting,
        test_execute_dag_plan_tool,
        test_autonomous_diagnosis_and_healing,
        test_phase3_dispatcher_and_schemas
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"PASS: {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"FAIL: {t.__name__} -> {e}")
    print(f"\nTOTAL: {passed}/{len(tests)} PHASE 3 TESTS PASSED.")
