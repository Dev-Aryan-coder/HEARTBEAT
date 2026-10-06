import json
from dataclasses import dataclass, field
from typing import List, Optional
from llm.client import call_heart_l2
from llm.prompts import HEART_L2_CLASSIFY_PROMPT
from heart.ambiguity_detector import detect as detect_ambiguity
from heart.topic_shift_detector import detect_shift
from heart.intent_splitter import split_intents

@dataclass
class ValveResult:
    intent_type: str  # fact/command/temporary/noise/small_talk
    is_permanent: bool
    is_ambiguous: bool
    clarification_question: Optional[str] = None
    ambiguous_word: Optional[str] = None
    is_topic_shift: bool = False
    topic_similarity: float = 1.0
    topic_embedding: List[float] = field(default_factory=list)
    splits: List[str] = field(default_factory=list)

async def classify_intent(text: str) -> dict:
    """Calls Gemma 27B to classify the intent of the text."""
    prompt = HEART_L2_CLASSIFY_PROMPT + f"\nUSER MESSAGE: {text}\n"
    try:
        response = await call_heart_l2(prompt)
        return json.loads(response)
    except Exception:
        # Fallback if classification fails
        return {"intent_type": "permanent_fact", "is_permanent": True, "confidence": 0.5}

async def valve(cleaned_text: str, context_messages: List[str] = [], previous_topic_embedding: Optional[List[float]] = None) -> ValveResult:
    """Main Level 2 orchestrator."""
    # 1. Classify Intent
    intent_data = await classify_intent(cleaned_text)
    intent_type = intent_data.get("intent_type", "noise")
    is_permanent = intent_data.get("is_permanent", False)
    
    # If noise or small talk, return early
    if intent_type in ["noise", "small_talk"]:
        return ValveResult(intent_type=intent_type, is_permanent=False, is_ambiguous=False)
    
    # 2. Check Ambiguity
    amb_result = detect_ambiguity(cleaned_text, context_messages)
    
    # 3. Check Topic Shift
    shift_result = detect_shift(cleaned_text, previous_topic_embedding)
    
    # 4. Check Splits
    splits = split_intents(cleaned_text)
    
    return ValveResult(
        intent_type=intent_type,
        is_permanent=is_permanent,
        is_ambiguous=amb_result["is_ambiguous"],
        clarification_question=amb_result["question"],
        ambiguous_word=amb_result["ambiguous_word"],
        is_topic_shift=shift_result["is_shift"],
        topic_similarity=shift_result["similarity"],
        topic_embedding=shift_result["embedding"],
        splits=splits
    )
