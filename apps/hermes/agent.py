"""
Hermes-Agent Execution Loop
"""
import os
import httpx
from .prompts import HERMES_SYSTEM_PROMPT, format_chatml_prompt
from .tools import get_system_health, calculate_natal_chart, send_whatsapp_otp

BIFROST_URL = os.getenv("HERMES_MODEL_ENDPOINT", "http://bifrost:8080/v1")
MODEL_NAME = os.getenv("HERMES_MODEL_NAME", "hermes-3-llama-3.1-8b")
BIFROST_KEY = os.getenv("BIFROST_VIRTUAL_KEY", "vk-hermes-agent")

class HermesAgent:
    def __init__(self, system_prompt: str = HERMES_SYSTEM_PROMPT):
        self.system_prompt = system_prompt
        self.history: list[dict[str, str]] = []

    async def run_turn(self, user_query: str) -> str:
        prompt = format_chatml_prompt(self.system_prompt, self.history, user_query)
        
        async with httpx.AsyncClient(timeout=45.0) as client:
            try:
                res = await client.post(
                    f"{BIFROST_URL}/chat/completions",
                    headers={"Authorization": f"Bearer {BIFROST_KEY}"},
                    json={
                        "model": MODEL_NAME,
                        "messages": [
                            {"role": "system", "content": self.system_prompt},
                            *self.history,
                            {"role": "user", "content": user_query}
                        ],
                        "temperature": 0.7,
                    }
                )
                if res.status_code == 200:
                    data = res.json()
                    content = data["choices"][0]["message"]["content"]
                    self.history.append({"role": "user", "content": user_query})
                    self.history.append({"role": "assistant", "content": content})
                    return content
                else:
                    return f"[Hermes] Error from AI Gateway: {res.status_code}"
            except Exception as e:
                return f"[Hermes] Gateway unreachable ({str(e)}). Running in fallback mode."
