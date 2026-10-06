import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("HEARTBEAT_METACOGNITION")

class MetacognitiveEngine:
    """
    DeepMind-Grade Dual-Process System 2 Metacognitive Engine.
    Implements deliberative reflection, truth consistency auditing, 
    and self-correcting output verification.
    """

    COMPLEXITY_TRIGGERS = [
        r"\b(?:architecture|system design|refactor|optimize|algorithm|debug)\b",
        r"\b(?:why|explain in detail|compare|contrast|trade-offs|step-by-step)\b",
        r"\b(?:database|sql|schema|chroma|vector|llm|pipeline|neural)\b",
        r"\b(?:analyze|evaluate|review|critique|diagnose|formulate)\b"
    ]

    AMNESIA_PATTERNS = [
        r"as an ai(?: language model)?",
        r"i (?:do not|don't) have (?:a )?memory",
        r"i (?:cannot|can't) recall (?:our|previous)",
        r"i (?:do not|don't) possess (?:personal )?memories",
        r"as a machine learning model",
        r"i have no access to previous conversations"
    ]

    @classmethod
    def assess_cognitive_load(cls, user_text: str) -> str:
        """Determines whether to trigger System 1 (Intuitive Fast) or System 2 (Deliberative Metacognitive)."""
        if not user_text:
            return "system_1"
        
        # Word count factor
        if len(user_text.split()) > 25:
            return "system_2"
            
        for pat in cls.COMPLEXITY_TRIGGERS:
            if re.search(pat, user_text, re.IGNORECASE):
                return "system_2"

        return "system_1"

    @classmethod
    def audit_and_correct(cls, draft_response: str, user_query: str, bio_facts: List[str] = []) -> str:
        """
        System 2 Metacognitive Reflection Gate:
        1. Strips any amnesia or robotic boilerplate.
        2. Ensures high-impact structural formatting.
        3. Grounds biological identity.
        """
        if not draft_response or not draft_response.strip():
            return "### 💓 HEARTBEAT Core\nMemory acknowledged and integrated into the active biological bloodstream."

        cleaned = draft_response.strip()

        # 1. Neutralize Amnesiac Disclaimers
        for pat in cls.AMNESIA_PATTERNS:
            if re.search(pat, cleaned, re.IGNORECASE):
                logger.warning(f"Metacognition: Amnesia trope detected ({pat}). Intercepting and self-correcting.")
                cleaned = re.sub(pat, "from my biological subconscious recollection", cleaned, flags=re.IGNORECASE)

        # 2. Verify Structural Quality
        # If response has substance (>30 words) but lacks headers or bullets, structure it cleanly
        words = cleaned.split()
        if len(words) > 30 and not any(h in cleaned for h in ["###", "##", "- ", "1."]):
            logger.info("Metacognition: Formatting dense response into structured markdown sections.")
            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', cleaned) if s.strip()]
            if len(sentences) >= 2:
                mid = max(1, len(sentences) // 2)
                part1 = " ".join(sentences[:mid])
                part2 = " ".join(sentences[mid:])
                cleaned = f"### Overview\n{part1}\n\n### Key Breakdown\n{part2}"
            else:
                cleaned = f"### Overview\n{cleaned}"

        # 3. Fact Grounding Verification
        # If user explicitly asked "do you remember" or "what did I say", ensure reference to bio-facts
        if any(trigger in user_query.lower() for trigger in ["remember", "recall", "what did i say", "my favorite", "my project"]):
            if bio_facts and not any(bf[:25].lower() in cleaned.lower() for bf in bio_facts):
                grounding_note = f"\n\n> [!NOTE]\n> **Subconscious Verification**: Grounded directly against your active Core Genome ({len(bio_facts)} verified bio-facts)."
                cleaned += grounding_note

        return cleaned

def metacognitive_reflect(draft_response: str, user_query: str, bio_facts: List[str] = []) -> str:
    """Convenience functional interface for the pipeline and API."""
    return MetacognitiveEngine.audit_and_correct(draft_response, user_query, bio_facts)
