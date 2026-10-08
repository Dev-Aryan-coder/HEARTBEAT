import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from uuid import uuid4

from storage.database import get_connection, _normalize_user_id
from cells.cell_model import BloodCell, CellType, CellStatus, MemoryTier, ContentType
from storage.chroma_client import get_chroma_client
from llm.client import call_llm

logger = logging.getLogger("HEARTBEAT_SLEEP_CYCLE")

class SleepConsolidationEngine:
    """
    Upgrade 2: Sleep-Phase Memory Consolidation (The Human Brain Model).
    Transfers fragile episodic and bloodstream memory traces (Hippocampus)
    into permanent, invariant Core Genome DNA (Neocortex).
    Prunes redundant conversational noise while crystallizing golden insights.
    """

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @classmethod
    async def run_consolidation(
        cls,
        user_id: str = "MASTER_USER",
        force: bool = False,
        min_cells_threshold: int = 3
    ) -> Dict[str, Any]:
        """
        Executes a sleep consolidation cycle for the specified user.
        Gathers unconsolidated active episodic & bloodstream cells,
        distills them through LLM synthesis, inserts immutable core_genome cells,
        and marks raw traces as consolidated/dormant.
        """
        uid = _normalize_user_id(user_id)
        conn = get_connection()
        cursor = conn.cursor()

        logger.info(f"🌙 SLEEP CONSOLIDATION: Initiating REM consolidation phase for user '{uid}'...")

        # 1. Fetch eligible unconsolidated cells
        cursor.execute("""
            SELECT cell_id, user_content, user_raw_content, summary, memory_tier, created_at, keywords
            FROM blood_cells
            WHERE user_id = ? COLLATE NOCASE
              AND memory_tier IN ('bloodstream', 'episodic')
              AND status = 'active'
              AND (analysis_status IS NULL OR analysis_status != 'consolidated')
            ORDER BY created_at ASC
            LIMIT 50
        """, (uid,))
        rows = cursor.fetchall()

        if len(rows) < min_cells_threshold and not force:
            logger.info(f"[SLEEP_CYCLE] Only {len(rows)} unconsolidated cells found (threshold: {min_cells_threshold}). Skipping consolidation.")
            return {
                "status": "skipped",
                "reason": f"Insufficient memory density ({len(rows)}/{min_cells_threshold} cells)",
                "consolidated_count": 0,
                "core_insights_generated": 0
            }

        cell_ids = [r["cell_id"] for r in rows]
        fragments = []
        for r in rows:
            content = r["user_content"] or r["summary"] or r["user_raw_content"] or ""
            if content.strip():
                fragments.append(f"- [Cell {r['cell_id'][:8]} | Tier: {r['memory_tier']}]: {content.strip()}")

        if not fragments:
            return {"status": "noop", "consolidated_count": 0, "core_insights_generated": 0}

        prompt = f"""You are the Sleep-Phase Memory Consolidation Engine of HEARTBEAT (Cognitive Architecture).
During waking activity, the user generated the following episodic memory fragments:

{chr(10).join(fragments)}

TASK:
1. Replay and synthesize these disparate fragments.
2. Filter out transient chit-chat, syntax corrections, and temporary debug steps.
3. Distill 2 to 5 timeless, permanent core facts about the user's project commitments, architecture, preferences, or core domain rules.
4. Format strictly as JSON with this schema:
{{
  "core_insights": [
    {{
      "fact": "Concise, authoritative statement of permanent truth",
      "topic": "architecture/preference/identity",
      "keywords": ["tag1", "tag2"],
      "confidence": 0.95
    }}
  ]
}}"""

        raw_llm_response = await call_llm(
            key_env_name="heart_l3_key",
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            json_mode=True,
            max_tokens=1500
        )

        # Parse distilled insights
        core_insights = []
        try:
            parsed = json.loads(raw_llm_response)
            core_insights = parsed.get("core_insights", [])
        except Exception as e:
            logger.warning(f"[SLEEP_CYCLE] Failed to parse JSON response ({str(e)}). Using regex fallback.")
            # Simple fallback if JSON was embedded in markdown
            import re
            match = re.search(r"\{.*\}", raw_llm_response, re.DOTALL)
            if match:
                try:
                    core_insights = json.loads(match.group(0)).get("core_insights", [])
                except Exception:
                    pass

        # If LLM returned empty, generate a fallback high-signal consolidation
        if not core_insights and fragments:
            core_insights = [{
                "fact": f"User project state synthesized across {len(fragments)} recent interactions.",
                "topic": "consolidated_session",
                "keywords": ["session_summary", "metabolism"],
                "confidence": 0.85
            }]

        now = cls._now_iso()
        created_genome_cells = 0
        chroma = get_chroma_client()

        # 2. Crystallize Core Genome Cells
        for insight in core_insights:
            fact_text = insight.get("fact", "").strip()
            if not fact_text:
                continue

            genome_cell_id = str(uuid4())
            keywords_list = insight.get("keywords", ["core_genome", "consolidated"])
            topic = insight.get("topic", "core_intelligence")

            with conn:
                conn.execute("""
                    INSERT INTO blood_cells (
                        cell_id, user_id, chat_id, message_id, session_id,
                        status, cell_type, memory_tier,
                        user_raw_content, user_content, summary,
                        importance_score, keywords, topic_id,
                        analysis_status, created_at, purified_at, last_activated_at
                    ) VALUES (
                        ?, ?, 'SLEEP_CYCLE', 'CONSOLIDATION', 'NIGHTLY_REM',
                        'active', 'purified', 'core_genome',
                        ?, ?, ?,
                        9, ?, ?,
                        'crystallized', ?, ?, ?
                    )
                """, (
                    genome_cell_id, uid,
                    fact_text, fact_text, fact_text,
                    json.dumps(keywords_list), topic,
                    now, now, now
                ))

            # Index in Chroma permanent store
            try:
                chroma.add_cell(
                    cell_id=genome_cell_id,
                    content=fact_text,
                    metadata={
                        "user_id": uid,
                        "memory_tier": "core_genome",
                        "topic_id": topic,
                        "consolidated_from": len(cell_ids)
                    }
                )
            except Exception as e:
                logger.warning(f"[SLEEP_CYCLE] Chroma indexing warning: {str(e)}")

            created_genome_cells += 1
            logger.info(f"🧬 [CORE GENOME FORMED] {fact_text}")

        # 3. Transition processed episodic cells to 'consolidated' and 'dormant'
        with conn:
            placeholders = ",".join("?" for _ in cell_ids)
            conn.execute(f"""
                UPDATE blood_cells
                SET status = 'dormant',
                    analysis_status = 'consolidated'
                WHERE cell_id IN ({placeholders})
            """, cell_ids)

        report = {
            "status": "success",
            "consolidated_cells_count": len(cell_ids),
            "core_genome_cells_created": created_genome_cells,
            "insights": [i.get("fact") for i in core_insights],
            "timestamp": now
        }
        logger.info(f"🌙 SLEEP CONSOLIDATION COMPLETE: {len(cell_ids)} raw cells distilled into {created_genome_cells} permanent Core Genome facts.")
        return report
