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

    def search(self, query: str, top_n: int = 10, top_k: int = 5, rerank: bool = True,
               doc_type: str = None):
        # 構造化フィルタ(メタデータ)を掛ける場合は広めに取得してから絞る = ハイブリッド検索
        fetch = top_n if doc_type is None else max(top_n, len(self._chunks))
        candidates = self.store.search(query, top_n=fetch)
        if doc_type is not None:
            candidates = [c for c in candidates if c.chunk.doc_type == doc_type][:top_n]
        if not rerank:
            # ベクトルのみ(評価比較用)
            return [{"doc_id": s.chunk.doc_id, "title": s.chunk.title, "doc_type": s.chunk.doc_type,
                     "score": round(s.score, 4)} for s in candidates[:top_k]]
        reranked = self.reranker.rerank(query, candidates)
        return [explain(query, r) for r in reranked[:top_k]]

    def reranked(self, query: str, top_n: int = 10, top_k: int = 5):
        """リランク済みチャンク(RerankedChunk)を返す(反実仮想説明などの入力用)."""
        candidates = self.store.search(query, top_n=top_n)
        return self.reranker.rerank(query, candidates)[:top_k]

    def ranked_doc_ids(self, query: str, top_n: int = 10, top_k: int = 5,
                       rerank: bool = True, doc_type: str = None) -> List[str]:
        results = self.search(query, top_n=top_n, top_k=top_k, rerank=rerank, doc_type=doc_type)
        seen, ids = set(), []
        for r in results:
            if r["doc_id"] not in seen:
                seen.add(r["doc_id"])
                ids.append(r["doc_id"])
        return ids
