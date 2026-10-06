import httpx
import json
import logging
import asyncio
from typing import List, Optional, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from heartbeat.config import get_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HEARTBEAT_LLM")

class LLMCallError(Exception):
    """Custom exception for LLM failures."""
    pass

class LLMTransientError(Exception):
    """Exception for errors that should be retried (e.g. 5xx, timeouts)."""
    pass

# ISSUE 3.3 FIX: Granular timeouts for long LLM inference
LLM_TIMEOUT = httpx.Timeout(
    connect=10.0,
    read=120.0,  # Allow 2 minutes for 70B models
    write=10.0,
    pool=10.0
)

# ISSUE 3.2 FIX: Exponential backoff for transient failures
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(LLMTransientError),
    reraise=True
)
async def _do_post(client: httpx.AsyncClient, url: str, headers: dict, payload: dict) -> dict:
    try:
        response = await client.post(url, headers=headers, json=payload)
        
        # ISSUE 3.4 FIX: Handle 429 and 5xx correctly
        if response.status_code == 429:
            logger.warning("Groq Rate Limit (429). Retrying...")
            raise LLMTransientError("Rate limit exceeded")
        elif response.status_code >= 500:
            logger.warning(f"Groq Server Error ({response.status_code}). Retrying...")
            raise LLMTransientError(f"Server error: {response.status_code}")
        
        response.raise_for_status()
        return response.json()
    except (httpx.TimeoutException, httpx.NetworkError) as e:
        logger.warning(f"Network error ({type(e).__name__}). Retrying...")
        raise LLMTransientError(f"Network failure: {str(e)}")
    except httpx.HTTPStatusError as e:
        # Non-transient errors (400, 401, 404)
        raise LLMCallError(f"API Error: {e.response.status_code} - {e.response.text}")

async def call_llm(key_env_name: str, model: str, messages: List[dict], json_mode: bool = False, max_tokens: int = 4096) -> str:
    """Core function to call Groq API — ISSUE 3.1 & 3.5 FIX (Groq Centric)"""
    config = get_config()
    
    # ISSUE 20 FIX: Robust Groq key resolution with dedicated and fallback keys
    api_key = (
        getattr(config, key_env_name.lower(), None)
        or getattr(config, 'groq_api_key', None)
        or getattr(config, 'brain_key', None)
        or getattr(config, 'heart_l3_key', None)
        or getattr(config, 'heart_l2_key', None)
        or getattr(config, 'nervous_key', None)
    )
    if not api_key:
        api_key = (
            os.getenv("HEARTBEAT_BRAIN_KEY")
            or os.getenv("HEARTBEAT_GROQ_KEY")
            or os.getenv("GROQ_API_KEY")
            or os.getenv("HEARTBEAT_HEART_L3_KEY")
        )
    if not api_key:
        raise LLMCallError(f"Groq API Key '{key_env_name}' not found.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "HEARTBEAT/4.0 (Windows NT 10.0; Win64; x64)"
    }

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.5
    }
    
    # ISSUE 3.5 FIX: Groq supports response_format
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    url = f"{config.groq_base_url}/chat/completions"
    
    async with httpx.AsyncClient(timeout=LLM_TIMEOUT) as client:
        try:
            logger.info(f"Calling Groq: {model} (JSON={json_mode})")
            data = await _do_post(client, url, headers, payload)
            content = data["choices"][0]["message"]["content"]
            if not content:
                raise LLMCallError("Empty content received from LLM.")
            return content
        except Exception as e:
            logger.error(f"Failed LLM Call: {str(e)}")
            raise LLMCallError(f"LLM Processing Failed: {str(e)}")

# --- NATIVE GROQ MODELS ---
MODELS = {
    "PURIFIER": "openai/gpt-oss-120b",
    "VALVE": "openai/gpt-oss-20b",
    "BRAIN": "openai/gpt-oss-120b",
    "NERVOUS": "openai/gpt-oss-20b"
}

async def call_heart_l3(prompt: str, json_mode: bool = True) -> str:
    """Purifier: GPT-OSS-120B (High Fidelity)"""
    messages = [{"role": "user", "content": prompt}]
    return await call_llm("heart_l3_key", MODELS["PURIFIER"], messages, json_mode=json_mode, max_tokens=1500)

async def call_heart_l2(prompt: str) -> str:
    """Valve: GPT-OSS-20B (Fast Intent)"""
    messages = [{"role": "user", "content": prompt}]
    return await call_llm("heart_l2_key", MODELS["VALVE"], messages, json_mode=False, max_tokens=500)

async def call_brain(messages: List[dict], max_tokens: int = 4096) -> str:
    """Main Chat Logic: GPT-OSS-120B (Authoritative Subconscious)"""
    return await call_llm("brain_key", MODELS["BRAIN"], messages, json_mode=False, max_tokens=max_tokens)

async def call_nervous(prompt: str) -> str:
    """Dormant Trigger: GPT-OSS-20B (Fast Extraction)"""
    messages = [{"role": "user", "content": prompt}]
    return await call_llm("nervous_key", MODELS["NERVOUS"], messages, json_mode=True)
