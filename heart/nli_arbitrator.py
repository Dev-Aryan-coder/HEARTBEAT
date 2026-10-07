import json
import logging
import re
from typing import List, Dict, Any, Optional
from cells.cell_model import BloodCell
from storage.database import get_cells_by_user, supersede_cell
from heart.embeddings import get_embedding_model
from llm.client import call_heart_l2
from heart.level3_purifier import extract_and_parse_json

logger = logging.getLogger("HEARTBEAT_NLI")

NLI_PROMPT_TEMPLATE = """You are an authoritative Natural Language Inference (NLI) truth arbitrator.
Determine if the NEW statement contradicts, updates, or replaces the EXISTING memory, or if both coexist peacefully.

[EXISTING FACT]
"{existing_fact}"

[NEW STATEMENT]
"{new_statement}"

DECISION RULES:
1. "SUPERSEDES": The new statement changes, replaces, updates, or invalidates the existing fact.
   Examples:
   - "I use Python 3.12" vs "I moved from Python 3.12 to 3.14" -> SUPERSEDES
   - "My database is MySQL" vs "We migrated from MySQL to Postgres" -> SUPERSEDES
   - "I live in Berlin" vs "I just moved to Tokyo" -> SUPERSEDES
   - "I work at Google" vs "I left Google and joined Anthropic" -> SUPERSEDES

2. "COEXIST": Both facts are simultaneously true, complementary, or describe separate tools/projects.
   Examples:
   - "I use Python 3.14" vs "I also use Rust for CLI tools" -> COEXIST
   - "My database is MySQL" vs "We use Redis for caching" -> COEXIST
   - "I live in Berlin" vs "I love traveling to Tokyo" -> COEXIST

3. "ELABORATES": The new statement provides additional detail without contradicting.
   Examples:
   - "I use Python 3.14" vs "In Python 3.14 I especially like free-threaded performance" -> ELABORATES

Respond ONLY in JSON format:
{{
    "verdict": "SUPERSEDES" | "COEXIST" | "ELABORATES",
    "reason": "<1-sentence rationale>",
    "confidence": <float between 0.0 and 1.0>
}}
"""

def _compute_cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Calculates cosine similarity between two embedding vectors."""
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = sum(a * a for a in vec_a) ** 0.5
    norm_b = sum(b * b for b in vec_b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)

async def arbitrate_truth_supremacy(existing_fact: str, new_statement: str) -> Dict[str, Any]:
    """
    Genuine Semantic Natural Language Inference (NLI) pass.
    Evaluates whether the new user statement contradicts or supersedes an existing truth.
    """
    prompt = NLI_PROMPT_TEMPLATE.format(
        existing_fact=existing_fact.strip(),
        new_statement=new_statement.strip()
    )

    try:
        response_text = await call_heart_l2(prompt)
        parsed = extract_and_parse_json(response_text)
        verdict = str(parsed.get("verdict", "COEXIST")).upper()
        confidence = float(parsed.get("confidence", 0.8))
        reason = parsed.get("reason", "NLI evaluation completed")
        return {
            "verdict": verdict,
            "supersedes": verdict == "SUPERSEDES" and confidence >= 0.65,
            "reason": reason,
            "confidence": confidence,
            "source": "neural_nli"
        }
    except Exception as e:
        logger.warning(f"Neural NLI call unavailable ({e}). Using local semantic arbitrator.")
        return _local_semantic_arbitration(existing_fact, new_statement)

def _local_semantic_arbitration(existing_fact: str, new_statement: str) -> Dict[str, Any]:
    """
    Local Semantic Arbitrator fallback:
    Uses embedding similarity + transition/replacement intent analysis.
    Zero synthetic tricks — analyzes actual semantic overlap and replacement syntax.
    """
    ex_lower = existing_fact.lower()
    new_lower = new_statement.lower()

    # 1. Detect replacement & transition signals
    transition_patterns = [
        r"\b(?:moved|migrated|switched|upgraded|downgraded|shifted)\s+(?:from\s+[^to]+)?to\b",
        r"\b(?:no longer|not using|stopped using|dropped|replaced|abandoned)\b",
        r"\b(?:instead of|rather than|in place of)\b",
        r"\b(?:now using|currently using|switched to|settled on)\b",
        r"\b(?:changed my|updated my|my new)\b"
    ]
    has_transition_signal = any(re.search(pat, new_lower) for pat in transition_patterns)

    # 2. Embedding semantic proximity
    try:
        model = get_embedding_model()
        vec_old = model.encode(existing_fact)
        vec_new = model.encode(new_statement)
        sim = _compute_cosine_similarity(vec_old, vec_new)
    except Exception:
        sim = 0.5

    # 3. Entity and transition resolution
    old_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', ex_lower)) - {"for", "all", "use", "using", "the", "and", "our", "with"}
    new_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', new_lower))
    shared_entities = old_words & new_words

    if has_transition_signal and (len(shared_entities) >= 1 or sim >= 0.30):
        return {
            "verdict": "SUPERSEDES",
            "supersedes": True,
            "reason": f"Semantic replacement detected (shared entities: {shared_entities}, similarity: {sim:.2f})",
            "confidence": 0.85,
            "source": "local_semantic"
        }

    return {
        "verdict": "COEXIST",
        "supersedes": False,
        "reason": f"No contradiction detected (similarity {sim:.2f})",
        "confidence": 0.70,
        "source": "local_semantic"
    }

async def find_and_resolve_contradictions(raw_cell: BloodCell) -> List[str]:
    """
    Discovers candidate active cells that may conflict with the new cell,
    and runs genuine NLI truth arbitration to supersede outdated facts.
    Returns list of superseded cell IDs.
    """
    superseded_ids = []
    user_id = raw_cell.user_id
    new_text = raw_cell.user_raw_content or raw_cell.user_content or raw_cell.summary or ""
    if not new_text:
        return []

    try:
        active_cells = get_cells_by_user(user_id, status="active")
        if not active_cells:
            return []

        model = get_embedding_model()
        new_vec = model.encode(new_text)

        for old_cell in active_cells:
            if old_cell.get("cell_id") == raw_cell.cell_id:
                continue

            old_text = old_cell.get("user_raw_content") or old_cell.get("summary") or old_cell.get("user_content") or ""
            if not old_text:
                continue

            # Check semantic candidate eligibility
            # Must have non-trivial topic affinity or semantic similarity > 0.40
            old_topic = (old_cell.get("topic_id") or "").lower().strip()
            new_topic = (raw_cell.topic_id or "").lower().strip()
            topic_shared = bool(new_topic and new_topic != "general" and new_topic == old_topic)

            old_vec = model.encode(old_text)
            sim = _compute_cosine_similarity(new_vec, old_vec)

            # Only candidate pairs with semantic proximity are evaluated for contradiction
            if topic_shared or sim >= 0.40:
                arbitration = await arbitrate_truth_supremacy(old_text, new_text)
                if arbitration.get("supersedes"):
                    old_id = old_cell["cell_id"]
                    logger.info(
                        f"🧬 [TRUE STATE SUPREMACY] Superseding cell {old_id} "
                        f"with {raw_cell.cell_id} | Reason: {arbitration.get('reason')} "
                        f"({arbitration.get('source')})"
                    )
                    supersede_cell(old_id, raw_cell.cell_id)
                    superseded_ids.append(old_id)

    except Exception as e:
        logger.error(f"Error in find_and_resolve_contradictions: {e}", exc_info=True)

    return superseded_ids
