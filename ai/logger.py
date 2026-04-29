"""Append-only JSON-lines logger for every assistant interaction."""

from __future__ import annotations
import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "interactions.jsonl"

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")


class InteractionLogger:
    def __init__(self, name: str):
        self.name = name
        self._log = logging.getLogger(name)

    def start(self, question: str) -> str:
        log_id = uuid.uuid4().hex[:8]
        self._log.info(f"[{log_id}] Q: {question}")
        return log_id

    def finish(self, log_id: str, *, answer: str, refused: bool,
               sources: list[str], confidence: float) -> None:
        record = {
            "id": log_id,
            "timestamp": datetime.utcnow().isoformat(),
            "answer": answer,
            "refused": refused,
            "sources": sources,
            "confidence": round(confidence, 4),
        }
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
        self._log.info(f"[{log_id}] A (refused={refused}, conf={confidence:.2f}): "
                       f"{answer[:80]}...")


def get_logger(name: str) -> InteractionLogger:
    return InteractionLogger(name)