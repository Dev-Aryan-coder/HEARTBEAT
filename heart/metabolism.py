import asyncio
import logging
from datetime import datetime
from storage.database import get_connection
from api.websocket import monitor

# Configure logging
logger = logging.getLogger("HEARTBEAT_METABOLISM")

async def automated_decay_job():
    """
    ISSUE 5.2 & 11.1 FIX: Batch Decay Job.
    Purges expired cells periodically without N+1 query overhead.
    """
    logger.info("🧬 METABOLISM: Batch Decay Worker Initialized.")
    
    # Run every hour
    INTERVAL = 3600 

    while True:
        try:
            now = datetime.utcnow().isoformat()
            conn = get_connection()
            cursor = conn.cursor()

            # 1. Identify all cells that reached lifecycle end (All Users at once)
            cursor.execute("""
                SELECT cell_id, user_id FROM blood_cells 
                WHERE status = 'active' 
                AND expires_at IS NOT NULL 
                AND expires_at < ?
            """, (now,))
            expired_rows = cursor.fetchall()

            if expired_rows:
                # 2. Bulk Update to 'dormant'
                cursor.execute("""
                    UPDATE blood_cells 
                    SET status = 'dormant' 
                    WHERE status = 'active' 
                    AND expires_at IS NOT NULL 
                    AND expires_at < ?
                """, (now,))
                conn.commit()
                
                logger.info(f"🧬 METABOLISM: {len(expired_rows)} cells moved to dormant storage.")

                # 3. Broadcast events per user
                for row in expired_rows:
                    user_id = row['user_id']
                    cell_id = row['cell_id']
                    try:
                        await monitor.broadcast_cell_event(user_id, {
                            "type": "CELL_EXPIRED",
                            "summary": "Life cycle complete. Cell moved to dormant storage.",
                            "cell_id": cell_id
                        })
                    except Exception as b_err:
                        logger.debug(f"Broadcast failed for {user_id}: {b_err}")

        except Exception as e:
            logger.error(f"🧬 METABOLISM ERROR: {str(e)}")

        await asyncio.sleep(INTERVAL)

def start_metabolism():
    """
    ISSUE 5.6 FIX: Event Loop Guard.
    Starts the metabolism loop safely within the running event loop.
    """
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(automated_decay_job())
        logger.info("🧬 Metabolism task attached to event loop.")
    except RuntimeError:
        logger.error("Failed to start metabolism: No running event loop detected.")
