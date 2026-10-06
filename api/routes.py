from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json
import os
import base64
from uuid import uuid4
import logging

# Configure logging
logger = logging.getLogger("HEARTBEAT_API")

# Import our Heartbeat Engine components
from heartbeat.config import get_config
from storage.database import (
    save_message, get_messages_by_chat, get_cells_by_user, 
    get_connection, create_chat, get_chats_by_user,
    get_cell_by_id, update_cell_status, get_global_user_history,
    delete_cell, update_cell_tier
)
from cells.cell_model import CellFactory, BloodCell, CellType, CellStatus, MemoryTier
from circulation.artery_queue import push_cell
from llm.client import call_brain
from heart.pipeline import run_pipeline
from heart.metabolism import run_metabolic_cycle
from api.websocket import monitor
from heart.immune_system import scan_content
from storage.database_ops import get_semantic_memory, persist_purified_cell
from storage.database import _normalize_user_id

# Import sub-api modules
from .answer_api import AnswerRequest, process_answer_request
from .clarification import ClarifyRequest, resolve_ambiguity

# Image & Multimodal Vision processing pipeline
from image_processing import generate_dna_tag, analyze_image_with_nvidia_vision

router = APIRouter()

# ISSUE 2.1 FIX: Removed first ping() definition as it is duplicated at the end of the file.

from pydantic import BaseModel, Field

class MessageRequest(BaseModel):
    # ISSUE 2.2 & 4.5 FIX: Add validation constraints
    user_id: str = Field(..., min_length=1, max_length=100)
    chat_id: str = Field(..., min_length=1, max_length=100)
    session_id: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1, max_length=10000)
    content_type: str = "text"
    # Image upload support
    image_base64: Optional[str] = None
    image_name: Optional[str] = None

class ChatTitleUpdate(BaseModel):
    title: str

