from llm.client import call_brain
from storage.database import get_messages_by_chat
from cells.cell_model import BloodCell

async def get_full_original_answer(cell: BloodCell) -> str:
    """Full Original Level 3 Answer: Fetches raw conversations and reformats using Groq."""
    
    # 1. Fetch raw SQLite messages for context
    raw_msgs = get_messages_by_chat(cell.chat_id)
    
    # 2. Limit the context if too large
    context_str = ""
    for r in raw_msgs[-10:]:
        role = r.get('role', 'user')
        content = r.get('content', '')
        context_str += f"{role.capitalize()}: {content}\n"
    
    # 3. Create the BRAIN prompt
    prompt = f"""The user is asking for full original detail about a past memory.
Based on these raw conversation logs:

{context_str}

Reconstruct the full original information with clear, polished GitHub-Flavored Markdown formatting:
- Use bullet points for key facts or timeline items.
- Bold key names, dates, metrics, and parameters.
- If there are multiple attributes or settings, present them in a clean Markdown table.

Current Cell Summary for context: {cell.summary}
"""
    
    try:
        messages = [{"role": "system", "content": "You are the Heartbeat Brain. Provide structured, accurate, well-formatted markdown responses with headings and bullet points."},
                    {"role": "user", "content": prompt}]
        
        # Call Groq (llama-3.1-8b-instant via HEARTBEAT_BRAIN_KEY)
        response = await call_brain(messages)
        return f"💓 [Level 3: Full Original]\n{response}"
    except Exception as e:
        return f"💓 [Level 3 Error] Fallback to Summary: {cell.summary} (Error: {e})"
