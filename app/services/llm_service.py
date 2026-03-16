from app.core.config import settings
from openai import OpenAI

client = OpenAI(api_key=settings.OPENAI_API_KEY)

async def ask_llm(prompt: str):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )

    return response.choices[0].message.content