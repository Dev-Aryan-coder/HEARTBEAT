from typing import Tuple

# Ordered list of key environment names for prioritization
KEY_PRIORITY = [
    "HEART_L3_KEY",
    "HEART_L2_KEY",
    "BRAIN_KEY",
    "NERVOUS_KEY",
    "FALLBACK_KEY"
]

def get_fallback_model() -> Tuple[str, str]:
    """Returns the fallback key environment name and the auto-model identifier."""
    return ("FALLBACK_KEY", "openrouter/auto")

def is_rate_limited(status_code: int) -> bool:
    """Checks if the response indicates a rate limit (429)."""
    return status_code == 429
