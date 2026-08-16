import time
import json
import logging
import os
from typing import Optional, Dict, Any

logger = logging.getLogger("kowalski_telemetry")
logger.setLevel(logging.INFO)

class LLMTraceEvent:
    def __init__(
        self,
        task_name: str,
        model_name: str,
        latency_ms: float,
        prompt_length: int,
        response_length: int,
        success: bool,
        error: Optional[str] = None
    ):
        self.task_name = task_name
        self.model_name = model_name
        self.latency_ms = round(latency_ms, 2)
        self.prompt_length = prompt_length
        self.response_length = response_length
        self.success = success
        self.error = error
        self.timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "task_name": self.task_name,
            "model_name": self.model_name,
            "latency_ms": self.latency_ms,
            "prompt_length": self.prompt_length,
            "response_length": self.response_length,
            "success": self.success,
            "error": self.error
        }

def log_llm_trace(event: LLMTraceEvent):
    """Rejestruje ślad wywołania LLM w ustrukturyzowanych logach oraz w pliku logs/llm_traces.jsonl."""
    trace_dict = event.to_dict()
    logger.info(f"LLM Trace: {event.task_name} | Model: {event.model_name} | Czas: {event.latency_ms}ms | Sukces: {event.success}")

    try:
        os.makedirs("logs", exist_ok=True)
        with open(os.path.join("logs", "llm_traces.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps(trace_dict, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.warning(f"Błąd zapisu telemetrii: {e}")
