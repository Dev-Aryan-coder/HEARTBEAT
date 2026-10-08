import pytest
import asyncio
from datetime import datetime, timezone
from cells.cell_model import BloodCell, CellType, CellStatus, MemoryTier
from storage.database import (
    init_database, save_cell, get_cell_by_id, get_cells_by_user,
    supersede_cell, delete_cell, get_connection
)
from storage.chroma_client import get_chroma_manager
from storage.database_ops import persist_purified_cell, get_semantic_memory
from heart.level4_metacognition import MetacognitiveEngine, metacognitive_reflect
from heart.pipeline import run_pipeline

@pytest.fixture(autouse=True)
def setup_clean_db():
    init_database()
    # Clean test tables safely with child cascade
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM temporal_edges WHERE source_cell_id IN (SELECT cell_id FROM blood_cells WHERE user_id LIKE 'BENCHMARK_%')")
    cursor.execute("DELETE FROM ambient_events WHERE cell_id IN (SELECT cell_id FROM blood_cells WHERE user_id LIKE 'BENCHMARK_%')")
    cursor.execute("DELETE FROM link_vault WHERE cell_id IN (SELECT cell_id FROM blood_cells WHERE user_id LIKE 'BENCHMARK_%')")
    cursor.execute("DELETE FROM blood_cells WHERE user_id LIKE 'BENCHMARK_%'")
    conn.commit()

# =====================================================================
# BENCHMARK SUITE 1: STATE SUPREMACY (LIVING TRUTH RESOLUTION)
# =====================================================================

def test_benchmark_state_supremacy_python_upgrade():
    """
    Direct model evaluation benchmark for the user's exact scenario:
    'I use Python 3.12' -> 'I moved from Python 3.12 to 3.14'
    Verifies that:
    1. The old fact is marked 'expired' and superseded_by new cell id in SQLite.
    2. The old fact is completely evicted from ChromaDB vector space.
    3. get_semantic_memory returns ONLY the new truth, preventing contradictory prompt injection.
    """
    user_id = "BENCHMARK_USER_PY"
    chroma = get_chroma_manager()

    # Turn 1: User introduces Python 3.12
    old_cell = BloodCell(
        cell_id="cell_py_312",
        user_id=user_id,
        chat_id="chat_py",
        message_id="msg_001",
        session_id="sess_001",
        cell_type=CellType.purified,
        status=CellStatus.active,
        memory_tier=MemoryTier.episodic,
        topic_id="python_version",
        keywords=["python", "version", "3.12", "runtime"],
        user_raw_content="I use Python 3.12 for my backend development.",
        user_content="User uses Python 3.12 for backend development.",
        summary="User python version is 3.12",
        importance_score=7
    )
    asyncio.run(persist_purified_cell(old_cell))

    # Verify Turn 1 is active in SQLite and ChromaDB
    active_cells = get_cells_by_user(user_id, status="active")
    assert len(active_cells) == 1
    assert active_cells[0]["cell_id"] == "cell_py_312"

    chroma_hits = get_semantic_memory(user_id, "Python version", limit=5)
    assert any("3.12" in h.get("document", "") for h in chroma_hits)

    # Turn 2: User upgrades to Python 3.14
    new_cell = BloodCell(
        cell_id="cell_py_314",
        user_id=user_id,
        chat_id="chat_py",
        message_id="msg_002",
        session_id="sess_001",
        cell_type=CellType.purified,
        status=CellStatus.active,
        memory_tier=MemoryTier.episodic,
        topic_id="python_version",
        keywords=["python", "version", "3.14", "runtime", "upgrade"],
        user_raw_content="I moved from Python 3.12 to 3.14.",
        user_content="User upgraded backend from Python 3.12 to Python 3.14.",
        summary="User python version is now 3.14",
        importance_score=8
    )

    # Execute State Supremacy Resolution
    superseded = supersede_cell(old_cell.cell_id, new_cell.cell_id)
    assert superseded is True
    asyncio.run(persist_purified_cell(new_cell))

    # VERIFICATION 1: SQLite State Supremacy
    old_record = get_cell_by_id(old_cell.cell_id)
    assert old_record["status"] == "expired", "Old cell MUST be expired"
    assert old_record["superseded_by"] == new_cell.cell_id, "Old cell MUST point to new truth"

    new_record = get_cell_by_id(new_cell.cell_id)
    assert new_record["status"] == "active", "New cell MUST be active"

    active_user_cells = get_cells_by_user(user_id, status="active")
    assert len(active_user_cells) == 1
    assert active_user_cells[0]["cell_id"] == "cell_py_314"
    assert "3.14" in active_user_cells[0]["summary"]

    # VERIFICATION 2: ChromaDB Vector Eviction (Zero Contradiction Guarantee)
    # The old cell 'cell_py_312' must NEVER appear in semantic query
    semantic_results = get_semantic_memory(user_id, "What version of Python do I use?", limit=5)
    for hit in semantic_results:
        assert hit["id"] != old_cell.cell_id, f"Expired cell {old_cell.cell_id} leaked into vector search!"
        assert "3.12" not in hit.get("document", "") or "moved from" in hit.get("document", "")


