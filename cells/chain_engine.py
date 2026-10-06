import logging
from typing import List, Tuple, Optional
from uuid import uuid4
from cells.cell_model import BloodCell, CellType, CellStatus, MemoryTier
from storage.database import get_connection, save_link_vault_entry, save_cell

logger = logging.getLogger("HEARTBEAT_CHAIN_ENGINE")

CHUNK_WORD_LIMIT = 250  # Slice boundary for chain cells (~350 tokens)

def should_chain(text: str) -> bool:
    """Returns True if content is large enough to require chain cell splitting."""
    if not text:
        return False
    return len(text.split()) > CHUNK_WORD_LIMIT

def split_content_into_chunks(text: str, chunk_size: int = CHUNK_WORD_LIMIT) -> List[str]:
    """Splits a large body of text into sequential word chunks preserving paragraph boundaries."""
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = []
    current_words = 0

    for para in paragraphs:
        para_words = len(para.split())
        if current_words + para_words > chunk_size and current_chunk:
            chunks.append("\n\n".join(current_chunk))
            current_chunk = [para]
            current_words = para_words
        else:
            current_chunk.append(para)
            current_words += para_words

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks if chunks else [text]

def create_cell_chain(
    base_cell: BloodCell, 
    full_response: str
) -> Tuple[BloodCell, List[BloodCell]]:
    """
    Creates a Chain Cell network for large content:
    - Generates HEAD cell (Part 1) that will circulate in bloodstream.
    - Generates child parts (Parts 2..N) stored in vault.
    - Links each part to the next via next_cell_id.
    """
    chunks = split_content_into_chunks(full_response, CHUNK_WORD_LIMIT)
    total_parts = len(chunks)

    if total_parts <= 1:
        # Fits in normal cell
        base_cell.ai_response_full = full_response
        base_cell.is_chain = False
        return base_cell, []

    chain_id = f"chain_{uuid4().hex[:12]}"
    part_cells = []
    part_ids = [str(uuid4()) for _ in range(total_parts)]

    # 1. Configure HEAD cell (Part 1)
    head_cell = base_cell.model_copy()
    head_cell.cell_id = part_ids[0]
    head_cell.is_head = True
    head_cell.is_chain = True
    head_cell.chain_id = chain_id
    head_cell.part_number = 1
    head_cell.total_parts = total_parts
    head_cell.next_cell_id = part_ids[1] if total_parts > 1 else None
    head_cell.ai_response_full = chunks[0]
    head_cell.memory_tier = MemoryTier.bloodstream
    
    # Save cell first, then vault entry for head
    link_id = f"link_{head_cell.cell_id}"
    head_cell.link_id = link_id
    save_cell(head_cell)
    save_link_vault_entry(link_id, head_cell.cell_id, "text", chunks[0], 1, total_parts, user_id=head_cell.user_id)

    # 2. Build remaining parts
    for i in range(1, total_parts):
        next_id = part_ids[i + 1] if i + 1 < total_parts else None
        p_cell = base_cell.model_copy()
        p_cell.cell_id = part_ids[i]
        p_cell.is_head = False
        p_cell.is_chain = True
        p_cell.chain_id = chain_id
        p_cell.part_number = i + 1
        p_cell.total_parts = total_parts
        p_cell.next_cell_id = next_id
        p_cell.ai_response_full = chunks[i]
        p_cell.status = CellStatus.dormant  # Child parts sleep in Bones until requested
        p_cell.memory_tier = MemoryTier.episodic
        
        part_link_id = f"link_{p_cell.cell_id}"
        p_cell.link_id = part_link_id
        save_cell(p_cell)
        save_link_vault_entry(part_link_id, p_cell.cell_id, "text", chunks[i], i + 1, total_parts, user_id=p_cell.user_id)
        part_cells.append(p_cell)

    logger.info(f"🧬 CHAIN CREATED: chain_id={chain_id} with {total_parts} parts.")
    return head_cell, part_cells

def reassemble_chain_content(chain_id: str) -> Optional[str]:
    """
    Reassembles full content of a chain cell by fetching all parts in sequence.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT full_content, part_number 
        FROM link_vault lv
        JOIN blood_cells bc ON lv.cell_id = bc.cell_id
        WHERE bc.chain_id = ?
        ORDER BY lv.part_number ASC
    """, (chain_id,))
    rows = cursor.fetchall()
    
    if not rows:
        return None

    return "\n\n".join([row['full_content'] for row in rows])
