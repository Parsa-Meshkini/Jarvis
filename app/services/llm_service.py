import os
import asyncio
import json
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def generate_plan(user_input: str, system_prompt: str) -> dict:
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt + "\n\nCRITICAL: Return ONLY valid JSON. No markdown, no code fences, no explanation."
                },
                {
                    "role": "user",
                    "content": f"""USER REQUEST: {user_input}

REMINDER: For booking requests you MUST include ALL 4 steps: search_places, check_calendar, call_business, add_to_calendar.

Return ONLY the JSON object."""
                },
            ],
            max_tokens=1000,
            temperature=0.1,
        )

        text = response.choices[0].message.content.strip()

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