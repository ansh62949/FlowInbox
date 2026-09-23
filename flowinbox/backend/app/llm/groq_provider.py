from typing import List, Dict, Any, Optional
import asyncio
import logging
from app.llm.base import LLMProvider
from app.core.config import settings

logger = logging.getLogger("flowinbox.llm.groq")


class GroqProvider(LLMProvider):
    """Primary LLM provider using Groq API."""

    def __init__(self):
        self.model = settings.GROQ_MODEL
        self.api_key = settings.GROQ_API_KEY
        self.is_mock = self.api_key.startswith("mock") or not self.api_key
        mode_str = "MOCK" if self.is_mock else "LIVE"
        logger.info(f"[GroqProvider] Initialized in {mode_str} mode (model: {self.model})")

    def _get_active_model(self) -> str:
        return self.model or "llama-3.3-70b-versatile"

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        last_user_msg = messages[-1]["content"] if messages else ""
        active_model = self._get_active_model()

        if self.is_mock:
            await asyncio.sleep(0.05)
            logger.info(f"[GroqProvider] [MOCK] Generating canned response.")
            return {
                "content": f"Groq mock response for: {last_user_msg}",
                "tool_calls": [],
                "provider": "groq",
                "model": active_model
            }

        logger.info(f"[GroqProvider] [LIVE] Calling Groq API model '{active_model}'...")
        try:
            from groq import AsyncGroq
            client = AsyncGroq(api_key=self.api_key)
            res = await client.chat.completions.create(
                model=active_model,
                messages=messages,
                temperature=temperature
            )
            content = res.choices[0].message.content
            logger.info(f"[GroqProvider] [LIVE] Success! Received {len(content)} chars.")
            return {
                "content": content,
                "tool_calls": [],
                "provider": "groq",
                "model": self.model
            }
        except Exception as e:
            logger.error(f"[GroqProvider] [LIVE] Error calling Groq API: {str(e)}")
            raise RuntimeError(f"Groq API call failed: {str(e)}")