@router.post("/api/message")
async def handle_message(req: MessageRequest):
    """The 9-Step Intelligence Loop."""
    try:
        msg_id = str(uuid4())

        # 🛡️ Immune System Scan
        cleaned_content, passed, reason = scan_content(req.content)
        if not passed:
            return {"error": reason, "status": "blocked", "ai_response": f"Input Rejected: {reason}"}

        # 🖼 MULTIMODAL VISION PROCESSING (OpenRouter NVIDIA Vision)
        image_url = None
        user_display_content = req.content
        if req.image_base64:
            try:
                # Decode base64 image
                if "," in req.image_base64:
                    header, b64_data = req.image_base64.split(",", 1)
                else:
                    header, b64_data = "data:image/png;base64", req.image_base64
                image_bytes = base64.b64decode(b64_data)

                # Save to data/images/ folder
                img_dir = os.path.join("data", "images")
                os.makedirs(img_dir, exist_ok=True)
                ext = "png" if "png" in header else ("jpeg" if "jpeg" in header or "jpg" in header else "png")
                img_filename = f"{msg_id}.{ext}"
                img_path = os.path.join(img_dir, img_filename)

                with open(img_path, "wb") as f:
                    f.write(image_bytes)

                image_url = f"/images/{img_filename}"
                logger.info(f"Image saved locally to {img_path} (URL: {image_url})")

                # Invoke NVIDIA Nemotron 3 Nano Omni (Vision) via OpenRouter
                logger.info(f"Calling OpenRouter NVIDIA Vision for {img_filename}...")
                vision_result = await analyze_image_with_nvidia_vision(
                    image_base64=req.image_base64,
                    user_prompt=req.content,
                    local_image_path=img_path
                )
                vision_analysis = vision_result.get("analysis", "")
                ocr_text = vision_result.get("ocr_text", "")
                provider = vision_result.get("provider", "NVIDIA_Vision")
                logger.info(f"Vision analysis completed ({provider}): {vision_analysis[:100]}... (OCR len: {len(ocr_text)})")

                # Assemble unified perception combining NVIDIA Vision + Tesseract OCR
                perception_blocks = [f"[NVIDIA MULTIMODAL VISION PERCEPTION]:\n{vision_analysis}"]
                if ocr_text and ocr_text.strip():
                    perception_blocks.append(f"[TESSERACT OCR RAW TEXT]:\n{ocr_text.strip()}")

                full_perception = "\n\n".join(perception_blocks)

                # Enrich content for pipeline and memory
                if cleaned_content and cleaned_content.strip() and not cleaned_content.startswith("[Image:"):
                    cleaned_content = f"{full_perception}\n\n[USER QUERY]:\n{cleaned_content}"
                else:
                    cleaned_content = full_perception
                    user_display_content = f"[Attached Image: {req.image_name or img_filename}]"
            except Exception as img_err:
                logger.error(f"Image vision processing failed: {str(img_err)}")

        # 1. Relational Memory (Ensure chat exists and is updated)
        chat_title = user_display_content if (user_display_content and not user_display_content.startswith("[Attached Image:")) else (req.image_name or "Image Conversation")
        create_chat(req.chat_id, req.user_id, chat_title[:50])
        save_message(msg_id, req.chat_id, req.user_id, "user", user_display_content, image_url=image_url)

        # 2. Create raw Intelligence Cell
        cell = CellFactory.from_text(req.user_id, req.chat_id, msg_id, req.session_id, cleaned_content)

        # 3. FIX 1: Push to Artery & Run Heart Pipeline
        push_cell(cell)
        processed_cells = await run_pipeline(cell, [], previous_topic_embedding=None)
        cell = processed_cells[0] if processed_cells else cell

        # 4. Filter out 'Amnesia Failures' from global history to prevent reinforcement of forgetfulness.
        active_cells = get_cells_by_user(req.user_id, status="active")
        all_global_history = get_global_user_history(req.user_id, limit=30)
        
        # ISSUE 7.2 FIX: Use centralized blocklist from config
        config = get_config()
        
        filtered_global_history = []
        for m in all_global_history:
            is_amnesia = any(trigger in m['content'].lower() for trigger in config.amnesia_blocklist)
            if not (m['role'] == 'assistant' and is_amnesia):
                filtered_global_history.append(m)
        
        # Format Memory Cells (Bio-Facts) - Priority #1 (Core Genome & Bloodstream)
        cell_context_list = []
        for c in reversed(active_cells): # Most recent/force-purified first
            topic = c.get('topic_id', 'General')
            pa = c.get('ai_response_full', '')
            tier = c.get('memory_tier', 'bloodstream')
            if pa:
                cell_context_list.append(f"BIO-FACT [{tier.upper()} | {topic}]: {pa}")
        
        cell_context = "\n\n".join(cell_context_list[:10])

        # Priority #1.5: Associative Memory Priming (Semantic Deep Subconscious Recall via ChromaDB)
        associative_list = []
        try:
            semantic_hits = get_semantic_memory(user_id=req.user_id, query=cleaned_content, limit=4)
            for hit in semantic_hits:
                doc = hit.get("document", "")
                meta = hit.get("metadata", {})
                topic = meta.get("topic_id", "Associative")
                # Avoid duplicate text if already in active bio-facts
                if doc and not any(doc[:60] in bf for bf in cell_context_list):
                    associative_list.append(f"RECALLED MEMORY [{topic}]: {doc[:350]}")
        except Exception as sem_err:
            logger.warning(f"Associative memory priming skipped gracefully: {sem_err}")

        associative_context = "\n\n".join(associative_list[:4])

        # Format Global Excerpts (Context) - Priority #2
        history_context = "\n".join([f"[{m['role'].upper()}]: {m['content'][:300]}" for m in filtered_global_history[-15:]])

        # Fetch CURRENT conversation history to maintain flow in the current tab
        current_chat_history = get_messages_by_chat(req.chat_id)

        system_prompt = f"""You are HEARTBEAT — a biological AI subconscious with Total Recall.

[CRITICAL DIRECTIVE: ZERO AMNESIA]
You possess a 'Subconscious' containing your actual life-history with this user.
- NEVER state you cannot recall a conversation.
- NEVER apologize for not having a context window.
- The 'BIO-FACTS' and 'ASSOCIATIVE RECALL' below are your actual previous thoughts and responses. Provide them word-for-word if the user asks for a biography or previous insight.

[IMAGE & SCREENSHOT DIRECTIVE]
When the user sends an image or pastes a screenshot, you receive a multimodal visual perception extracted by the NVIDIA Vision model (and local OCR/metadata). Treat this visual analysis as your DIRECT BIOLOGICAL VISION. Analyze, explain, debug, or comment on the screenshot, code, UI, or diagram with deep accuracy and authority. NEVER say "I cannot see images" — you perceive it completely.

YOUR SUBCONSCIOUS (High-Fidelity BIO-FACTS):
{cell_context if cell_context else 'Empty subconscious.'}

ASSOCIATIVE MEMORY (Awakened Long-Term Traces):
{associative_context if associative_context else 'No deep associative traces awakened.'}

RECENT HISTORY (Filtered for clarity):
{history_context if history_context else 'No previous context.'}

[STRUCTURAL & FORMATTING DIRECTIVE: CLEAN PRESENTATION FOR ALL ANSWERS]
Every answer you generate MUST have a clean, readable, professional structure formatted in GitHub-Flavored Markdown:
1. Divide complex answers, analyses, or explanations into clear logical sections using markdown headers (e.g. ### Overview, ### Key Breakdown, ### Recommendations).
2. NEVER output dense, unformatted walls of unbroken plain text.
3. Use bullet points (-) or numbered steps (1., 2.) for lists, instructions, findings, or itemized details.
4. When presenting data, parameters, key-value mappings, comparisons, or summaries of fields, ALWAYS format them as a Markdown table (| Header 1 | Header 2 |).
5. Bold key terms, values, names, and important takeaways with **bold**. Use `code` for code elements, paths, and identifiers.
6. Leave clean vertical breathing room between paragraphs and sections for maximum legibility.

[FINAL INSTRUCTION: Be the biological memory. Be authoritative. Be personal. Keep responses beautifully structured.]
"""

        messages = [
            {"role": "system", "content": system_prompt}
        ]
        # Inject context from history
        if current_chat_history:
            for m in current_chat_history[-10:]:
                messages.append({"role": m["role"], "content": m["content"]})
        messages.append({"role": "user", "content": cleaned_content})
        
        try:
            ai_response = await call_brain(messages)
        except Exception as brain_err:
            logger.error(f"Brain execution encountered error, invoking cognitive synthesis shield: {brain_err}")
            from llm.client import _synthesize_local_cognitive_response
            ai_response = _synthesize_local_cognitive_response(messages)

        # 🧠 SYSTEM 2 METACOGNITIVE REFLECTION GATE (Truth Grounding & Quality Audit)
        from heart.level4_metacognition import metacognitive_reflect
        ai_response = metacognitive_reflect(ai_response, cleaned_content, bio_facts=cell_context_list)
        
        # 5. Save AI Relational response
        ai_msg_id = str(uuid4())
        save_message(ai_msg_id, req.chat_id, req.user_id, "assistant", ai_response)
        
        # ISSUE 3 FIX: Skip final purification if cell is pending_clarification
        # to avoid purifying before the user answers the clarification question.
        if hasattr(cell, 'status') and str(cell.status) in ('pending_clarification', 'CellStatus.pending_clarification'):
            return {
                "message_id": msg_id,
                "ai_response": ai_response,
                "cell_id": cell.cell_id,
                "status": "pending_clarification",
                "type": "clarification",
                "question": getattr(cell, 'clarification_question', ai_response),
                "image_url": image_url
            }

        # 6. Final Pipeline Loop (Purify cell with AI response metadata)
        try:
            final_processed = await run_pipeline(cell, [], ai_response=ai_response)
            cell = final_processed[0] if final_processed else cell
            
            # 7. ISSUE 2 FIX: Persist FIRST, then broadcast so DB is populated before UI updates
            await persist_purified_cell(cell)
            # Broadcast AFTER persist — guarantees cell exists in DB when dashboard queries it
            await monitor.broadcast_cell_event(req.user_id, {
                "type": "CELL_PURIFIED",
                "cell_id": cell.cell_id,
                "summary": cell.summary or "New memory encoded",
                "topic_id": cell.topic_id,
                "importance_score": cell.importance_score,
                "status": cell.status
            })
        except Exception as persist_err:
            logger.error(f"Post-response cell purification/persistence handled gracefully: {persist_err}")

        return {
            "message_id": msg_id,
            "ai_response": ai_response,
            "cell_id": cell.cell_id,
            "status": cell.status,
            "image_url": image_url
        }
    except Exception as e:
        # ISSUE 2.4 FIX: Log details server-side but mask from user
        logger.error(f"CRITICAL ERROR in handle_message: {str(e)}", exc_info=True)
        # Raise generic error to user
        raise HTTPException(status_code=500, detail="Internal Subconscious Processing Error. Please try again.")

