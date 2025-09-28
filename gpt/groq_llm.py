import os
from typing import List, Dict, Optional
from groq import Groq

class GroqLLM:

    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Missing GROQ_API_KEY in environment")
        self.client = Groq(api_key=api_key)
        self.model = model

    def respond(
        self,
        history: List[Dict[str, str]],
        web_info: Optional[str] = None,
        max_tokens: int = 500
    ) -> str:
        messages = list(history)
        # ✅ Prepend web info if available
        if web_info and "couldn't find" not in web_info.lower():
            messages = [{
                "role": "system",
                "content": (
                    "Use the provided web context if relevant; "
                    "otherwise rely on general knowledge.\n\n" + web_info
                )
            }] + messages
        # ✅ Only one messages=messages here
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.7
        )
        return resp.choices[0].message.content.strip()
