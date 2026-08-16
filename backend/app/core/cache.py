from datetime import datetime, timedelta
from typing import Dict, Any, Optional

INTERVALS_CACHE: Dict[int, Dict[str, Any]] = {}
CACHE_TTL = timedelta(hours=3)

def get_cached_intervals(user_id: int) -> Optional[Dict[str, Any]]:
    entry = INTERVALS_CACHE.get(user_id)
    if not entry:
        return None
    if datetime.now() - entry["timestamp"] > CACHE_TTL:
        INTERVALS_CACHE.pop(user_id, None)
        return None
    return entry["data"]

def set_cached_intervals(user_id: int, data: Dict[str, Any]):
    INTERVALS_CACHE[user_id] = {
        "timestamp": datetime.now(),
        "data": data
    }
