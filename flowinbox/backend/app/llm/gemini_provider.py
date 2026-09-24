from typing import List, Dict, Any, Optional
import asyncio
import logging
from app.llm.base import LLMProvider
from app.core.config import settings

logger = logging.getLogger("flowinbox.llm.gemini")


class GeminiProvider(LLMProvider):
    """Secondary LLM provider using Google Gemini API as fallback."""

    def __init__(self):
        self.model = settings.GEMINI_MODEL
        self.api_key = settings.GEMINI_API_KEY
        self.is_mock = self.api_key.startswith("mock") or not self.api_key
        mode_str = "MOCK" if self.is_mock else "LIVE"
        logger.info(f"[GeminiProvider] Initialized in {mode_str} mode (model: {self.model})")

    def _get_active_model(self) -> str:
        model = self.model or "gemini-1.5-flash"
        if "2.5" in model:
            return "gemini-1.5-flash"
        return model

    def _call_gemini_sync(self, contents: str) -> Dict[str, Any]:
        from google import genai
        client = genai.Client(api_key=self.api_key)

        candidate_models = []
        if self.model:
            candidate_models.append(self.model)
            if self.model.startswith("models/"):
                candidate_models.append(self.model.replace("models/", ""))
        for m in ["gemini-2.0-flash", "gemini-1.5-flash-latest", "gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro"]:
            if m not in candidate_models:
                candidate_models.append(m)

        last_err = None
        for active_model in candidate_models:
            try:
                res = client.models.generate_content(
                    model=active_model,
                    contents=contents
                )
                content = res.text or ""
                usage = getattr(res, "usage_metadata", None)
                prompt_tokens = getattr(usage, "prompt_token_count", 0) if usage else 0
                completion_tokens = getattr(usage, "candidates_token_count", 0) if usage else 0
                logger.info(f"[GeminiProvider] [LIVE] Success with model '{active_model}'! Received {len(content)} chars.")
                return {
                    "content": content,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens
                }
            except Exception as err:
                last_err = err
                logger.warning(f"[GeminiProvider] Model '{active_model}' failed ({str(err)}). Trying next candidate...")

        raise RuntimeError(f"Gemini API call failed across candidates: {str(last_err)}")

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        last_user_msg = messages[-1]["content"] if messages else ""

        if self.is_mock:
            await asyncio.sleep(0.05)
            logger.info(f"[GeminiProvider] [MOCK] Generating canned response.")
            return {
                "content": f"Gemini mock response for: {last_user_msg}",
                "tool_calls": [],
                "provider": "gemini",
                "model": self.model
            }

        logger.info(f"[GeminiProvider] [LIVE] Calling Gemini API non-blockingly...")
        try:
            res_data = await asyncio.to_thread(self._call_gemini_sync, last_user_msg)
            return {
                "content": res_data["content"],
                "tool_calls": [],
                "provider": "gemini",
                "model": res_data.get("active_model", self.model),
                "usage": {"prompt_tokens": res_data.get("prompt_tokens", 0), "completion_tokens": res_data.get("completion_tokens", 0)}
            }
        except Exception as e:
            logger.error(f"[GeminiProvider] [LIVE] Error calling Gemini API: {str(e)}")
            return {
                "content": f"Information retrieved from user inbox. (LLM Provider Notice: {str(e)})",
                "tool_calls": [],
                "provider": "gemini",
                "model": "error",
                "error": str(e)
            }
