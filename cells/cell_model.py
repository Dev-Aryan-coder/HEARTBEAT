from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from uuid import uuid4
from pydantic import BaseModel, Field

class PurifiedData(BaseModel):
    """L3 AI Output structure."""
    entities: List[str] = Field(default_factory=list)
    facts: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class CellType(str, Enum):
    raw = "raw"
    purified = "purified"

class CellStatus(str, Enum):
    pending_purification = "pending_purification"
    pending_clarification = "pending_clarification"
    active = "active"
    dormant = "dormant"
    expired = "expired"

class ContentType(str, Enum):
    text = "text"
    image = "image"
    audio = "audio"

class BloodCell(BaseModel):
    # IDENTITY FIELDS
    cell_id: str = Field(default_factory=lambda: str(uuid4()))
    cell_type: CellType
    status: CellStatus

    # ORIGIN FIELDS
    user_id: str
    chat_id: str
    message_id: str
    session_id: str

    # USER SIDE FIELDS
    user_raw_content: str
    user_content: Optional[str] = None
    user_content_type: ContentType = ContentType.text
    user_discarded: Optional[str] = None
    user_word_count: int = 0
    analysis_status: str = "pending"

    # AI RESPONSE FIELDS
    ai_raw_response: Optional[str] = None
    ai_response_summary: Optional[str] = None
    ai_response_full: Optional[str] = None
    ai_response_type: Optional[str] = None  # short/long/chain
    ai_response_link_id: Optional[str] = None
    ai_response_chain_id: Optional[str] = None
    ai_response_word_count: int = 0

    # HEART INTELLIGENCE FIELDS
    importance_score: Optional[int] = None  # 1-10
    keywords: List[str] = Field(default_factory=list)
    topic_id: Optional[str] = None
    summary: Optional[str] = None
    purified_data: Optional[PurifiedData] = None

    # AMBIGUITY FIELDS
    is_ambiguous: Optional[bool] = None
    clarification_question: Optional[str] = None
    clarification_answer: Optional[str] = None

    # CHAIN FIELDS
    is_head: Optional[bool] = None
    is_chain: bool = False
    chain_id: Optional[str] = None
    part_number: Optional[int] = None
    total_parts: Optional[int] = None
    next_cell_id: Optional[str] = None
    link_id: Optional[str] = None

    # DECAY FIELDS
    expires_at: Optional[datetime] = None
    last_activated_at: Optional[datetime] = None
    activation_count: int = 0

    # TIMESTAMP FIELDS
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    entered_artery_at: Optional[datetime] = None
    ai_responded_at: Optional[datetime] = None
    purified_at: Optional[datetime] = None
    entered_vein_at: Optional[datetime] = None

class CellFactory:
    @staticmethod
    def from_text(user_id: str, chat_id: str, message_id: str, session_id: str, content: str) -> BloodCell:
        return BloodCell(
            cell_type=CellType.raw,
            status=CellStatus.pending_purification,
            user_id=user_id,
            chat_id=chat_id,
            message_id=message_id,
            session_id=session_id,
            user_raw_content=content,
            user_content=content,
            user_content_type=ContentType.text,
            user_word_count=len(content.split())
        )
