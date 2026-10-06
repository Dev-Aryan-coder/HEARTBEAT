import logging
import asyncio
from datetime import datetime
from typing import List, Optional
from cells.cell_model import BloodCell, CellStatus, CellType, MemoryTier
from heart import level1_sieve, level2_valve, level3_purifier
from storage.database import get_cells_by_user, update_cell_status, save_link_vault_entry, supersede_cell
from api.websocket import monitor

# Configure logging
logger = logging.getLogger("HEARTBEAT_PIPELINE")

async def run_pipeline(raw_cell: BloodCell, context_messages: List[str] = [], previous_topic_embedding: Optional[List[float]] = None, ai_response: Optional[str] = None) -> List[BloodCell]:
    """
    Main orchestrator function for the Heart pipeline.
    ISSUE 10.1 & 6.3 FIX: Removed NameError flow control and added logging.
    """
    try:
        cleaned_text = raw_cell.user_raw_content
        valve_res = None # Explicitly initialize to avoid NameError

        # STEP 1-3: Filtering and Ambiguity (Only if no AI response yet)
        if not ai_response:
            logger.info(f"PIPELINE START [Cell: {raw_cell.cell_id}]")
            
            # STEP 1: Sieve
            sieve_res = level1_sieve.process_l1(raw_cell.user_raw_content)
            if not sieve_res["passed"]:
                logger.warning(f"Sieve Dismissal [Cell: {raw_cell.cell_id}]: {sieve_res['removed']}")
                raw_cell.status = CellStatus.expired
                return [raw_cell]
            
            cleaned_text = sieve_res["cleaned"]
            
            # STEP 2: Valve
            valve_res = await level2_valve.valve(cleaned_text, context_messages, previous_topic_embedding)
            
            if valve_res.intent_type in ["noise", "small_talk"]:
                logger.info(f"Valve Dismissal [Cell: {raw_cell.cell_id}]: Intent={valve_res.intent_type}")
                raw_cell.status = CellStatus.expired
                return [raw_cell]
            
            if valve_res.is_ambiguous:
                logger.info(f"Ambiguity Detected [Cell: {raw_cell.cell_id}]: {valve_res.ambiguous_word}")
                raw_cell.status = CellStatus.pending_clarification
                raw_cell.is_ambiguous = True
                raw_cell.clarification_question = valve_res.clarification_question
                return [raw_cell]
        
        # STEP 4: Intent Split (Only during initial processing and if valve succeeded)
        if not ai_response and valve_res and hasattr(valve_res, 'splits'):
            if len(valve_res.splits) > 1:
                logger.info(f"Intent Splitting [Cell: {raw_cell.cell_id}]: Found {len(valve_res.splits)} intents")
                child_cells = []
                for i, split in enumerate(valve_res.splits):
                    child = raw_cell.model_copy(update={
                        "cell_id": f"{raw_cell.cell_id}_{i}", # Ensure unique IDs for splits
                        "user_raw_content": split,
                        "user_content": split,
                        "is_chain": True,
                        "chain_id": raw_cell.cell_id,
                        "part_number": i + 1,
                        "total_parts": len(valve_res.splits)
                    })
                    # Recursive call for children
                    processed_children = await run_pipeline(child, context_messages, previous_topic_embedding)
                    child_cells.extend(processed_children)
                return child_cells

        # STEP 5: Purify (This is the stage where memory is actually formed)
        logger.info(f"Purification Start [Cell: {raw_cell.cell_id}]")
        purify_res = await level3_purifier.purify(cleaned_text, ai_response)
        
        # Update cell fields from purification result
        raw_cell.user_content = purify_res.user_content
        raw_cell.ai_response_summary = purify_res.ai_response_summary
        raw_cell.ai_response_full = purify_res.ai_response_full
        raw_cell.link_id = purify_res.link_id
        raw_cell.importance_score = purify_res.importance_score
        raw_cell.keywords = purify_res.keywords
        raw_cell.topic_id = purify_res.topic_id
        raw_cell.summary = purify_res.summary
        raw_cell.expires_at = purify_res.expires_at
        
        # 🧬 3-TIER BIOLOGICAL MEMORY CLASSIFICATION
        if (raw_cell.importance_score or 5) >= 8:
            raw_cell.memory_tier = MemoryTier.core_genome  # Permanent identity (immune to decay)
        elif (raw_cell.importance_score or 5) <= 4:
            raw_cell.memory_tier = MemoryTier.bloodstream    # Fast working memory
        else:
            raw_cell.memory_tier = MemoryTier.episodic       # Standard project/context memory
        
        # 🔗 LINK CELL LOGIC
        if purify_res.link_id:
            logger.info(f"Link Detected [Cell: {raw_cell.cell_id}]: ID={purify_res.link_id}")
            save_link_vault_entry(purify_res.link_id, raw_cell.cell_id, "text", ai_response or "", 1, 1)
            raw_cell.link_id = purify_res.link_id

        # 🧪 PRESSURE LOGIC: Fact Supremacy (Living Truth Resolution)
        # Supersede older active cells that share same topic or core keywords
        try:
            active_cells = get_cells_by_user(raw_cell.user_id, status="active")
            for old_c in active_cells:
                # Same topic collision check (avoid self)
                if old_c.get("cell_id") != raw_cell.cell_id and old_c.get("topic_id") == raw_cell.topic_id:
                    logger.info(f"FACT SUPREMACY: Superseding old cell {old_c['cell_id']} with new truth {raw_cell.cell_id}")
                    supersede_cell(old_c["cell_id"], raw_cell.cell_id)
                    # Broadcast to dashboard
                    await monitor.broadcast_cell_event(raw_cell.user_id, {
                        "type": "FACT_SUPREMACY",
                        "summary": f"Overwriting outdated memory for topic '{raw_cell.topic_id}' with new truth.",
                        "old_cell_id": old_c["cell_id"],
                        "new_cell_id": raw_cell.cell_id
                    })
        except Exception as e:
            logger.error(f"Pressure logic error: {str(e)}")
        
        # STEP 6: Finalize
        raw_cell.status = CellStatus.active
        raw_cell.cell_type = CellType.purified
        raw_cell.purified_at = datetime.utcnow()
        
        logger.info(f"PIPELINE COMPLETE [Cell: {raw_cell.cell_id}] | Topic: {raw_cell.topic_id}")
        return [raw_cell]

    except Exception as e:
        logger.error(f"PIPELINE CRITICAL FAILURE: {str(e)}", exc_info=True)
        raw_cell.status = CellStatus.expired
        return [raw_cell]
