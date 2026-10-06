import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from cells.cell_model import BloodCell, CellType, CellStatus, MemoryTier
from storage.database import (
    init_database, save_cell, get_cell_by_id, delete_cell, 
    update_cell_tier, supersede_cell, decay_cell_importance, get_connection
)
from heart.metabolism import run_metabolic_cycle
from cells.chain_engine import create_cell_chain, reassemble_chain_content, should_chain

@pytest.fixture(autouse=True)
def setup_db():
    init_database()

def test_three_tier_model_and_persistence():
    """Verify that MemoryTier persists correctly in the biological database."""
    cell = BloodCell(
        cell_id="tier_test_001",
        user_id="MASTER_USER",
        chat_id="chat_001",
        message_id="msg_001",
        session_id="sess_001",
        cell_type=CellType.purified,
        status=CellStatus.active,
        memory_tier=MemoryTier.core_genome,
        user_raw_content="My fundamental engineering philosophy is radical transparency.",
        importance_score=9
    )
    save_cell(cell)

    fetched = get_cell_by_id("tier_test_001")
    assert fetched is not None
    assert fetched["memory_tier"] == "core_genome"
    assert fetched["importance_score"] == 9

def test_core_genome_decay_immunity():
    """Verify that Core Genome DNA is completely immune to decay."""
    cell = BloodCell(
        cell_id="tier_core_dna",
        user_id="MASTER_USER",
        chat_id="chat_001",
        message_id="msg_001",
        session_id="sess_001",
        cell_type=CellType.purified,
        status=CellStatus.active,
        memory_tier=MemoryTier.core_genome,
        user_raw_content="I am allergic to penicillin.",
        importance_score=10
    )
    save_cell(cell)

    # Attempt to decay core genome cell
    new_score = decay_cell_importance("tier_core_dna", decay_amount=3)
    assert new_score == 10  # Score remains untouched!

    fetched = get_cell_by_id("tier_core_dna")
    assert fetched["importance_score"] == 10
    assert fetched["status"] == "active"

def test_episodic_decay():
    """Verify that episodic cells decay and hibernate when importance drops <= 2."""
    cell = BloodCell(
        cell_id="tier_episodic_test",
        user_id="MASTER_USER",
        chat_id="chat_001",
        message_id="msg_001",
        session_id="sess_001",
        cell_type=CellType.purified,
        status=CellStatus.active,
        memory_tier=MemoryTier.episodic,
        user_raw_content="Working on project alpha sprint 2.",
        importance_score=3
    )
    save_cell(cell)

    new_score = decay_cell_importance("tier_episodic_test", decay_amount=2)
    assert new_score == 1  # 3 - 2 = 1

    fetched = get_cell_by_id("tier_episodic_test")
    assert fetched["importance_score"] == 1
    assert fetched["status"] == "dormant"  # Shifted to sleeping in Bones

def test_state_supremacy_superseding():
    """Verify Living Truth Resolution (old conflicting fact is superseded by new fact)."""
    old_cell = BloodCell(
        cell_id="old_truth_001",
        user_id="MASTER_USER",
        chat_id="chat_001",
        message_id="msg_001",
        session_id="sess_001",
        cell_type=CellType.purified,
        status=CellStatus.active,
        topic_id="editor_preference",
        user_raw_content="I use VS Code for coding."
    )
    save_cell(old_cell)

    new_cell_id = "new_truth_002"
    supersede_cell(old_cell.cell_id, new_cell_id)

    fetched_old = get_cell_by_id("old_truth_001")
    assert fetched_old["status"] == "expired"
    assert fetched_old["superseded_by"] == new_cell_id

def test_cell_pruning():
    """Verify that user can manually prune/dissolve a memory cell."""
    cell = BloodCell(
        cell_id="cell_to_prune",
        user_id="MASTER_USER",
        chat_id="chat_001",
        message_id="msg_001",
        session_id="sess_001",
        cell_type=CellType.purified,
        status=CellStatus.active,
        user_raw_content="Temporary secret note."
    )
    save_cell(cell)
    assert get_cell_by_id("cell_to_prune") is not None

    deleted = delete_cell("cell_to_prune")
    assert deleted is True
    assert get_cell_by_id("cell_to_prune") is None

def test_metabolic_pulse_telemetry():
    """Verify the biological metabolic pulse cycle execution and telemetry generation."""
    telemetry = asyncio.run(run_metabolic_cycle("MASTER_USER"))
    assert "heart_rate_bpm" in telemetry
    assert "circulating_active" in telemetry
    assert "core_genome_dna" in telemetry
    assert "blood_pressure" in telemetry
    assert telemetry["heart_rate_bpm"] >= 60

def test_chain_cell_engine():
    """Verify chunking and seamless reassembly of large content (>2000 tokens)."""
    large_text = "Paragraph one with detailed architecture information.\n\n" * 80
    assert should_chain(large_text) is True

    base_cell = BloodCell(
        cell_id="chain_base_test",
        user_id="MASTER_USER",
        chat_id="chat_001",
        message_id="msg_001",
        session_id="sess_001",
        cell_type=CellType.purified,
        status=CellStatus.active,
        user_raw_content="Explain the entire HEARTBEAT biological architecture."
    )

    head, parts = create_cell_chain(base_cell, large_text)
    assert head.is_head is True
    assert head.is_chain is True
    assert head.chain_id is not None
    assert len(parts) > 0

    save_cell(head)
    for p in parts:
        save_cell(p)

    reassembled = reassemble_chain_content(head.chain_id)
    assert reassembled is not None
    assert "Paragraph one with detailed architecture information." in reassembled
