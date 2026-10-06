import pytest
from heart.level4_metacognition import MetacognitiveEngine, metacognitive_reflect
from llm.client import CircuitBreaker

def test_metacognitive_engine_amnesia_interception():
    # Test that forbidden amnesiac tropes are caught and self-corrected
    bot_draft = "As an AI language model, I do not have a memory of our previous chats."
    corrected = metacognitive_reflect(bot_draft, "What was my favorite framework?")
    assert "as an ai language model" not in corrected.lower()
    assert "subconscious" in corrected.lower()

def test_metacognitive_engine_structural_enforcement():
    dense_text = (
        "Here is the breakdown of the system. First we have the perception layer that takes images and text. "
        "Second we have the integration layer that performs memory storage and reasoning. "
        "Third we have the execution layer that sends the response to the user and stores it."
    )
    corrected = metacognitive_reflect(dense_text, "Explain the architecture")
    assert "### Overview" in corrected or "### Core Analysis" in corrected or "###" in corrected

def test_circuit_breaker_state_machine():
    cb = CircuitBreaker("TestBreaker", failure_threshold=2, recovery_time_seconds=1.0)
    assert cb.state == "CLOSED"
    assert cb.can_attempt() is True
    
    # 1st failure
    cb.record_failure()
    assert cb.state == "CLOSED"
    
    # 2nd failure triggers trip to OPEN
    cb.record_failure()
    assert cb.state == "OPEN"
    assert cb.can_attempt() is False
    
    # After recovery period
    import time
    time.sleep(1.1)
    assert cb.can_attempt() is True
    assert cb.state == "HALF_OPEN"
    
    # Success resets to CLOSED
    cb.record_success()
    assert cb.state == "CLOSED"
