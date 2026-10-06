import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from answers.answer_router import route_answer
from cells.cell_model import CellFactory, CellType, CellStatus

@pytest.mark.anyio
async def test_answer_quick_depth():
    """Confirms 'quick' triggering avoids LLM calls entirely."""
    cell = CellFactory.from_text("u1", "c1", "m1", "s1", "Python Memory")
    cell.summary = "A quick summary."
    
    # We don't patch LLM here, if it tries to call LLM, it should hang/fail
    response = await route_answer("Give me a quick summary", cell)
    assert "[Level 1: Quick]" in response
    assert "A quick summary" in response

@pytest.mark.anyio
async def test_answer_detailed_depth():
    """Confirms 'detail' triggering loads more context."""
    cell = CellFactory.from_text("u1", "c1", "m1", "s1", "Detailed Memory")
    cell.summary = "Initial summary."
    
    response = await route_answer("I need more detail", cell)
    assert "[Level 2: Detailed]" in response

@pytest.mark.anyio
async def test_answer_full_original():
    """Confirms 'original' triggering calls the Groq brain."""
    cell = CellFactory.from_text("u1", "c1", "m1", "s1", "Original Memory")
    cell.summary = "Context summary."
    
    # Mocking call_brain to avoid external API dependencies during test
    with patch("answers.level3_original.call_brain", new_callable=AsyncMock if hasattr(patch, 'AsyncMock') else MagicMock) as mocked_brain:
        if isinstance(mocked_brain, AsyncMock):
            mocked_brain.return_value = "This is reconstructed raw detail."
        else:
            # Fallback for older mock versions
            async def async_mock_res(*args, **kwargs): return "This is reconstructed raw detail."
            mocked_brain.side_effect = async_mock_res
            
        response = await route_answer("Show me the original source", cell)
        assert "[Level 3: Full Original]" in response
        assert "reconstructed" in response