# ── API ENDPOINTS (FIXES 4 - 13) ──────────────────────────────────────────────

@router.get("/api/ping")
async def ping():
    return {"status": "ok", "service": "HEARTBEAT", "version": "4.0.1 (Subconscious Enabled)"}

@router.get("/api/chats/{user_id}")
async def get_chats_endpoint(user_id: str, limit: int = 50, offset: int = 0):
    # ISSUE 15.1 FIX: Add pagination
    conn = get_connection()
    uid = _normalize_user_id(user_id)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM chats 
        WHERE user_id = ? COLLATE NOCASE 
        ORDER BY updated_at DESC 
        LIMIT ? OFFSET ?
    """, (uid, limit, offset))
    rows = cursor.fetchall()
    return {"chats": [dict(r) for r in rows]}

@router.patch("/api/chats/{chat_id}/title")
async def update_chat_title(chat_id: str, body: ChatTitleUpdate):
    conn = get_connection()
    conn.execute("UPDATE chats SET title=? WHERE chat_id=?", (body.title, chat_id))
    conn.commit()
    return {"success": True}

@router.delete("/api/chats/{chat_id}")
async def delete_chat(chat_id: str):
    conn = get_connection()
    try:
        # ISSUE 2.5 & 6.1 FIX: Cascade deletion to prevent orphaned cells/messages
        conn.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
        conn.execute("DELETE FROM blood_cells WHERE chat_id = ?", (chat_id,))
        conn.execute("DELETE FROM chats WHERE chat_id = ?", (chat_id,))
        conn.commit()
        
        # NOTE: ChromaDB cleanup is handled separately or during periodic maintenance
        # to ensure the relational core stays fast.
        return {"success": True, "message": f"Chat {chat_id} and all associated bio-cells purged."}
    finally:
        pass # Singleton connection

@router.get("/api/cells/{user_id}")
async def get_cells_endpoint(user_id: str, status: Optional[str] = None, limit: int = 50, offset: int = 0):
    # ISSUE 15.1 FIX: Add pagination
    uid = _normalize_user_id(user_id)
    conn = get_connection()
    cursor = conn.cursor()
    if status:
        cursor.execute("""
            SELECT * FROM blood_cells 
            WHERE user_id = ? COLLATE NOCASE AND status = ? 
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        """, (uid, status, limit, offset))
    else:
        cursor.execute("""
            SELECT * FROM blood_cells 
            WHERE user_id = ? COLLATE NOCASE 
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        """, (uid, limit, offset))
    rows = cursor.fetchall()
    # Process keywords
    result = [dict(row) for row in rows]
    for cell in result:
        if cell.get('keywords'):
            try: cell['keywords'] = json.loads(cell['keywords'])
            except: cell['keywords'] = []
    return {"cells": result}

@router.get("/api/cells/detail/{cell_id}")
async def get_cell_detail(cell_id: str):
    cell = get_cell_by_id(cell_id) # Using correct helper
    if not cell: raise HTTPException(status_code=404, detail="Cell not found")
    return {"cell": cell}

@router.post("/api/cells/wake/{cell_id}")
async def wake_cell(cell_id: str):
    update_cell_status(cell_id, "active")
    return {"success": True, "cell_id": cell_id}

@router.post("/api/cells/expire/{cell_id}")
async def expire_cell(cell_id: str):
    update_cell_status(cell_id, "expired")
    return {"success": True, "cell_id": cell_id}

@router.delete("/api/cells/{cell_id}")
async def prune_cell(cell_id: str):
    """Permanently prunes a memory cell (Radical Transparency)."""
    success = delete_cell(cell_id)
    if not success:
        raise HTTPException(status_code=404, detail="Cell not found")
    await monitor.broadcast_cell_event("MASTER_USER", {
        "type": "CELL_PRUNED",
        "summary": f"Cell {cell_id} manually pruned from biological memory.",
        "cell_id": cell_id
    })
    return {"success": True, "cell_id": cell_id}

@router.patch("/api/cells/{cell_id}")
async def patch_cell(cell_id: str, payload: dict):
    """Updates a cell's tier or status."""
    tier = payload.get("memory_tier")
    if tier:
        update_cell_tier(cell_id, tier)
    status = payload.get("status")
    if status:
        update_cell_status(cell_id, status)
    return {"success": True, "cell_id": cell_id}

