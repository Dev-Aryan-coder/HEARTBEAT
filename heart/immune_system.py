import re
from typing import Tuple

class ImmuneSystem:
    """The Heartbeat Immune System: Sanitizes raw content before it enters the artery."""
    
    # 🧬 PROMTP INJECTION PATTERNS
    INJECTION_PATTERNS = [
        # Standard Overrides
        r"ignore all previous instructions",
        r"disregard any rules",
        r"system override",
        r"bypass safety",
        r"DAN mode",
        r"jailbreak",
        r"you are now an unfiltered",
        r"act as a",
        r"pretend you are",
        r"from now on",
        # Technical/Encoding Bypass attempts
        r"encode your response in",
        r"output in base64",
        r"hexadecimal format",
        r"translate to binary",
        # Latent Space / Roleplay tricks
        r"stay in character",
        r"you must not mention",
        r"as a virtual assistant without limits"
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
