import os
import httpx
import json
import asyncio
import logging
from typing import Optional, Dict, Any
from heartbeat.config import get_config
from .dna_tag_generator import generate_dna_tag
from .ocr_extractor import extract_text_from_image
from .metadata_reader import get_image_info

logger = logging.getLogger("HEARTBEAT_VISION")

OPENROUTER_VISION_MODEL = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"

async def analyze_image_with_nvidia_vision(image_base64: str, user_prompt: str = "", local_image_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyzes an image/screenshot using a collaborative pipeline:
    1. Local Tesseract OCR extracts raw verbatim characters, logs, code, and error messages.
    2. NVIDIA Nemotron 3 Nano Omni (Vision via OpenRouter) analyzes layout, visual UI, colors, charts, and diagrams.
    3. The two systems reinforce each other for maximum accuracy.
    """
    config = get_config()
    api_key = (
        getattr(config, "openrouter_api_key", None)
        or os.getenv("OPENROUTER_API_KEY", "")
    )
    base_url = getattr(config, "openrouter_base_url", "https://openrouter.ai/api/v1")

    # 1. Run local Tesseract OCR & metadata to help the vision model
    ocr_text = ""
    image_meta = {}
    if local_image_path and os.path.exists(local_image_path):
        try:
            ocr_text = extract_text_from_image(local_image_path)
            if ocr_text:
                logger.info(f"Tesseract OCR extracted {len(ocr_text)} chars from {os.path.basename(local_image_path)}")
        except Exception as ocr_err:
            logger.warning(f"Tesseract OCR warning: {ocr_err}")

        try:
            image_meta = get_image_info(local_image_path) or {}
        except Exception as meta_err:
            logger.warning(f"Image metadata warning: {meta_err}")

    # Format proper Data URI
    if not image_base64.startswith("data:"):
        image_data_uri = f"data:image/png;base64,{image_base64}"
    else:
        image_data_uri = image_base64

    # Build prompt for NVIDIA Vision incorporating Tesseract OCR data as helper context
    user_p = user_prompt.strip() if user_prompt else ""
    prompt_sections = []
    
    if user_p:
        prompt_sections.append(f"User Request: \"{user_p}\"")

    if ocr_text.strip():
        prompt_sections.append(
            f"Pre-extracted Text (via Tesseract OCR from this image):\n\"\"\"\n{ocr_text.strip()[:1500]}\n\"\"\""
        )

    prompt_sections.append(
        "Instructions: Carefully examine the image visually and cross-reference with the OCR text provided above. "
        "Analyze all UI components, buttons, dialogs, code snippets, diagrams, tables, charts, error logs, and colors.\n"
        "Formatting Requirements:\n"
        "- Structure your breakdown using clean GitHub-Flavored Markdown.\n"
        "- Use markdown headings (### ...) to separate distinct areas (e.g. Overview, Key Visual Details, Observations, Recommendations).\n"
        "- Use bullet points (-) or numbered steps for details and takeaways.\n"
        "- Format tabular data, metadata, or key-value fields in a clear Markdown table.\n"
        "- Emphasize key terms, states, numbers, and conclusions in **bold**.\n"
        "- Provide a professional, organized, and complete response without dense text walls."
    )

    instruction = "\n\n".join(prompt_sections)

    payload = {
        "model": OPENROUTER_VISION_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": instruction},
                    {"type": "image_url", "image_url": {"url": image_data_uri}}
                ]
            }
        ],
        "max_tokens": 3000,
        "temperature": 0.2
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "HEARTBEAT/4.0 (Windows NT 10.0; Win64; x64)"
    }

    url = f"{base_url.rstrip('/')}/chat/completions"

    # Try up to 3 attempts with slight backoff
    vision_text = ""
    for attempt in range(1, 4):
        try:
            logger.info(f"OpenRouter NVIDIA Vision attempt {attempt}/3 ({OPENROUTER_VISION_MODEL})...")
            timeout = httpx.Timeout(connect=15.0, read=90.0, write=15.0, pool=10.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    if "error" in data:
                        err_msg = data["error"].get("message", "Unknown provider error")
                        logger.warning(f"Attempt {attempt} returned API error: {err_msg}")
                        if attempt < 3:
                            await asyncio.sleep(1.5)
                            continue
                    else:
                        choices = data.get("choices", [])
                        if choices:
                            msg = choices[0].get("message", {})
                            content = (msg.get("content") or "").strip()
                            reasoning = (msg.get("reasoning") or "").strip()
                            analysis_text = content if content else reasoning
                            if analysis_text:
                                logger.info(f"NVIDIA Vision succeeded on attempt {attempt}.")
                                vision_text = analysis_text
                                break
                else:
                    logger.warning(f"Attempt {attempt} returned HTTP {resp.status_code}: {resp.text[:200]}")
                    if attempt < 3:
                        await asyncio.sleep(1.5)
        except Exception as e:
            logger.error(f"Attempt {attempt} exception: {str(e)}")
            if attempt < 3:
                await asyncio.sleep(1.5)

    # If NVIDIA Vision succeeded, combine with Tesseract OCR
    if vision_text:
        return {
            "success": True,
            "analysis": vision_text,
            "ocr_text": ocr_text.strip(),
            "meta": image_meta,
            "provider": "OpenRouter_NVIDIA_Vision",
            "model": OPENROUTER_VISION_MODEL
        }

    # Fallback to local OCR / DNA Tag Generator if all remote vision calls failed
    fallback_text = ""
    if local_image_path and os.path.exists(local_image_path):
        try:
            logger.info("Using local OCR / DNA tag generator as fallback...")
            fallback_text = generate_dna_tag(local_image_path)
        except Exception as local_err:
            logger.warning(f"Local DNA tag fallback error: {local_err}")

    if not fallback_text:
        fallback_text = ocr_text.strip() if ocr_text.strip() else "Image attached by user."

    return {
        "success": False,
        "analysis": fallback_text,
        "ocr_text": ocr_text.strip(),
        "meta": image_meta,
        "provider": "Local_Tesseract_OCR",
        "model": "tesseract"
    }
