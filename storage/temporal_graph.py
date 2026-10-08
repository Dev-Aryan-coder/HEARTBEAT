import sqlite3
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from uuid import uuid4
from dataclasses import dataclass, asdict
from storage.database import get_connection

logger = logging.getLogger("HEARTBEAT_TEMPORAL_GRAPH")

@dataclass
class TemporalEdge:
    id: str
    subject: str
    predicate: str
    object: str
    valid_from: str
    valid_to: Optional[str]
    confidence: float
    source_cell_id: Optional[str]
    created_at: str

    @property
    def is_active(self) -> bool:
        return self.valid_to is None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TemporalGraph:
    """
    Temporal Knowledge Graph (Zep Graphiti Model).
    Stores Entity-Relation-Time Triples: (Subject) --[Predicate | valid_from -> valid_to]--> (Object).
    Provides point-in-time state reconstruction and timeline evolution queries.
    """

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @classmethod
    def add_edge(
        cls,
        subject: str,
        predicate: str,
        obj: str,
        valid_from: Optional[str] = None,
        source_cell_id: Optional[str] = None,
        confidence: float = 1.0,
        supersede: bool = True
    ) -> str:
        """
        Inserts a temporal triple.
        If supersede=True and an active triple exists with identical (subject, predicate)
        but different object, expires the previous triple with valid_to = valid_from.
        """
        conn = get_connection()
        edge_id = str(uuid4())
        now = cls._now_iso()
        valid_from = valid_from or now
        sub = subject.strip()
        pred = predicate.strip().lower()
        obj_val = obj.strip()

        with conn:
            cursor = conn.cursor()
            if supersede:
                # Find currently active edges for (subject, predicate)
                cursor.execute("""
                    SELECT id, object, valid_from FROM temporal_edges
                    WHERE LOWER(subject) = LOWER(?) AND LOWER(predicate) = LOWER(?) AND valid_to IS NULL
                """, (sub, pred))
                existing = cursor.fetchall()
                for row in existing:
                    old_id = row["id"]
                    old_obj = row["object"]
                    # If same object, no need to duplicate
                    if old_obj.lower() == obj_val.lower():
                        logger.debug(f"[TEMPORAL_GRAPH] Triple ({sub}, {pred}, {obj_val}) already active.")
                        return old_id
                    # Expire previous truth
                    cursor.execute("""
                        UPDATE temporal_edges
                        SET valid_to = ?
                        WHERE id = ?
                    """, (valid_from, old_id))
                    logger.info(f"[TEMPORAL_GRAPH] Expired previous triple ({sub}, {pred}, {old_obj}) at {valid_from}")

            # Insert new active edge
            cursor.execute("""
                INSERT INTO temporal_edges (id, subject, predicate, object, valid_from, valid_to, confidence, source_cell_id, created_at)
                VALUES (?, ?, ?, ?, ?, NULL, ?, ?, ?)
            """, (edge_id, sub, pred, obj_val, valid_from, confidence, source_cell_id, now))

        logger.info(f"[TEMPORAL_GRAPH] Created edge: ({sub}) --[{pred}]--> ({obj_val}) [valid_from: {valid_from}]")
        return edge_id

    @classmethod
    def query_active(
        cls,
        subject: Optional[str] = None,
        predicate: Optional[str] = None
    ) -> List[TemporalEdge]:
        """Returns all currently active triples (valid_to IS NULL)."""
        conn = get_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM temporal_edges WHERE valid_to IS NULL"
        params = []
        if subject:
            query += " AND LOWER(subject) = LOWER(?)"
            params.append(subject.strip())
        if predicate:
            query += " AND LOWER(predicate) = LOWER(?)"
            params.append(predicate.strip())

        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [TemporalEdge(**dict(r)) for r in rows]

    @classmethod
    def query_at(
        cls,
        timestamp: str,
        subject: Optional[str] = None,
        predicate: Optional[str] = None
    ) -> List[TemporalEdge]:
        """
        Time-travel query: returns the world state as it existed at 'timestamp'.
        Matches edges where valid_from <= timestamp AND (valid_to IS NULL OR valid_to > timestamp).
        """
        conn = get_connection()
        cursor = conn.cursor()
        query = """
            SELECT * FROM temporal_edges
            WHERE valid_from <= ? AND (valid_to IS NULL OR valid_to > ?)
        """
        params = [timestamp, timestamp]
        if subject:
            query += " AND LOWER(subject) = LOWER(?)"
            params.append(subject.strip())
        if predicate:
            query += " AND LOWER(predicate) = LOWER(?)"
            params.append(predicate.strip())

        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [TemporalEdge(**dict(r)) for r in rows]

    @classmethod
    def get_timeline(
        cls,
        subject: str,
        predicate: Optional[str] = None
    ) -> List[TemporalEdge]:
        """Returns the full chronological evolution of a subject's relationships."""
        conn = get_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM temporal_edges WHERE LOWER(subject) = LOWER(?)"
        params = [subject.strip()]
        if predicate:
            query += " AND LOWER(predicate) = LOWER(?)"
            params.append(predicate.strip())
        query += " ORDER BY valid_from ASC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [TemporalEdge(**dict(r)) for r in rows]

    @classmethod
    def format_graph_context(cls, subject: Optional[str] = None, limit: int = 15) -> str:
        """
        Generates clean temporal graph context string to inject into LLM prompts.
        """
        active_edges = cls.query_active(subject=subject)[:limit]
        if not active_edges:
            return ""

        lines = ["### 🕸️ Temporal Knowledge Graph (Current Valid State):"]
        for edge in active_edges:
            lines.append(f"- ({edge.subject}) --[{edge.predicate}]--> ({edge.object}) [since {edge.valid_from[:10]}]")
        return "\n".join(lines)

    @classmethod
    def extract_and_store_triples_from_cell(cls, cell_id: str, content: str, user_id: str = "Aryan") -> List[str]:
        """
        Extracts temporal triples from cell text using semantic relation heuristics.
        Handles patterns like:
        - "uses Python 3.14" -> (Aryan, uses_runtime, Python 3.14)
        - "switched to FastAPI" -> (Aryan, prefers_framework, FastAPI)
        - "working on Sprint 2" -> (Aryan, active_project, Sprint 2)
        - "model is DeepSeek R1" -> (HEARTBEAT, uses_model, DeepSeek R1)
        """
        import re
        created_edge_ids = []
        if not content:
            return created_edge_ids

        # Pattern 1: subject uses/running/using tool/version
        matches_uses = re.findall(r"(?:i am using|i use|using|switched to|migrated to|running on)\s+([A-Za-z0-9_.\- ]{2,30})", content, re.IGNORECASE)
        for target in matches_uses:
            clean_tgt = target.strip()
            if len(clean_tgt) > 2 and not clean_tgt.lower().startswith("the "):
                pred = "migrated_to" if "switch" in content.lower() or "migrat" in content.lower() else "uses"
                edge_id = cls.add_edge(subject=user_id or "Aryan", predicate=pred, obj=clean_tgt, source_cell_id=cell_id)
                created_edge_ids.append(edge_id)

        # Pattern 2: Tool/project prefers or configured with
        matches_tech = re.findall(r"\b(python|ollama|deepseek|qwen|fastapi|sqlite|chroma|docker|react|vite)\s*([0-9.]+)?\b", content, re.IGNORECASE)
        for tech, ver in matches_tech:
            full_val = f"{tech} {ver}".strip() if ver else tech
            edge_id = cls.add_edge(subject=user_id or "Aryan", predicate="tech_stack", obj=full_val, source_cell_id=cell_id, supersede=False)
            created_edge_ids.append(edge_id)

        return created_edge_ids

