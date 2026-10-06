import pytest
from unittest.mock import MagicMock, patch
from heart.level1_sieve import process_l1 as sieve
from heart.ambiguity_detector import detect as detect_ambiguity
from cells.cell_model import CellFactory

def test_l1_sieve_noise():
    res = sieve("hi")
    assert res["passed"] is False

def test_ambiguity_no_llm():
    # Ambiguity detector now uses config and shared logic, not call_llm
    # We test it with a known ambiguous word
    res = detect_ambiguity("I am eating an apple", [])
    # 'eating' is a clue for fruit, so confidence 1.0 > threshold 0.6
    assert not res["is_ambiguous"]
    
    res_amb = detect_ambiguity("apple", [])
    assert res_amb["is_ambiguous"]
    assert "fruit" in res_amb["question"]
