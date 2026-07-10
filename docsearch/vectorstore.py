"""インメモリ ベクトルストア. 埋め込み検索(recall段)を担う."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from .embed import Embedder, cosine
from .loader import Chunk


@dataclass
class ScoredChunk:
    chunk: Chunk
    score: float


class VectorStore:
    def __init__(self, embedder: Embedder) -> None:
        self.embedder = embedder
        self._items: List[Tuple[Chunk, Dict[str, float]]] = []

    def index(self, chunks: List[Chunk]) -> None:
        for c in chunks:
            self._items.append((c, self.embedder.embed(c.title + "\n" + c.text)))

    def search(self, query: str, top_n: int = 10) -> List[ScoredChunk]:
        q = self.embedder.embed(query)
        scored = [ScoredChunk(c, cosine(q, v)) for c, v in self._items]
        scored = [s for s in scored if s.score > 0]
        scored.sort(key=lambda s: s.score, reverse=True)
        return scored[:top_n]
