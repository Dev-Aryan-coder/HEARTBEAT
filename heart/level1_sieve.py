import nltk
import logging
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from heart.nltk_utils import ensure_nltk_data

# Configure logging
logger = logging.getLogger("HEARTBEAT_L1_SIEVE")

def extract_meaningful_sentences(content: str) -> list:
    """Uses NLTK to extract sentences that contain nouns or verbs."""
    try:
        ensure_nltk_data()
        sentences = sent_tokenize(content)
        meaningful = []
        
        for s in sentences:
            words = word_tokenize(s)
            # Remove stopwords
            sw = set(stopwords.words('english'))
            words_filtered = [w for w in words if w.lower() not in sw]
            
            # POS Tagging
            tagged = nltk.pos_tag(words_filtered)
            
            # Heuristic: Must have at least one noun (NN) or verb (VB)
            if any(t.startswith('NN') or t.startswith('VB') for _, t in tagged):
                meaningful.append(s)
                
        return meaningful if meaningful else [content]
    except Exception as e:
        logger.error(f"L1 Meaningful Sentence Extraction Error: {str(e)}")
        return [content]

def process_l1(content: str) -> dict:
    """Main entry for L1 Sieve using NLTK."""
    # 1. Strip whitespace
    raw = content.strip()
    
    # 1.1 Filter common conversational greetings and noise
    if raw.lower() in ["hi", "hello", "hey", "sup", "yo", "ok", "okay", "cool", "bye", "thanks", "thx"]:
        return {"passed": False, "cleaned": raw, "removed": "Greeting / short noise detected"}
    
    # 2. Extract meaningful bits
    cleaned_sentences = extract_meaningful_sentences(raw)
    cleaned_text = " ".join(cleaned_sentences)
    
    # 3. Simple redundancy check
    if len(cleaned_text) < len(raw) * 0.3:
        # If we stripped >70%, user likely sent noise
        return {"passed": False, "cleaned": raw, "removed": "Too much noise detected"}
    
    return {
        "passed": True,
        "cleaned": cleaned_text,
        "removed": None
    }

# Backward compatibility alias
sieve = process_l1