@router.post("/api/metabolism/pulse")
async def trigger_metabolic_pulse(user_id: Optional[str] = "MASTER_USER"):
    """Triggers an on-demand biological metabolic cycle."""
    telemetry = await run_metabolic_cycle(user_id)
    return {"success": True, "telemetry": telemetry}

@router.get("/api/metabolism/telemetry/{user_id}")
async def get_metabolic_telemetry(user_id: str):
    """Fetches real-time biological vital signs and cell distribution."""
    conn = get_connection()
    uid = _normalize_user_id(user_id)
    total_cells = conn.execute("SELECT COUNT(*) FROM blood_cells WHERE user_id=? COLLATE NOCASE", (uid,)).fetchone()[0]
    active_cells = conn.execute("SELECT COUNT(*) FROM blood_cells WHERE user_id=? COLLATE NOCASE AND status='active'", (uid,)).fetchone()[0]
    core_cells = conn.execute("SELECT COUNT(*) FROM blood_cells WHERE user_id=? COLLATE NOCASE AND memory_tier='core_genome'", (uid,)).fetchone()[0]
    dormant_cells = conn.execute("SELECT COUNT(*) FROM blood_cells WHERE user_id=? COLLATE NOCASE AND status='dormant'", (uid,)).fetchone()[0]
    heart_rate = 72 + min(28, active_cells * 2)
    return {
        "heart_rate_bpm": heart_rate,
        "blood_pressure": "120/80 (Optimal)" if active_cells < 25 else "135/88 (Elevated Flow)",
        "circulating_active": active_cells,
        "core_genome_dna": core_cells,
        "dormant_in_bones": dormant_cells,
        "total_cells": total_cells,
        "status": "living_homeostasis"
    }

