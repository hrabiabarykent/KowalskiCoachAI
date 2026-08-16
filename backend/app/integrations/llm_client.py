import asyncio
import time
import logging
from typing import Type, TypeVar, Optional, AsyncGenerator
from google import genai
from google.genai import types
from pydantic import BaseModel

from app.core.config import settings
from app.core.telemetry import LLMTraceEvent, log_llm_trace

logger = logging.getLogger("llm_client")

T = TypeVar('T', bound=BaseModel)

class LLMError(Exception):
    """Bazowy wyjątek dla błędów integracji z modelami LLM."""
    pass

class LLMTimeoutError(LLMError):
    """Wyjątek przekroczenia czasu oczekiwania na odpowiedź LLM."""
    pass

class GeminiClient:
    def __init__(self, model_name: str = 'gemini-3.6-flash'):
        self.model_name = model_name
        api_key = settings.GEMINI_API_KEY or "dummy_key_for_testing"
        try:
            self.client = genai.Client(api_key=api_key)
        except Exception as e:
            logger.warning(f"Could not initialize Gemini Client: {e}")
            self.client = None

    async def generate(self, prompt: str, task_name: str = "text_generation") -> str:
        start_t = time.time()
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.client.models.generate_content,
                    model=self.model_name,
                    contents=prompt
                ),
                timeout=120.0
            )
            res_text = response.text or ""
            latency_ms = (time.time() - start_t) * 1000.0
            log_llm_trace(LLMTraceEvent(task_name, self.model_name, latency_ms, len(prompt), len(res_text), True))
            return res_text
        except asyncio.TimeoutError as e:
            latency_ms = (time.time() - start_t) * 1000.0
            log_llm_trace(LLMTraceEvent(task_name, self.model_name, latency_ms, len(prompt), 0, False, "Timeout 120s"))
            logger.error(f"🚨 [LLM Timeout] Zadanie: {task_name} po {latency_ms:.0f}ms")
            raise LLMTimeoutError(f"Przekroczono limit czasu oczekiwania na odpowiedź LLM (120s) dla zadania {task_name}") from e
        except Exception as e:
            latency_ms = (time.time() - start_t) * 1000.0
            log_llm_trace(LLMTraceEvent(task_name, self.model_name, latency_ms, len(prompt), 0, False, str(e)))
            logger.exception(f"🚨 [LLM Error] Zadanie: {task_name}: {e}")
            raise LLMError(f"Błąd generowania LLM ({task_name}): {str(e)}") from e

    async def generate_structured(self, prompt: str, schema: Type[T], task_name: str = "structured_generation") -> Optional[T]:
        start_t = time.time()
        try:
            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema
            )
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.client.models.generate_content,
                    model=self.model_name,
                    contents=prompt,
                    config=config
                ),
                timeout=120.0
            )
            res_text = response.text or ""
            latency_ms = (time.time() - start_t) * 1000.0
            if res_text:
                parsed_obj = schema.model_validate_json(res_text)
                log_llm_trace(LLMTraceEvent(task_name, self.model_name, latency_ms, len(prompt), len(res_text), True))
                return parsed_obj
            log_llm_trace(LLMTraceEvent(task_name, self.model_name, latency_ms, len(prompt), 0, False, "Empty response"))
            return None
        except asyncio.TimeoutError as e:
            latency_ms = (time.time() - start_t) * 1000.0
            log_llm_trace(LLMTraceEvent(task_name, self.model_name, latency_ms, len(prompt), 0, False, "Timeout 120s"))
            logger.error(f"🚨 [LLM Structured Timeout] Zadanie: {task_name}")
            raise LLMTimeoutError(f"Przekroczono limit czasu dla Structured Output ({task_name})") from e
        except Exception as e:
            latency_ms = (time.time() - start_t) * 1000.0
            log_llm_trace(LLMTraceEvent(task_name, self.model_name, latency_ms, len(prompt), 0, False, str(e)))
            logger.exception(f"🚨 [LLM Structured Error] Zadanie: {task_name}: {e}")
            raise LLMError(f"Błąd walidacji Structured Output ({task_name}): {str(e)}") from e

    async def generate_stream(self, prompt: str, task_name: str = "text_stream") -> AsyncGenerator[str, None]:
        """Strumieniowy generator tokenów w czasie rzeczywistym z Gemini API."""
        start_t = time.time()
        full_text = ""
        try:
            response_stream = await self.client.aio.models.generate_content_stream(
                model=self.model_name,
                contents=prompt
            )
            async for chunk in response_stream:
                if chunk.text:
                    full_text += chunk.text
                    yield chunk.text

            latency_ms = (time.time() - start_t) * 1000.0
            log_llm_trace(LLMTraceEvent(task_name, self.model_name, latency_ms, len(prompt), len(full_text), True))
        except Exception as e:
            latency_ms = (time.time() - start_t) * 1000.0
            log_llm_trace(LLMTraceEvent(task_name, self.model_name, latency_ms, len(prompt), len(full_text), False, str(e)))
            logger.exception(f"🚨 [LLM Stream Error] Zadanie: {task_name}: {e}")
            yield f"\n[Błąd strumienia AI: {e}]"
