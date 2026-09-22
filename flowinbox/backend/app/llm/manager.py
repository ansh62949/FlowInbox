import hashlib
import json
from typing import List, Dict, Any, Optional
import logging
from app.core.config import settings
from app.llm.base import LLMProvider
from app.llm.groq_provider import GroqProvider
from app.llm.gemini_provider import GeminiProvider

logger = logging.getLogger("flowinbox.llm.manager")


import asyncio

class LLMManager:
    """Manages primary provider execution with retry/backoff, automatic fallback, and bounded response cache."""

    MAX_CACHE_SIZE = 500

    def __init__(self):
        self.primary_provider = GroqProvider() if settings.LLM_PROVIDER == "groq" else GeminiProvider()
        self.fallback_provider = GeminiProvider() if settings.LLM_PROVIDER == "groq" else GroqProvider()
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _hash_request(self, messages: List[Dict[str, str]], temperature: float) -> str:
        raw_str = json.dumps({"messages": messages, "temp": temperature}, sort_keys=True)
        return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

    def _set_cache(self, req_hash: str, res: Dict[str, Any]):
        if len(self._cache) >= self.MAX_CACHE_SIZE:
            # Evict first (oldest inserted) key
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        self._cache[req_hash] = res

    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        req_hash = self._hash_request(messages, temperature)
        if req_hash in self._cache:
            logger.info(f"[LLMManager] Cache HIT for request hash '{req_hash[:8]}'")
            cached = dict(self._cache[req_hash])
            cached["cached"] = True
            return cached

        # Retry primary provider up to 2 times with backoff on transient errors
        for attempt in range(2):
            try:
                logger.info(f"[LLMManager] Executing primary LLM provider: {settings.LLM_PROVIDER} (attempt {attempt+1})")
                res = await self.primary_provider.generate_response(messages, temperature, tools)
                self._set_cache(req_hash, res)
                return res
            except Exception as e:
                err_str = str(e).lower()
                # If error is non-retryable auth/bad-request, break early to fallback
                if "auth" in err_str or "unauthorized" in err_str or "invalid" in err_str:
                    logger.warning(f"[LLMManager] Non-retryable error on primary provider: {e}")
                    break
                if attempt < 1:
                    await asyncio.sleep(0.5 * (2 ** attempt))

        logger.warning(f"[LLMManager] Primary provider '{settings.LLM_PROVIDER}' failed after retries. Triggering fallback to '{settings.LLM_FALLBACK_PROVIDER}'.")
        res = await self.fallback_provider.generate_response(messages, temperature, tools)
        self._set_cache(req_hash, res)
        return res

