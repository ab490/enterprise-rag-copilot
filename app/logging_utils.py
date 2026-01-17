import json
import os
import time
from typing import Any, Dict
from .config import settings

def ensure_dirs():
    os.makedirs(settings.log_dir, exist_ok=True)

def log_event(event: Dict[str, Any], filename: str = "events.jsonl") -> None:
    ensure_dirs()
    path = os.path.join(settings.log_dir, filename)
    event = {**event, "ts": time.time()}
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
