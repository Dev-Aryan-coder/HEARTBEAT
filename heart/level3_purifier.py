import json
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, timedelta
from llm.client import call_heart_l3
from llm.prompts import build_heart_l3_prompt

@dataclass
class PurificationResult:
    user_content: str
    ai_response_summary: Optional[str]
    ai_response_full: Optional[str]
    ai_response_type: str
    importance_score: int
    keywords: List[str]
    topic_id: str
    summary: str
    expires_at: Optional[datetime]
    is_link: bool = False
    link_id: Optional[str] = None

def calculate_expiry(importance_score: int) -> Optional[datetime]:
    """Calculates expiry date based on 1-10 importance score."""
    now = datetime.utcnow()
    if importance_score <= 2:
        return now + timedelta(days=3)
    elif importance_score <= 4:
        return now + timedelta(days=7)
    elif importance_score <= 6:
        return now + timedelta(days=30)
    elif importance_score <= 8:
        return now + timedelta(days=180)
    else:
        return None  # Never expires

def determine_response_type(ai_response: str, token_limit: int = 500) -> str:
    """Classifies response as short, long, or chain."""
    word_count = len(ai_response.split())
    if word_count < 50:
        return "short"
    elif word_count < 200:
        return "long"
    else:
        return "chain"

async def purify(cleaned_text: str, ai_response: Optional[str] = None) -> PurificationResult:
    """Calls GPT-OSS-120B to extract structured user and AI data."""
    prompt = build_heart_l3_prompt(cleaned_text, ai_response)
    
    try:
        response_text = await call_heart_l3(prompt)
        data = json.loads(response_text)
    except json.JSONDecodeError as je:
        # ISSUE 1 FIX: Log explicitly so we know which cells got fake data
        import logging
        logging.warning(f"[L3 Purifier] JSON parse failed: {je}. Using fallback data for: '{cleaned_text[:60]}'")
        data = {
            "user_content": cleaned_text,
            "importance_score": 5,
            "keywords": ["neural_heartbeat"],
            "topic_id": "general",
            "summary": f"Interaction: {cleaned_text[:60]}"
        }
    except Exception as e:
        import logging
        logging.error(f"[L3 Purifier] LLM call failed: {e}. Using fallback data.")
        data = {
            "user_content": cleaned_text,
            "importance_score": 5,
            "keywords": ["neural_heartbeat"],
            "topic_id": "general",
            "summary": f"Interaction: {cleaned_text[:60]}"
        }
        
    importance_score = data.get("importance_score", 5)
    
    # 🔗 LINK CELL LOGIC (09)
    # If the response is over ~500 words, mark it as a link
    word_count = len(ai_response.split()) if ai_response else 0
    is_link = word_count > 500
    link_id = f"link_{datetime.utcnow().timestamp()}" if is_link else None
    
    return PurificationResult(
        user_content=data.get("user_content", cleaned_text),
        ai_response_summary=ai_response[:100] if ai_response else None,
        ai_response_full=ai_response,
        ai_response_type=determine_response_type(ai_response) if ai_response else "none",
        importance_score=importance_score,
        keywords=data.get("keywords", []),
        topic_id=data.get("topic_id", "general"),
        summary=data.get("summary", ""),
        expires_at=calculate_expiry(importance_score),
        is_link=is_link,
        link_id=link_id
    )
