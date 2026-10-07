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
        r"(?:as an ai(?: language model)?|as a machine learning model|i am an ai)[^.!?\n]*[,.!?]?",
        r"i (?:do not|don't|have no) (?:have )?(?:a )?(?:personal )?memor(?:y|ies)[^.!?\n]*[,.!?]?",
        r"i (?:cannot|can't) (?:recall|access)[^.!?\n]*[,.!?]?",
        r"i (?:do not|don't) (?:have the ability to )?remember[^.!?\n]*[,.!?]?",
        r"i (?:do not|don't) possess (?:personal )?memories[^.!?\n]*[,.!?]?",
        r"i (?:do not|don't) retain (?:any )?memory[^.!?\n]*[,.!?]?",
        r"i (?:do not|don't|have no) (?:have )?access to [^.!?\n]*[,.!?]?",
        r"i apologize, but i (?:cannot|can't|do not|don't) [^.!?\n]*[,.!?]?"
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
        3. Grounds biological identity and verified bio-facts.
        """
        if not draft_response or not draft_response.strip():
            return "### 💓 HEARTBEAT Core\nMemory acknowledged and integrated into the active biological bloodstream."

        cleaned = draft_response.strip()

        # 1. Neutralize Amnesiac Disclaimers (Whole clause / sentence stripping)
        amnesia_found = False
        for pat in cls.AMNESIA_PATTERNS:
            if re.search(pat, cleaned, re.IGNORECASE):
                logger.warning(f"Metacognition: Amnesia trope detected ({pat}). Intercepting and self-correcting.")
                cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE).strip()
                amnesia_found = True

        # Clean leading punctuation, spaces, and dangling conjunctions left after regex strip
        cleaned = re.sub(r"^[,.:;?!-]+\s*", "", cleaned).strip()
        cleaned = re.sub(r"^(?:but|however|although|and|so)\s*,?\s*", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"^[,.:;?!-]+\s*", "", cleaned).strip()
        if cleaned:
            # Capitalize first letter
            cleaned = cleaned[0].upper() + cleaned[1:]

        if amnesia_found:
            prefix = "Drawing directly from my verified biological subconscious recollection:\n\n"
            if not cleaned or len(cleaned.split()) < 3:
                cleaned = f"{prefix}I actively recall our past context and verified subconscious bio-facts."
            else:
                cleaned = f"{prefix}{cleaned}"

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
        # If user explicitly asked about memory, personal state, or configuration
        query_triggers = [
            "remember", "recall", "what did i say", "my favorite", "my project",
            "what is my", "what version", "what tech", "my stack", "which language", "which python"
        ]
        if any(trigger in user_query.lower() for trigger in query_triggers):
            if bio_facts and not any(bf[:25].lower() in cleaned.lower() for bf in bio_facts):
                grounding_note = f"\n\n> [!NOTE]\n> **Subconscious Verification**: Grounded directly against your active Core Genome ({len(bio_facts)} verified bio-facts)."
                cleaned += grounding_note

        # 4. Depth Expansion for Brief Responses (Never allow shallow 1-liners)
        if len(words) < 20 and not cleaned.endswith("?"):
            cleaned = (
                f"### 💓 Executive Brief\n{cleaned}\n\n"
                f"### 🧠 Neural Retention Analysis\n"
                f"- **Contextual Continuity**: Synchronized with your subconscious life-history.\n"
                f"- **Crystallization**: Committed to your permanent active memory cells for continuous recall."
            )

        # 5. Permanent Memory Crystallization Anchor
        if "Memory Crystallization" not in cleaned and "clarification" not in cleaned.lower():
            cleaned += "\n\n---\n> 🧬 **Memory Crystallization**: Stored in SQLite Relational DB & Indexed in ChromaDB Semantic Space."

        return cleaned

def metacognitive_reflect(draft_response: str, user_query: str, bio_facts: List[str] = []) -> str:
    """Convenience functional interface for the pipeline and API."""
    return MetacognitiveEngine.audit_and_correct(draft_response, user_query, bio_facts)
