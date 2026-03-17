import os
import asyncio
import json
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def generate_plan(user_input: str, system_prompt: str) -> dict:
    full_prompt = f"""{system_prompt}

USER REQUEST:
{user_input}

Respond ONLY with valid JSON. No markdown, no explanation, just JSON.
"""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a JSON-only response bot. Never use markdown. Always respond with valid JSON."},
                {"role": "user",   "content": full_prompt},
            ],
            max_tokens=1000,
            temperature=0.3,
        )

        text = response.choices[0].message.content.strip()

        # Strip markdown fences if present
        if "```" in text:
            lines = text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            text  = "\n".join(lines).strip()

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

    except Exception as exc:
        error_str = str(exc)
        if "429" in error_str or "quota" in error_str.lower():
            return {"goal": "rate_limit_error", "steps": [], "error": "Rate limit hit — try again in a moment"}
        return {"goal": "llm_error", "steps": [], "error": error_str}