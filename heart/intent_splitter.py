import nltk
import logging
from nltk.tokenize import word_tokenize, sent_tokenize
from heart.nltk_utils import ensure_nltk_data

# Configure logging
logger = logging.getLogger("HEARTBEAT_INTENT_SPLITTER")

def count_distinct_verbs(text: str) -> int:
    """Counts distinct action verbs in the text using NLTK."""
    try:
        words = word_tokenize(text)
        tagged = nltk.pos_tag(words)
        # NTLK tags for verbs: VB, VBD, VBG, VBN, VBP, VBZ
        verbs = [word for word, tag in tagged if tag.startswith('VB')]
        return len(set(verbs))
    except Exception as e:
        logger.error(f"Verb counting failure: {str(e)}")
        return 1 # Fallback to 1 intent

def split_intents(text: str) -> list:
    """Main function for multi-intent splitting using NLTK."""
    ensure_nltk_data()
    
    # 1. Simple heuristic: If multiple sentences, might be multiple intents.
    sentences = sent_tokenize(text)
    
    # 2. Refined splitting by 'and' or 'also' if verbs follow
    splits = []
    for s in sentences:
        # Split by conjunctions
        parts = [p.strip() for p in s.split(' and ') if p.strip()]
        for p in parts:
            if count_distinct_verbs(p) >= 1:
                splits.append(p)
            else:
                # If no verb, likely just extra info
                if splits: splits[-1] += f" and {p}"
                else: splits.append(p)
                
    return splits if splits else [text]