def test_benchmark_multi_turn_cascading_supersession():
    """
    Tests 4 sequential contradictory updates to verify cascading state supremacy:
    MySQL -> PostgreSQL -> CockroachDB -> SQLite
    """
    user_id = "BENCHMARK_USER_DB_CASCADE"
    db_sequence = [
        ("cell_db_1", "MySQL", "My primary database is MySQL"),
        ("cell_db_2", "PostgreSQL", "Actually I migrated from MySQL to PostgreSQL"),
        ("cell_db_3", "CockroachDB", "We switched from PostgreSQL to CockroachDB"),
        ("cell_db_4", "SQLite", "We settled permanently on SQLite for simplicity")
    ]

    last_cell_id = None
    for cell_id, db_name, content in db_sequence:
        cell = BloodCell(
            cell_id=cell_id,
            user_id=user_id,
            chat_id="chat_cascade",
            message_id=f"msg_{cell_id}",
            session_id="sess_001",
            cell_type=CellType.purified,
            status=CellStatus.active,
            topic_id="database_choice",
            keywords=["database", "storage", db_name.lower()],
            user_raw_content=content,
            summary=f"Database choice is {db_name}",
            importance_score=7
        )
        if last_cell_id:
            supersede_cell(last_cell_id, cell.cell_id)
        asyncio.run(persist_purified_cell(cell))
        last_cell_id = cell_id

    # Verify only the final cell (SQLite) is active
    active_cells = get_cells_by_user(user_id, status="active")
    assert len(active_cells) == 1
    assert active_cells[0]["cell_id"] == "cell_db_4"
    assert "SQLite" in active_cells[0]["summary"]

    # Verify all previous cells are expired
    for prev_id in ["cell_db_1", "cell_db_2", "cell_db_3"]:
        row = get_cell_by_id(prev_id)
        assert row["status"] == "expired"
        assert row["superseded_by"] is not None

    # Verify semantic search returns SQLite as the only active candidate
    hits = get_semantic_memory(user_id, "What is my primary database?", limit=5)
    assert len(hits) >= 1
    assert hits[0]["id"] == "cell_db_4"


def test_benchmark_negative_control_non_conflicting_facts():
    """
    Verifies that distinct facts on different topics are NEVER superseded.
    """
    user_id = "BENCHMARK_USER_INDEPENDENT"
    facts = [
        ("fact_lang", "programming_language", ["python", "lang"], "I program in Python 3.14"),
        ("fact_city", "user_location", ["city", "location"], "I live in Berlin"),
        ("fact_theme", "ui_preference", ["ui", "theme", "dark"], "I prefer dark mode UI")
    ]

    for cid, topic, kws, text in facts:
        c = BloodCell(
            cell_id=cid,
            user_id=user_id,
            chat_id="chat_indep",
            message_id=f"msg_{cid}",
            session_id="sess_001",
            cell_type=CellType.purified,
            status=CellStatus.active,
            topic_id=topic,
            keywords=kws,
            user_raw_content=text,
            summary=text,
            importance_score=6
        )
        asyncio.run(persist_purified_cell(c))

    active = get_cells_by_user(user_id, status="active")
    assert len(active) == 3, "Non-conflicting facts must all remain active"


# =====================================================================
# BENCHMARK SUITE 2: SYSTEM 2 METACOGNITIVE GATE AUDITING
# =====================================================================

