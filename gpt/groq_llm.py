import os
from typing import List, Dict, Optional
from groq import Groq
from groq.types.chat import ChatCompletionMessageParam # Import for message typing
from gpt.config import get_config  # read model/keys/settings centrally [file:9]

class GroqLLM:
    def __init__(self, model: Optional[str] = None): # Explicitly Optional[str]
        cfg = get_config()
        api_key = cfg.groq_api_key  # validated by config [file:9]
        self.client = Groq(api_key=api_key)
        self.model: str = model if model is not None else cfg.llm_model # Ensure self.model is str
        self.temperature = cfg.llm_temperature  # from config [file:9]
        self.max_tokens_default = cfg.llm_max_tokens  # from config [file:9]

    def respond(
        self,
        history: List[Dict[str, str]], # Keep as Dict[str, str] for flexibility
        web_info: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        messages = list(history)

        if web_info and "couldn't find" not in web_info.lower():
            messages = [{
                "role": "system",
                "content": (
                    "Use the provided web context if relevant; "
                    "otherwise rely on general knowledge.\n\n" + web_info
                )
            }] + messages

        # Optional: inject system prompt from config persona if not present
        cfg = get_config()
        if not any(m.get("role") == "system" for m in messages):
            messages = [{"role": "system", "content": cfg.get_system_prompt()}] + messages  # [file:9]

        # Ensure messages conform to ChatCompletionMessageParam type
        # Explicitly convert to ChatCompletionMessageParam to satisfy type checker
        typed_messages: List[ChatCompletionMessageParam] = []
        for m in messages:
            if m["role"] == "user":
                typed_messages.append({"role": "user", "content": m["content"]})
            elif m["role"] == "assistant":
                typed_messages.append({"role": "assistant", "content": m["content"]})
            elif m["role"] == "system":
                typed_messages.append({"role": "system", "content": m["content"]})
            # Add other roles if necessary, e.g., tool

        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=typed_messages,  # Use typed_messages here
                max_tokens=(max_tokens or self.max_tokens_default),
                temperature=self.temperature
            )
            content = resp.choices[0].message.content
            return content.strip() if content is not None else ""  # Handle None case for content
        except Exception as e:
            # Log the error for debugging
            print(f"Error calling Groq API: {e}")
            # Return a user-friendly error message
            return "Sorry, I'm having trouble connecting to the language model. Please check your API key and network connection."
