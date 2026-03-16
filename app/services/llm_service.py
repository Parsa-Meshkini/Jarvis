# app/services/llm_service.py
import os
import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-1.5-flash"))

# Thread pool for running sync Gemini calls without blocking
_executor = ThreadPoolExecutor(max_workers=4)


def _call_gemini(prompt: str) -> str:
    """Synchronous Gemini call — runs in thread pool."""
    response = model.generate_content(prompt)
    return response.text


async def generate_plan(user_input: str, system_prompt: str) -> dict:
    full_prompt = f"""{system_prompt}

USER REQUEST:
{user_input}

Respond ONLY with valid JSON. No markdown, no explanation, just JSON.
"""

    loop = asyncio.get_event_loop()

    # Run the blocking Gemini call in a separate thread
    text = await loop.run_in_executor(_executor, _call_gemini, full_prompt)
    text = text.strip()

    # Strip markdown fences if Gemini wraps output in ```json ... ```
    if "```" in text:
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end   = text.rfind("}") + 1
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end])
            except Exception:
                pass
        return {"goal": "parse_error", "steps": [], "raw_output": text}