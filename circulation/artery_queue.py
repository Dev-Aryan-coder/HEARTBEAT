import json
import logging
from cells.cell_model import BloodCell
from storage.redis_client import get_redis_client

# Configure logging
logger = logging.getLogger("HEARTBEAT_ARTERY")

def push_cell(cell: BloodCell) -> bool:
    """Stores a cell in the heartbeat:artery Hash."""
    try:
        r = get_redis_client()
        r.hset("heartbeat:artery", cell.cell_id, cell.model_dump_json())
        return True
    except Exception as e:
        logger.warning(f"Redis offline, skipping artery push (Local Dev Mode): {str(e)}")
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
        logger.error(f"Error popping from artery: {str(e)}")
    return None

def list_all_cells() -> list:
    """Utility to list all cells currently in the artery."""
    try:
        r = get_redis_client()
        return [BloodCell.model_validate_json(v) for v in r.hvals("heartbeat:artery")]
    except Exception as e:
        logger.error(f"Error listing artery: {str(e)}")
        return []
