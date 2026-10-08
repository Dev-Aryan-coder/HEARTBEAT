import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from storage.database import get_connection, init_database, ensure_user
from storage.temporal_graph import TemporalGraph
from storage.synaptic_network import SynapticNetwork
from heart.sleep_cycle import SleepConsolidationEngine
from circulation.ambient_sensor import AmbientSensor
from storage.database_ops import get_semantic_memory, persist_purified_cell
from cells.cell_model import BloodCell, CellType, CellStatus, MemoryTier

@pytest.fixture(autouse=True)
def setup_db():
    init_database()
    ensure_user("MASTER_USER")
    ensure_user("Aryan")
    ensure_user("CONSOLIDATION_TEST_USER")
    conn = get_connection()
    with conn:
        conn.execute("DELETE FROM temporal_edges")
        conn.execute("DELETE FROM synaptic_links")
        conn.execute("DELETE FROM ambient_events")
        conn.execute("DELETE FROM blood_cells WHERE user_id = 'CONSOLIDATION_TEST_USER'")
    yield

def test_temporal_knowledge_graph_superseding():
    """Upgrade 1: Test temporal entity-relation-time triples and edge expiry."""
    # Day 1: Aryan uses Python 3.12
    t1 = "2026-05-01T10:00:00Z"
    edge1 = TemporalGraph.add_edge("Aryan", "uses_runtime", "Python 3.12", valid_from=t1)
    
    # Check active state at t1
    active_edges = TemporalGraph.query_active(subject="Aryan", predicate="uses_runtime")
    assert len(active_edges) == 1
    assert active_edges[0].object == "Python 3.12"
    assert active_edges[0].valid_to is None

    # Day 2: Aryan updates runtime to Python 3.14 (supersedes 3.12)
    t2 = "2026-10-07T14:00:00Z"
    edge2 = TemporalGraph.add_edge("Aryan", "uses_runtime", "Python 3.14", valid_from=t2, supersede=True)

    # Current active truth must now be Python 3.14
    current_edges = TemporalGraph.query_active(subject="Aryan", predicate="uses_runtime")
    assert len(current_edges) == 1
    assert current_edges[0].object == "Python 3.14"

    # Time-travel query: What was Aryan using back in June 2026?
    june_query = TemporalGraph.query_at("2026-06-15T12:00:00Z", subject="Aryan", predicate="uses_runtime")
    assert len(june_query) == 1
    assert june_query[0].object == "Python 3.12"

    # Timeline query: Chronological evolution
    timeline = TemporalGraph.get_timeline("Aryan", predicate="uses_runtime")
    assert len(timeline) == 2
    assert timeline[0].object == "Python 3.12"
    assert timeline[1].object == "Python 3.14"

def test_hebbian_synaptic_reinforcement():
    """Upgrade 3: Test 'neurons that fire together, wire together'."""
    cell_a = "cell_fastapi_01"
    cell_b = "cell_nemotron_02"
    cell_c = "cell_ollama_03"

    # Initial co-occurrence of A and B
    boosted = SynapticNetwork.reinforce_co_occurrence([cell_a, cell_b], boost=0.2)
    assert boosted == 1

    # Second co-occurrence of A and B
    SynapticNetwork.reinforce_co_occurrence([cell_a, cell_b], boost=0.2)

    # Co-occurrence of A and C
    SynapticNetwork.reinforce_co_occurrence([cell_a, cell_c], boost=0.2)

    # Associative priming from cell_a
    neighbors = SynapticNetwork.get_associated_cells([cell_a], top_k=5)
    neighbor_ids = [n["cell_id"] for n in neighbors]
    assert cell_b in neighbor_ids
    assert cell_c in neighbor_ids

    # Cell B should have higher weight because it fired twice
    b_info = next(n for n in neighbors if n["cell_id"] == cell_b)
    c_info = next(n for n in neighbors if n["cell_id"] == cell_c)
    assert b_info["synaptic_weight"] > c_info["synaptic_weight"]
    assert b_info["co_fired_count"] == 2

def test_ambient_sensor_git_probe():
    """Upgrade 4: Test silent ambient perception probe on workspace."""
    sensor = AmbientSensor()
    git_state = sensor.probe_git_state()
    assert git_state is not None
    assert "branch" in git_state
    assert "commit_hash" in git_state

    # Test event recording
    event_id = sensor.record_ambient_event(
        event_type="test_ambient",
        summary="User refactored storage layer to use WAL mode",
        details={"module": "storage/database.py", "wal": True},
        user_id="MASTER_USER"
    )
    assert event_id is not None

def test_sleep_phase_consolidation():
    """Upgrade 2: Test Hippocampus -> Neocortex consolidation."""
    async def _async_test():
        conn = get_connection()
        uid = "CONSOLIDATION_TEST_USER"
        now = datetime.now(timezone.utc).isoformat()

        # Insert 3 noisy episodic cells
        for i in range(3):
            conn.execute("""
                INSERT INTO blood_cells (
                    cell_id, user_id, chat_id, message_id, session_id,
                    status, cell_type, memory_tier,
                    user_raw_content, user_content, summary,
                    importance_score, analysis_status, created_at
                ) VALUES (?, ?, 'CHAT_1', ?, 'SESS_1', 'active', 'raw', 'episodic', ?, ?, ?, 5, 'pending', ?)
            """, (
                f"test_ep_cell_{i}", uid, f"msg_{i}",
                f"User prefers Python 3.14 and Ollama model qwen2.5-coder step {i}",
                f"User prefers Python 3.14 and Ollama model qwen2.5-coder step {i}",
                f"Preference fragment {i}",
                now
            ))
        conn.commit()

        # Run sleep consolidation with force=True
        report = await SleepConsolidationEngine.run_consolidation(user_id=uid, force=True, min_cells_threshold=2)
        assert report["status"] == "success"
        assert report["consolidated_cells_count"] >= 3
        assert report["core_genome_cells_created"] >= 1

        # Verify that raw cells became dormant
        cursor = conn.cursor()
        cursor.execute("SELECT status, analysis_status FROM blood_cells WHERE cell_id = 'test_ep_cell_0'")
        row = cursor.fetchone()
        assert row["status"] == "dormant"
        assert row["analysis_status"] == "consolidated"

        # Verify that a core_genome cell was born
        cursor.execute("SELECT memory_tier FROM blood_cells WHERE user_id = ? AND memory_tier = 'core_genome'", (uid,))
        genome_rows = cursor.fetchall()
        assert len(genome_rows) >= 1

    asyncio.run(_async_test())