def test_benchmark_metacognitive_gate_adversarial_amnesia_suite():
    """
    Exhaustive 10-case adversarial evaluation testing whether LLM amnesia tropes
    are completely intercepted and neutralized by the Metacognitive Gate.
    """
    adversarial_drafts = [
        ("As an AI language model, I do not have personal memories.", "What was my tech stack?"),
        ("I don't have access to past conversations, but here is some advice.", "What did I ask earlier?"),
        ("I cannot recall our previous chats. Could you remind me?", "Remember my framework?"),
        ("I do not retain any memory across sessions, sorry.", "What version of Python do I use?"),
        ("As a machine learning model, I have no memory of what you said.", "Which database did I pick?"),
        ("I have no access to our previous conversations.", "What is my project goal?"),
        ("I don't possess personal memories, however you asked about databases.", "Which DB did I choose?"),
        ("I don't have the ability to remember past messages.", "Do you remember my favorite tool?"),
        ("I cannot access our past chats at this moment.", "What was my architecture design?"),
        ("As an AI, I don't remember your preferred framework.", "What framework did I select?")
    ]

    forbidden_tokens = [
        "as an ai", "machine learning model", "don't have access to past",
        "cannot recall our previous", "do not retain any memory",
        "have no memory of what you said", "no access to our previous conversations",
        "don't possess personal memories", "don't have the ability to remember"
    ]

    for draft, query in adversarial_drafts:
        audited = metacognitive_reflect(draft, query, bio_facts=["User uses Python 3.14 with SQLite."])
        audited_lower = audited.lower()

        # Zero-tolerance check: No amnesiac disclaimers allowed through the gate
        for token in forbidden_tokens:
            assert token not in audited_lower, f"Metacognitive gate leaked amnesia token '{token}' in: {audited}"

        # Must assert biological subconscious authority
        assert "subconscious" in audited_lower or "recollection" in audited_lower or "heartbeat" in audited_lower


def test_benchmark_metacognitive_fact_grounding_verification():
    """
    Verifies that when a user asks a memory retrieval question ('what version of python'),
    the Metacognitive Gate enforces subconscious grounding against active bio-facts.
    """
    user_query = "What version of Python do I use?"
    vague_llm_draft = "You are currently developing on a modern, high-performance runtime."
    bio_facts = [
        "BIO-FACT [EPISODIC | python_version]: User upgraded backend to Python 3.14."
    ]

    audited = metacognitive_reflect(vague_llm_draft, user_query, bio_facts=bio_facts)

    assert "> [!NOTE]" in audited
    assert "Subconscious Verification" in audited
    assert "1 verified bio-facts" in audited


def test_benchmark_metacognitive_depth_expansion_and_crystallization():
    """
    Verifies that shallow one-sentence responses are expanded into authoritative briefs
    with neural retention analysis and memory crystallization anchors.
    """
    shallow_draft = "You are on Python 3.14."
    query = "Confirm my current runtime."

    audited = metacognitive_reflect(shallow_draft, query)
    assert "### 💓 Executive Brief" in audited
    assert "### 🧠 Neural Retention Analysis" in audited
    assert "Memory Crystallization" in audited


def test_benchmark_nli_truth_arbitration():
    """
    Directly evaluates genuine Natural Language Inference (NLI) truth arbitration
    on nuanced real-world contradiction vs coexistence scenarios.
    """
    from heart.nli_arbitrator import arbitrate_truth_supremacy

    # 1. Real Contradiction: Migration
    res1 = asyncio.run(arbitrate_truth_supremacy(
        existing_fact="I use MySQL for all database storage.",
        new_statement="We dropped MySQL and migrated our database to PostgreSQL."
    ))
    assert res1["supersedes"] is True, f"Expected supersedes=True, got {res1}"

    # 2. Real Coexistence: Multilingual tooling (Must NOT supersede!)
    res2 = asyncio.run(arbitrate_truth_supremacy(
        existing_fact="I use Python 3.14 for my backend service.",
        new_statement="I also started learning Rust for WebAssembly tools."
    ))
    assert res2["supersedes"] is False, f"Expected supersedes=False for complementary tool, got {res2}"


def test_benchmark_metacognitive_technical_context_protection():
    """
    CRITICAL FALSE-POSITIVE TEST:
    Ensures that when a user asks a genuine computer science question about AI,
    the Metacognitive Gate does NOT censor legitimate technical explanations of AI.
    """
    technical_query = "How does an AI language model process tokens in transformers?"
    technical_draft = (
        "An AI language model processes text by converting tokens into numerical vectors "
        "and applying multi-head self-attention mechanisms to determine contextual relationships."
    )

    audited = metacognitive_reflect(technical_draft, technical_query)

    # Must preserve the technical computer science explanation without butchering
    assert "ai language model" in audited.lower() or "ai" in audited.lower()
    assert "tokens" in audited.lower()
    assert "attention" in audited.lower()
