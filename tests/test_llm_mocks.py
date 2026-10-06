import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from llm.client import call_llm, LLMCallError, LLMTransientError

@pytest.mark.anyio
async def test_llm_retry_logic():
    """Test Tenacity exponental backoff (Phase 3.2)."""
    # Mock config to have a fake API key
    mock_config = MagicMock()
    mock_config.groq_api_key = "fake_test_key"
    mock_config.groq_base_url = "https://api.groq.com/openai/v1"
    
    with patch("llm.client.get_config", return_value=mock_config), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        
        # Simulate transient error then success
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": "Success"}}]}
        mock_response.raise_for_status = MagicMock()
        
        mock_post.side_effect = [
            LLMTransientError("Rate limit"),
            LLMTransientError("Server error"),
            mock_response
        ]
        
        # This should trigger retries via tenacity on _do_post
        result = await call_llm("groq_api_key", "test-model", [{"role": "user", "content": "hi"}])
        assert result == "Success"
        assert mock_post.call_count == 3

@pytest.mark.anyio
async def test_purifier_json_fallback():
    """Test Phase 5.1/5.2: Purifier stability when LLM returns invalid JSON."""
    from heart.level3_purifier import purify
    
    with patch("heart.level3_purifier.call_heart_l3", new_callable=AsyncMock) as mock_llm:
        # Return junk string instead of JSON
        mock_llm.return_value = "This is not JSON..."
        
        # Purify should catch error and use fallback dictionary
        result = await purify("Test input", "Test response")
        assert result.topic_id == "general"
        assert "Interaction:" in result.summary

@pytest.mark.anyio
async def test_intent_splitting_logic():
    """Test Phase 5.2: Pipeline branching for multi-intent inputs."""
    from heart.pipeline import run_pipeline
    from cells.cell_model import BloodCell, CellStatus, CellType
    from datetime import datetime
    
    # Create test cell
    cell = BloodCell(
        cell_id="test_split_1",
        user_id="user_1",
        chat_id="chat_1",
        message_id="msg_1",
        session_id="s1",
        status=CellStatus.pending_purification,
        cell_type=CellType.raw,
        user_raw_content="Split intent A and intent B",
        user_content="Split intent A and intent B",
        created_at=datetime.utcnow()
    )
    
    # Mock Valve to return 2 splits
    with patch("heart.pipeline.level1_sieve.process_l1") as mock_sieve, \
         patch("heart.pipeline.level2_valve.valve", new_callable=AsyncMock) as mock_valve, \
         patch("heart.pipeline.level3_purifier.purify", new_callable=AsyncMock) as mock_purify:
        
        mock_sieve.return_value = {"passed": True, "cleaned": "Split intent A and intent B"}
        
        # valve_res needs to have 'splits' on first call only, then empty splits on child calls
        class MockValveResWithSplits:
            intent_type = "fact"
            is_ambiguous = False
            splits = ["Split intent A", "intent B"]
            
        class MockValveResChild:
            intent_type = "fact"
            is_ambiguous = False
            splits = []
            
        mock_valve.side_effect = [MockValveResWithSplits(), MockValveResChild(), MockValveResChild()]
        
        # Purify result
        from heart.level3_purifier import PurificationResult
        mock_purify.return_value = PurificationResult(
            user_content="intent A", ai_response_summary=None, ai_response_full=None,
            ai_response_type="none", importance_score=5, keywords=[], topic_id="test",
            summary="test", expires_at=None, link_id=None
        )
        
        # RUN PIPELINE
        results = await run_pipeline(cell)
        
        # Verify 2 cells returned (Splits)
        assert len(results) == 2
        assert results[0].cell_id == "test_split_1_0"
        assert results[1].cell_id == "test_split_1_1"
        assert results[0].is_chain is True
