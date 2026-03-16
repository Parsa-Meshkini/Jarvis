import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash-lite")

async def generate_plan(system_prompt: str, user_input: str):

    full_prompt = f"""
    {system_prompt}

    USER REQUEST:
    {user_input}

    Respond ONLY with valid JSON.
    """

    response = model.generate_content(full_prompt)

    text = response.text

    try:
        return json.loads(text)
    except:
        start = text.find("{")
        end = text.rfind("}") + 1
        return json.loads(text[start:end])