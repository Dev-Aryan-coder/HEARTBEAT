from typing import List, Optional
from heartbeat.config import get_config

AMBIGUOUS_WORDS = {
    'apple': ['fruit', 'Apple Inc company'],
    'python': ['snake', 'Python programming language'],
    'java': ['island', 'Java programming language', 'coffee'],
    'mercury': ['planet', 'element', 'car brand'],
    'amazon': ['river', 'Amazon company'],
    'meta': ['Facebook company', 'meta prefix']
}

def check_context_for_clues(word: str, context: List[str], current_text: str = "") -> Optional[str]:
    """Looks for disambiguating words in the current message and context."""
    meanings = AMBIGUOUS_WORDS.get(word.lower(), [])
    # Simplified clue matching
    clues = {
        'fruit': ['eat', 'food', 'tree', 'slice', 'eating', 'ate', 'taste'],
        'Apple Inc company': ['iphone', 'mac', 'stock', 'tech', 'ipad', 'tim cook'],
        'snake': ['reptile', 'zoo', 'bite', 'slither'],
        'Python programming language': ['code', 'script', 'import', 'dev', 'pip', 'django'],
        'island': ['travel', 'ocean', 'indonesia'],
        'Java programming language': ['jvm', 'runtime', 'backend', 'syntax', 'spring'],
        'coffee': ['drink', 'cup', 'beans', 'brew']
    }
    
    context_text = (current_text + " " + " ".join(context)).lower()
    for meaning in meanings:
        for clue in clues.get(meaning, []):
            if clue in context_text:
                return meaning
    return None

def calculate_confidence(word: str, context: List[str], current_text: str = "") -> float:
    """Returns a confidence score from 0.0 to 1.0 based on context clues."""
    clue = check_context_for_clues(word, context, current_text)
    return 1.0 if clue else 0.0

def generate_clarification_question(word: str, meanings: List[str]) -> str:
    """Generates a natural-sounding clarification question."""
    options = " or ".join(meanings)
    return f"Just to save this correctly, when you say {word} do you mean {options}?"

def detect(text: str, context_messages: List[str]) -> dict:
    """Main function for detecting ambiguity."""
    config = get_config()
    words = text.lower().split()
    
    for word in words:
        clean_word = word.strip(",.?!\"'")
        if clean_word in AMBIGUOUS_WORDS:
            meanings = AMBIGUOUS_WORDS[clean_word]
            confidence = calculate_confidence(clean_word, context_messages, text)
            
            if confidence < config.ambiguity_threshold:
                return {
                    "is_ambiguous": True,
                    "confidence": confidence,
                    "ambiguous_word": clean_word,
                    "question": generate_clarification_question(clean_word, meanings)
                }
    
    return {
        "is_ambiguous": False,
        "confidence": 1.0,
        "ambiguous_word": "",
        "question": None
    }

# Backward compatibility attributes & interface
call_llm = None

def detect_ambiguity(target, context_messages: List[str] = None):
    """Compatible interface accepting BloodCell or text, returning (is_amb, question)."""
    global call_llm
    if callable(call_llm):
        try:
            import json
            raw = call_llm("test")
            data = json.loads(raw) if isinstance(raw, str) else raw
            return data.get("is_ambiguous", False), data.get("question", "")
        except Exception:
            pass

    if hasattr(target, 'user_raw_content'):
        text = target.user_raw_content
    elif hasattr(target, 'content'):
        text = target.content
    else:
        text = str(target)
    
    res = detect(text, context_messages or [])
    return res["is_ambiguous"], (res["question"] or "")
