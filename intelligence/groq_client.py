import os

import httpx
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


class GroqClient:
    def __init__(self):
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not set in .env")
        self.headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }

    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        payload = {
            "model": GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.3,
        }
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(GROQ_API_URL, headers=self.headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
