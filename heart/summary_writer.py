def write_summary(user_content: str, ai_response_summary: str, topic_id: str) -> str:
    """Combines user fact and AI summary into one sentence."""
    user_fact = user_content.strip()
    ai_fact = ai_response_summary.strip()
    
    # Format: [user fact] ù [AI answer summary]
    summary = f"{user_fact} ù {ai_fact}"
    return truncate_summary(summary)

def truncate_summary(summary: str, max_chars: int = 200) -> str:
    """Ensures summary fits within the maximum character limit."""
    if len(summary) <= max_chars:
        return summary
    return summary[:max_chars-3] + "..."