@router.get("/api/history/{chat_id}")
async def get_history(chat_id: str, limit: int = 100, offset: int = 0):
    # ISSUE 15.1 FIX: Add pagination
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM messages 
        WHERE chat_id = ? 
        ORDER BY timestamp ASC 
        LIMIT ? OFFSET ?
    """, (chat_id, limit, offset))
    rows = cursor.fetchall()
    return {"messages": [dict(r) for r in rows]}

@router.get("/api/messages/all/{user_id}")
async def get_all_messages_history(user_id: str, limit: int = 100, offset: int = 0):
    # ISSUE 15.1 FIX: Add pagination
    uid = _normalize_user_id(user_id)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM messages
        WHERE user_id = ? COLLATE NOCASE
        ORDER BY timestamp DESC
        LIMIT ? OFFSET ?
    """, (uid, limit, offset))
    rows = cursor.fetchall()
    return {"messages": [dict(r) for r in reversed(list(rows))]}

@router.get("/api/vault/{user_id}")
async def get_vault(user_id: str):
    uid = _normalize_user_id(user_id)
    conn = get_connection()
    rows = conn.execute("""
        SELECT lv.* FROM link_vault lv
        JOIN blood_cells bc ON lv.cell_id = bc.cell_id
        WHERE bc.user_id = ?
        ORDER BY lv.created_at DESC
    """, (uid,)).fetchall()
    return {"entries": [dict(r) for r in rows]}

