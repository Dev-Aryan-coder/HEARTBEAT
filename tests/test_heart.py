import pytest
from unittest.mock import MagicMock, patch
from heart.level1_sieve import sieve
from heart.ambiguity_detector import detect_ambiguity
from cells.cell_model import CellFactory

def test_l1_sieve_noise():
    """Tests if short, noisy text is filtered out."""
    # sieve returns a dict with 'passed' False for noise
    res = sieve("hi")
    assert res["passed"] is False
    
    res2 = sieve("testing the heartbeat sieve logic with nouns and verbs")
    assert res2["passed"] is True
    assert "testing" in res2["cleaned"]

def test_ambiguity_no_llm():
    """Confirms the ambiguity detector can return fallback values."""
    with patch("heart.ambiguity_detector.call_llm") as mocked_llm:
        mocked_llm.return_value = "{\"is_ambiguous\": false}"
        cell = CellFactory.from_text("u1", "c1", "m1", "s1", "Python is great")
        is_amb, question = detect_ambiguity(cell)
        assert not is_amb
        assert question == ""

def test_full_heart_model_compatibility():
    """Tests if our Pydantic v2 models interact correctly with the Heart logic."""
    cell = CellFactory.from_text("u1", "c1", "m1", "s1", "Detailed complex query for purification")
    assert cell.user_word_count > 0
    assert cell.status == "pending_purification"
