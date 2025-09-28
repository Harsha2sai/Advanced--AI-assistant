from groq_llm import GroqLLM

class ChatEngine:

    def __init__(self):
        self.llm = GroqLLM()
        self.chat_history = []

    def ask(self, query: str) -> dict:
        # Save user query
        self.chat_history.append({"role": "user", "content": query})

        # Get LLM response
        response = self.llm.respond(self.chat_history)
        self.chat_history.append({"role": "assistant", "content": response})

        # Split into short + extra
        lines = response.split("\n", 1)
        short_answer = lines[0].strip()
        extra_info = lines[1].strip() if len(lines) > 1 else ""

        return {
            "short": short_answer,
            "extra": extra_info,
            "history": self.chat_history
        }

    def get_history(self):
        return self.chat_history

    def reset(self):
        self.chat_history = []