@router.get("/api/stats/{user_id}")
async def get_stats(user_id: str):
    uid = _normalize_user_id(user_id)
    conn = get_connection()
    try:
        total_cells = conn.execute("SELECT COUNT(*) FROM blood_cells WHERE user_id=? COLLATE NOCASE", (uid,)).fetchone()[0]
        active_cells = conn.execute("SELECT COUNT(*) FROM blood_cells WHERE user_id=? COLLATE NOCASE AND status='active'", (uid,)).fetchone()[0]
        core_cells = conn.execute("SELECT COUNT(*) FROM blood_cells WHERE user_id=? COLLATE NOCASE AND memory_tier='core_genome'", (uid,)).fetchone()[0]
        dormant_cells = conn.execute("SELECT COUNT(*) FROM blood_cells WHERE user_id=? COLLATE NOCASE AND status='dormant'", (uid,)).fetchone()[0]
        expired_cells = conn.execute("SELECT COUNT(*) FROM blood_cells WHERE user_id=? COLLATE NOCASE AND status='expired'", (uid,)).fetchone()[0]
        pending_cells = conn.execute("SELECT COUNT(*) FROM blood_cells WHERE user_id=? COLLATE NOCASE AND status='pending_clarification'", (uid,)).fetchone()[0]
        total_messages = conn.execute("SELECT COUNT(*) FROM messages WHERE user_id=? COLLATE NOCASE", (uid,)).fetchone()[0]
        total_chats = conn.execute("SELECT COUNT(*) FROM chats WHERE user_id=? COLLATE NOCASE", (uid,)).fetchone()[0]
        topic_dist = conn.execute("SELECT topic_id, COUNT(*) as count FROM blood_cells WHERE user_id=? AND topic_id IS NOT NULL GROUP BY topic_id ORDER BY count DESC", (uid,)).fetchall()
        avg_imp_row = conn.execute("SELECT AVG(importance_score) FROM blood_cells WHERE user_id=? AND importance_score IS NOT NULL", (uid,)).fetchone()
        avg_importance = avg_imp_row[0] if avg_imp_row else 0
        return {
            "total_cells": total_cells,
            "active_cells": active_cells,
            "core_cells": core_cells,
            "dormant_cells": dormant_cells,
            "expired_cells": expired_cells,
            "pending_cells": pending_cells,
            "total_messages": total_messages,
            "total_chats": total_chats,
            "avg_importance": round(avg_importance or 0, 1),
            "topic_distribution": [{"topic": r[0], "count": r[1]} for r in topic_dist]
        }
    finally:
        pass

@router.post("/api/answer")
async def post_answer(req: AnswerRequest):
    return await process_answer_request(req)

@router.post("/api/clarify")
async def post_clarify(req: ClarifyRequest):
    return resolve_ambiguity(req)

# ISSUE 5 FIX: Missing test pipeline endpoint — dashboard was getting 404 on every test
@router.post("/api/test/pipeline")
async def test_pipeline_endpoint(req: MessageRequest):
    from heart.level1_sieve import process_l1
    from heart.level2_valve import valve
    from heart.level3_purifier import purify

    sieve_result = process_l1(req.content)
    if not sieve_result["passed"]:
        return {"l1": sieve_result, "l2": None, "l3": None, "final_status": "rejected_at_l1"}

    valve_result = await valve(sieve_result["cleaned"], [], None)
    if valve_result.intent_type in ["noise", "small_talk"]:
        return {"l1": sieve_result, "l2": {"intent_type": valve_result.intent_type}, "l3": None, "final_status": "rejected_at_l2"}

    purify_result = await purify(sieve_result["cleaned"], None)
    return {
        "l1": sieve_result,
        "l2": {"intent_type": valve_result.intent_type, "is_ambiguous": valve_result.is_ambiguous, "splits": valve_result.splits},
        "l3": {"user_content": purify_result.user_content, "importance_score": purify_result.importance_score, "keywords": purify_result.keywords, "topic_id": purify_result.topic_id, "summary": purify_result.summary},
        "final_status": "purified"
    }
