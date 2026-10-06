import json
import logging
from typing import List, Optional
from cells.cell_model import BloodCell
from storage.redis_client import get_redis_client

# Configure logging
logger = logging.getLogger("HEARTBEAT_VEIN")

def publish_purified(cell: BloodCell) -> bool:
    """ISSUE 12.1 FIX: Publishes a purified cell to the user's vein channel using Redis singleton."""
    try:
        r = get_redis_client()
        channel = f"heartbeat:vein:{cell.user_id}"
        payload = {
            "type": "CELL_PURIFIED",
            "cell_id": cell.cell_id,
            "summary": cell.summary,
            "topic_id": cell.topic_id,
            "importance_score": cell.importance_score
        }
        r.publish(channel, json.dumps(payload))
        return True
    except Exception as e:
        logger.error(f"Error publishing purified cell for {cell.user_id}: {str(e)}")
        return False

def subscribe_purified(user_id: str):
    """Returns a PubSub object for the user's vein channel."""
    try:
        r = get_redis_client()
        p = r.pubsub()
        p.subscribe(f"heartbeat:vein:{user_id}")
        return p
    except Exception as e:
        logger.error(f"Error subscribing to vein for {user_id}: {str(e)}")
        return None
