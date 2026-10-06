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

import re

def extract_and_parse_json(text: str) -> dict:
    """Robust extractor that handles raw JSON, markdown code blocks, and partial LLM outputs."""
    if not text or not text.strip():
        raise ValueError("Empty response text")

    cleaned = text.strip()
    # Strip markdown code blocks
    if "```" in cleaned:
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()

    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # Find outermost curly braces
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = cleaned[start:end+1]
        try:
            return json.loads(candidate)
        except Exception:
            pass

    # Regex key extraction
    extracted = {}
    score_match = re.search(r'"importance_score"\s*:\s*(\d+)', cleaned)
    if score_match:
        extracted["importance_score"] = int(score_match.group(1))
    topic_match = re.search(r'"topic_id"\s*:\s*"([^"]+)"', cleaned)
    if topic_match:
        extracted["topic_id"] = topic_match.group(1)
    summary_match = re.search(r'"summary"\s*:\s*"([^"]+)"', cleaned)
    if summary_match:
        extracted["summary"] = summary_match.group(1)
    user_content_match = re.search(r'"user_content"\s*:\s*"([^"]+)"', cleaned)
    if user_content_match:
        extracted["user_content"] = user_content_match.group(1)

    if extracted:
        return extracted

    raise ValueError("No extractable JSON in LLM text")

async def purify(cleaned_text: str, ai_response: Optional[str] = None) -> PurificationResult:
    """Calls High-Fidelity LLM to extract structured user and AI data with bulletproof fallback."""
    prompt = build_heart_l3_prompt(cleaned_text, ai_response)
    
    try:
        response_text = await call_heart_l3(prompt)
        data = extract_and_parse_json(response_text)
    except Exception as je:
        import logging
        logging.warning(f"[L3 Purifier] Extractor handled non-standard format: {je}. Using resilient fallback.")
        # Auto-extract meaningful topic slug from text
        words = [w.lower() for w in re.findall(r'\b[a-zA-Z]{4,}\b', cleaned_text)]
        auto_topic = words[0] if words else "general"
        data = {
            "user_content": cleaned_text,
            "importance_score": 6,
            "keywords": words[:4] if words else ["subconscious", "memory"],
            "topic_id": f"pref_{auto_topic}",
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
