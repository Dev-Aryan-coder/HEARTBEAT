import json
import logging
from collections import OrderedDict
from cells.cell_model import BloodCell
from storage.redis_client import get_redis_client

# Configure logging
logger = logging.getLogger("HEARTBEAT_ARTERY")

# In-memory buffer fallback when Redis is offline in local dev mode
_memory_artery = OrderedDict()

def push_cell(cell: BloodCell) -> bool:
    """Stores a cell in the heartbeat:artery Hash or in-memory fallback."""
    try:
        r = get_redis_client()
        r.hset("heartbeat:artery", cell.cell_id, cell.model_dump_json())
        return True
    except Exception as e:
        logger.debug(f"Redis offline, using high-speed in-memory Artery buffer: {str(e)}")
        _memory_artery[cell.cell_id] = cell.model_dump_json()
        return True

def pop_cell(cell_id: str) -> BloodCell:
    """Retrieves and deletes a cell from the artery."""
    try:
        r = get_redis_client()
        data = r.hget("heartbeat:artery", cell_id)
        if data:
            r.hdel("heartbeat:artery", cell_id)
            return BloodCell.model_validate_json(data)
    except Exception as e:
        logger.debug(f"Redis offline, popping from in-memory Artery: {str(e)}")
    
    if cell_id in _memory_artery:
        data = _memory_artery.pop(cell_id)
        return BloodCell.model_validate_json(data)
    return None

def list_all_cells() -> list:
    """Utility to list all cells currently in the artery."""
    try:
        r = get_redis_client()
        return [BloodCell.model_validate_json(v) for v in r.hvals("heartbeat:artery")]
    except Exception as e:
        logger.debug(f"Listing from in-memory Artery buffer: {str(e)}")
        return [BloodCell.model_validate_json(v) for v in _memory_artery.values()]

