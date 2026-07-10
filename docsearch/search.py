"""検索パイプライン: 埋め込み -> ベクトル検索 -> リランク -> 根拠説明."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .embed import Embedder
from .explain import explain
from .loader import Chunk, Doc, chunk_text
from .reranker import Reranker
from .vectorstore import VectorStore


class SearchEngine:
    def __init__(self, embedder: Embedder = None, reranker: Reranker = None) -> None:
        self.embedder = embedder or Embedder()
        self.reranker = reranker or Reranker()
        self.store: VectorStore = None
        self._chunks: List[Chunk] = []

    def build(self, docs: List[Doc]) -> "SearchEngine":
        self._chunks = []
        for d in docs:
            self._chunks.extend(chunk_text(d))
        self.embedder.fit([c.title + "\n" + c.text for c in self._chunks])
        self.store = VectorStore(self.embedder)
        self.store.index(self._chunks)
        return self

    def search(self, query: str, top_n: int = 10, top_k: int = 5, rerank: bool = True):
        candidates = self.store.search(query, top_n=top_n)
        if not rerank:
            # ベクトルのみ(評価比較用)
            return [{"doc_id": s.chunk.doc_id, "title": s.chunk.title,
                     "score": round(s.score, 4)} for s in candidates[:top_k]]
        reranked = self.reranker.rerank(query, candidates)
        return [explain(query, r) for r in reranked[:top_k]]

    def ranked_doc_ids(self, query: str, top_n: int = 10, top_k: int = 5,
                       rerank: bool = True) -> List[str]:
        results = self.search(query, top_n=top_n, top_k=top_k, rerank=rerank)
        seen, ids = set(), []
        for r in results:
            if r["doc_id"] not in seen:
                seen.add(r["doc_id"])
                ids.append(r["doc_id"])
        return ids
