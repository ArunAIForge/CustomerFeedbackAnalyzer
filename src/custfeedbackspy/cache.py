"""Tiny on-disk cache so re-analysing the same review with the same model is instant and free."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .prompts import PROMPT_VERSION
from .schemas import ReviewAnalysis

CACHE_FILE = Path(__file__).resolve().parents[2] / ".cache" / "analysis_cache.json"


class AnalysisCache:
    def __init__(self, namespace: str, path: Path = CACHE_FILE):
        self.ns, self.path, self.dirty = f"{namespace}|{PROMPT_VERSION}", path, False
        try:
            self.data: dict = json.loads(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 - missing or corrupt cache just means a cold start
            self.data = {}

    def key(self, inp: dict) -> str:
        raw = f"{self.ns}|{inp['rating']}|{inp['review_text']}"  # platform does not change the analysis
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()

    def get(self, inp: dict) -> ReviewAnalysis | None:
        hit = self.data.get(self.key(inp))
        try:
            return ReviewAnalysis.model_validate(hit) if hit else None
        except Exception:  # noqa: BLE001
            return None

    def put(self, inp: dict, result: ReviewAnalysis) -> None:
        self.data[self.key(inp)] = result.model_dump()
        self.dirty = True

    def save(self) -> None:
        if not self.dirty:
            return
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self.data, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass  # cache is an optimisation only
