import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from storage.database import get_connection, _normalize_user_id
from api.websocket import monitor

# Configure logging
logger = logging.getLogger("HEARTBEAT_METABOLISM")

async def run_metabolic_cycle(user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Executes a biological metabolic cycle across cells:
    1. Core Genome cells: Immune to decay (permanent DNA).
    2. Episodic cells: Gradual half-life decay. Move to dormant when score <= 2.
    3. Bloodstream cells: Rapid cycle, shifts to episodic or decays if idle.
    4. Expired cells: Transitioned to expired/dormant.
    5. Computes live biological telemetry (Heart Rate, Pressure, Cell distribution).
    """
    logger.info("🧬 METABOLISM: Executing biological metabolic cycle...")
    conn = get_connection()
    cursor = conn.cursor()
    now_dt = datetime.now(timezone.utc)
    now_iso = now_dt.isoformat()

    user_clause = "WHERE user_id = ? COLLATE NOCASE" if user_id else ""
    params = (_normalize_user_id(user_id),) if user_id else ()

    # Fetch cells eligible for metabolic review
    query = f"""
        SELECT cell_id, user_id, status, memory_tier, importance_score, 
               created_at, last_activated_at, expires_at, topic_id
        FROM blood_cells
        {user_clause}
    """
    cursor.execute(query, params)
    rows = cursor.fetchall()

    decayed_count = 0
    dormant_shifted_count = 0
    expired_count = 0
    active_count = 0
    core_count = 0
    dormant_count = 0

    for row in rows:
        cell_id = row['cell_id']
        uid = row['user_id']
        status = row['status']
        tier = row['memory_tier'] or 'episodic'
        score = row['importance_score'] or 5
        expires_at = row['expires_at']
        last_activated = row['last_activated_at'] or row['created_at']

        # Tier breakdown counter
        if tier == 'core_genome':
            core_count += 1
            if status == 'active':
                active_count += 1
            continue  # CORE GENOME IS IMMUNE TO DECAY

        if status == 'dormant':
            dormant_count += 1
            continue

        if status == 'expired':
            continue

        # Check explicit TTL expiration
        if expires_at and expires_at < now_iso:
            cursor.execute("UPDATE blood_cells SET status = 'expired' WHERE cell_id = ?", (cell_id,))
            expired_count += 1
            continue

        # Check age/inactivity for decay
        days_inactive = 0
        if last_activated:
            try:
                # Strip Z if present
                clean_ts = last_activated.replace("Z", "+00:00")
                act_dt = datetime.fromisoformat(clean_ts)
                if act_dt.tzinfo is None:
                    act_dt = act_dt.replace(tzinfo=timezone.utc)
                days_inactive = (now_dt - act_dt).total_seconds() / 86400.0
            except Exception:
                days_inactive = 1.0

        should_decay = False
        decay_amount = 0

        if tier == 'bloodstream' and days_inactive >= 1.0:
            # Bloodstream cells idle for > 24 hours shift to episodic and decay
            decay_amount = 1
            should_decay = True
        elif tier == 'episodic' and days_inactive >= 3.0:
            # Episodic cells idle for > 3 days decay by 1
            decay_amount = 1
            should_decay = True

        if should_decay:
            new_score = max(1, score - decay_amount)
            new_status = 'dormant' if new_score <= 2 else 'active'
            
            cursor.execute("""
                UPDATE blood_cells 
                SET importance_score = ?, status = ?
                WHERE cell_id = ?
            """, (new_score, new_status, cell_id))
            
            decayed_count += 1
            if new_status == 'dormant':
                dormant_shifted_count += 1
                dormant_count += 1
            else:
                active_count += 1
        else:
            if status == 'active':
                active_count += 1

    # 🧬 HIPPOCAMPAL SLEEP CONSOLIDATION (DeepMind Experience Distillation)
    consolidated_count = 0
    try:
        user_filter = "AND user_id = ?" if user_id else ""
        consol_params = (_normalize_user_id(user_id),) if user_id else ()
        cursor.execute(f"""
            SELECT topic_id, user_id, COUNT(*) as cnt
            FROM blood_cells
            WHERE status = 'active' AND memory_tier = 'episodic' AND topic_id != '' AND topic_id IS NOT NULL {user_filter}
            GROUP BY topic_id, user_id
            HAVING cnt >= 3
        """, consol_params)
        clusters = cursor.fetchall()
        
        for cluster in clusters:
            topic = cluster['topic_id']
            uid = cluster['user_id']
            cursor.execute("""
                SELECT cell_id, summary, ai_response_full, importance_score
                FROM blood_cells
                WHERE user_id = ? AND topic_id = ? AND status = 'active' AND memory_tier = 'episodic'
                ORDER BY created_at ASC
            """, (uid, topic))
            c_cells = cursor.fetchall()
            summaries = [c['summary'] or c['ai_response_full'] or "" for c in c_cells if c['summary'] or c['ai_response_full']]
            if summaries:
                synthesized_text = f"Consolidated Knowledge on [{topic}]: " + " | ".join(summaries[:4])
                from uuid import uuid4
                new_cid = str(uuid4())
                cursor.execute("""
                    INSERT INTO blood_cells (
                        cell_id, user_id, user_raw_content, user_content,
                        ai_response_full, ai_response_summary,
                        cell_type, status, memory_tier, importance_score,
                        topic_id, summary, created_at, last_activated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    new_cid, uid, synthesized_text, synthesized_text,
                    synthesized_text, synthesized_text[:200],
                    "purified", "active", "core_genome", 9,
                    topic, synthesized_text[:250], now_iso, now_iso
                ))
                for c in c_cells:
                    cursor.execute("UPDATE blood_cells SET status = 'dormant', superseded_by = ? WHERE cell_id = ?", (new_cid, c['cell_id']))
                consolidated_count += 1
                core_count += 1
                dormant_count += len(c_cells)
                active_count = max(0, active_count - len(c_cells) + 1)
                logger.info(f"🧬 CONSOLIDATION: Synthesized {len(c_cells)} episodic cells for topic '{topic}' into Core Genome {new_cid}")
    except Exception as consol_err:
        logger.warning(f"Hippocampal consolidation skipped gracefully: {consol_err}")

    conn.commit()

    # Calculate dynamic biological vital signs
    heart_rate_bpm = 72 + min(28, active_count * 2)
    pressure_status = "120/80 (Optimal)" if active_count < 25 else "135/88 (Elevated Flow)"

    telemetry = {
        "timestamp": now_iso,
        "heart_rate_bpm": heart_rate_bpm,
        "blood_pressure": pressure_status,
        "circulating_active": active_count,
        "core_genome_dna": core_count,
        "dormant_in_bones": dormant_count,
        "decayed_this_cycle": decayed_count,
        "hibernated_this_cycle": dormant_shifted_count,
        "expired_this_cycle": expired_count,
        "consolidated_this_cycle": consolidated_count,
        "status": "healthy_rhythm"
    }

    logger.info(f"🧬 METABOLISM COMPLETE: {telemetry}")

    # Broadcast living telemetry event via WebSocket
    target_users = [user_id] if user_id else ["MASTER_USER"]
    for t_uid in target_users:
        try:
            await monitor.broadcast_cell_event(t_uid, {
                "type": "METABOLIC_PULSE",
                "summary": f"Biological pulse completed. {active_count} cells flowing, {core_count} core DNA.",
                "telemetry": telemetry
            })
        except Exception as b_err:
            logger.debug(f"Telemetry broadcast notice skipped for {t_uid}: {b_err}")

    return telemetry

async def automated_decay_job():
    """
    Background 24/7 Biological Metabolism Daemon.
    Cycles periodically to maintain homeostasis across memory cells.
    """
    logger.info("🧬 METABOLISM: 24/7 Living Organism Daemon Running.")
    INTERVAL = 3600  # Default 1 hour in production

    while True:
        try:
            await run_metabolic_cycle()
        except Exception as e:
            logger.error(f"🧬 METABOLISM ERROR: {str(e)}", exc_info=True)

        await asyncio.sleep(INTERVAL)

def start_metabolism():
    """
    Starts the metabolism daemon safely within the running event loop.
    """
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(automated_decay_job())
        logger.info("🧬 Metabolism daemon attached to event loop.")
    except RuntimeError:
        logger.error("Failed to start metabolism: No running event loop detected.")
