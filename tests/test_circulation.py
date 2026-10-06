import pytest
from unittest.mock import patch, MagicMock
from circulation.artery_queue import push_cell, pop_cell
from circulation.vein_pubsub import publish_purified
from cells.cell_model import CellFactory, BloodCell

@patch("circulation.artery_queue.get_redis_client")
def test_artery_push_pull(mock_redis_getter):
    """Tests if cells can be put and pulled from the artery."""
    mock_r = MagicMock()
    mock_redis_getter.return_value = mock_r
    
    cell = CellFactory.from_text("u1", "c1", "m1", "s1", "Python Memory")
    
    # Mock push
    push_success = push_cell(cell)
    assert push_success
    mock_r.hset.assert_called()
    
    # Mock pull
    mock_r.hget.return_value = cell.model_dump_json()
    returned_cell = pop_cell(cell.cell_id)
    assert returned_cell.cell_id == cell.cell_id
    mock_r.hdel.assert_called()

@patch("circulation.vein_pubsub.get_redis_client")
def test_vein_broadcast(mock_redis_getter):
    """Tests if purified cells are published for the dashboard."""
    mock_r = MagicMock()
    mock_redis_getter.return_value = mock_r
    
    cell = CellFactory.from_text("u1", "c1", "m1", "s1", "Purified Thought")
    publish_purified(cell)
    mock_r.publish.assert_called()
    assert f"heartbeat:vein:{cell.user_id}" in mock_r.publish.call_args[0]
