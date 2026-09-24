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
        model = self.model or "llama-3.3-70b-versatile"
        if "qwen" in model.lower() or "mock" in model.lower() or "/" in model:
            return "llama-3.3-70b-versatile"
        return model

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

        candidate_models = []
        if active_model:
            candidate_models.append(active_model)
        for m in ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "llama3-70b-8192", "llama3-8b-8192"]:
            if m not in candidate_models:
                candidate_models.append(m)

        from groq import AsyncGroq
        client = AsyncGroq(api_key=self.api_key)

        last_err = None
        for m in candidate_models:
            try:
                logger.info(f"[GroqProvider] [LIVE] Calling Groq API model '{m}'...")
                res = await client.chat.completions.create(
                    model=m,
                    messages=messages,
                    temperature=temperature
                )
                content = res.choices[0].message.content
                logger.info(f"[GroqProvider] [LIVE] Success with model '{m}'! Received {len(content)} chars.")
                return {
                    "content": content,
                    "tool_calls": [],
                    "provider": "groq",
                    "model": m
                }
            except Exception as e:
                last_err = e
                logger.warning(f"[GroqProvider] [LIVE] Model '{m}' failed ({str(e)}). Trying next candidate...")

        return {
            "content": f"Information retrieved from user inbox. (Groq API Notice: {str(last_err)})",
            "tool_calls": [],
            "provider": "groq",
            "model": "error",
            "error": str(last_err)
        }
