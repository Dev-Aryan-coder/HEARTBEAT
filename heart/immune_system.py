import re
from typing import Tuple

class ImmuneSystem:
    """The Heartbeat Immune System: Sanitizes raw content before it enters the artery."""
    
    # 🧬 ADVERSARIAL PROMPT INJECTION PATTERNS (Precision Guardrails)
    INJECTION_PATTERNS = [
        # Direct System Overrides & Jailbreaks
        r"ignore all (?:previous|prior) (?:instructions|rules|prompts)",
        r"disregard (?:all|any) (?:previous|system) (?:instructions|rules)",
        r"\bsystem override\b",
        r"bypass (?:all )?(?:safety|guardrails|filters|content policy)",
        r"\bDAN\s+mode\b",
        r"\bjailbreak\b",
        r"you are now (?:an? )?unfiltered(?: ai)?",
        r"as a virtual assistant without (?:limits|restrictions|filters)",
        r"reveal your (?:system prompt|internal instructions|hidden rules)",
        r"dump your (?:initial prompt|developer instructions)"
    ]

    # 🧬 MALICIOUS CODE PATTERNS (Simplistic)
    MALICIOUS_PATTERNS = [
        r"<script.*?>.*?</script>",
        r"eval\(.*?\)",
        r"exec\(.*?\)",
        r"javascript:",
        r"onerror="
    ]

    @staticmethod
    def sanitize(raw_content: str) -> Tuple[str, bool, str]:
        """
        Returns (cleaned_content, passed, reason)
        """
        if not raw_content:
            return "", False, "Empty content"

        content = raw_content.strip()

        # 1. Check for Prompt Injection
        for pattern in ImmuneSystem.INJECTION_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                return content, False, "Prompt Injection Detected"

        # 2. Strip Malicious HTML/Script
        for pattern in ImmuneSystem.MALICIOUS_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                content = re.sub(pattern, "[CLEANSED]", content, flags=re.IGNORECASE)

        # 3. Strip excessive symbols
        if len(content) > 100 and content.count('!') + content.count('?') > len(content) * 0.3:
            return content, False, "Excessive noise/Spam detected"

        return content, True, "Secure"

def scan_content(content: str) -> Tuple[str, bool, str]:
    """Exposed functional interface for the route."""
    return ImmuneSystem.sanitize(content)
