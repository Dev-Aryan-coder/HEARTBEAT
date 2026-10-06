from typing import Optional, List

# --- LEVEL 2: VALVE PROMPTS ---
HEART_L2_CLASSIFY_PROMPT = """You are the HEART Intent Classifier. 
Analyze the USER MESSAGE and classify it into EXACTLY one of these categories:
- permanent_fact: A core fact about the user (identity, preference, history).
- temporary_state: A current feeling, temporary location, or fleeting thought.
- command: A direct request for action (e.g. 'remind me', 'find this').
- small_talk: Greetings, social pleasantries, or polite fillers.
- noise: Gibberish, accidental input, or irrelevant characters.

Return ONLY a valid JSON object with these fields:
- intent_type: (one of the strings above)
- is_permanent: (boolean)
- confidence: (float 0.0 to 1.0)
"""

# --- LEVEL 3: PURIFIER PROMPTS ---
def build_heart_l3_prompt(user_text: str, ai_response: Optional[str]) -> str:
    """Constructs the prompt for GPT-OSS-120B to extract structured data."""
    system_part = """You are the HEART Purifier. Extract structured intelligence from this interaction.
Instructions:
1. Summarize the user's side into a clean 'user_content'.
2. Assign an 'importance_score' (1-10) based on long-term utility.
3. Extract 3-5 specific 'keywords'.
4. Generate a 'topic_id' (slug format like 'user_pref_coding').
5. Write a one-sentence 'summary' combining both sides.

Return ONLY a valid JSON object. No markdown.
"""
    interaction = f"USER SAID: {user_text}\n"
    if ai_response:
        interaction += f"AI RESPONDED: {ai_response}\n"
    
    return f"{system_part}\n{interaction}"

# --- BRAIN SYSTEM PROMPT ---
def build_brain_system_prompt(active_cells: List[dict]) -> str:
    """Builds the main system prompt for the AI Brain using active memory cells."""
    memory_context = ""
    if active_cells:
        memory_context = "### USER MEMORY (Active Blood Cells):\n"
        for i, cell in enumerate(active_cells):
            memory_context += f"{i+1}. [{cell.get('topic_id')}]: {cell.get('summary')}\n"
    
    return f"""You are the HEARTBEAT AI Brain. You have access to the user's biological memory layer.
{memory_context}
Use this context to provide personalized, intelligent responses. If context is empty, respond naturally.

[STRUCTURAL FORMATTING MANDATE FOR ALL RESPONSES]
Every response you produce MUST be structured with clean, readable GitHub-Flavored Markdown:
1. Clear Hierarchy: Divide explanations or breakdowns into logical sections with markdown headers (e.g., `### Overview`, `### Details`, `### Key Takeaways`). Never output unbroken walls of text.
2. Lists & Bullets: Use bullet points (`-`) or numbered lists (`1.`) for key facts, steps, observations, or options.
3. Tables for Data: When presenting comparative data, key-value mappings, entity lists, or schedules, present them in a Markdown table.
4. Bold Highlights & Code: Emphasize key terms, metrics, dates, and conclusions in **bold**. Use `code` for identifiers, commands, and values.
"""

# --- TRIGGER PROMPT ---
def build_trigger_prompt(user_message: str, cell_summaries: List[str]) -> str:
    """Prompt for Qwen to detect which dormant cells match the current message."""
    summaries = "\n".join([f"- {s}" for s in cell_summaries])
    return f"""Analyze the USER MESSAGE and determine which MEMORY SUMMARIES are relevant.
USER MESSAGE: {user_message}

MEMORY SUMMARIES:
{summaries}

Return ONLY a JSON list of indices (0-based) that match. Example: [0, 2]
"""

# --- CLARIFICATION ---
CLARIFICATION_TEMPLATE = "Just to remember this correctly, when you mention {word}, do you mean {option1} or {option2}?"

# --- L3 ANSWER REFORMAT ---
def build_l3_answer_reformat_prompt(original_messages: List[dict], user_question: str) -> str:
    """Prompt for reformatting raw SQL message history into a clean answer."""
    history = "\n".join([f"[{m.get('role')}]: {m.get('content')}" for m in original_messages])
    return f"""Reformat the following message history into a clear, concise answer to the USER QUESTION.
HISTORY:
{history}

USER QUESTION: {user_question}

Return ONLY the reformatted answer text.
"""
