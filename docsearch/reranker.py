"""リランカ(precision段). 埋め込み候補をクロス特徴で再スコアする.

埋め込み類似だけでは拾えない「完全一致フレーズ」「クエリ語の被覆」「近接」を
加味して並べ替える。cross-encoder の軽量代替。
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

from .embed import SYNONYM_GROUPS, _SURFACE_TO_GROUP
from .vectorstore import ScoredChunk

_TERM_RE = re.compile(r"[a-zA-Z0-9]+|[぀-ヿ一-鿿々〆ぁ-んァ-ヶ]{2,}")


def _query_terms(query: str) -> List[str]:
    return [t for t in _TERM_RE.findall(query) if len(t) >= 2]


@dataclass
class RerankedChunk:
    chunk: "object"
    vector_score: float
    rerank_score: float
    matched_terms: List[str]
    matched_concepts: List[str]


def _concepts(text: str) -> set:
    return {gid for surface, gid in _SURFACE_TO_GROUP.items() if surface in text}


class Reranker:
    def __init__(self, w_vec=0.5, w_coverage=0.3, w_phrase=0.1, w_concept=0.1) -> None:
        self.w_vec = w_vec
        self.w_coverage = w_coverage
        self.w_phrase = w_phrase
        self.w_concept = w_concept

    def rerank(self, query: str, candidates: List[ScoredChunk]) -> List[RerankedChunk]:
        terms = _query_terms(query)
        q_concepts = _concepts(query)
        out: List[RerankedChunk] = []
        for cand in candidates:
            body = cand.chunk.title + "\n" + cand.chunk.text
            matched = [t for t in terms if t in body]
            coverage = len(matched) / len(terms) if terms else 0.0
            phrase_bonus = 1.0 if any(len(t) >= 3 and t in body for t in terms) else 0.0
            c_matched = q_concepts & _concepts(body)
            concept_score = len(c_matched) / len(q_concepts) if q_concepts else 0.0
            score = (
                self.w_vec * cand.score
                + self.w_coverage * coverage
                + self.w_phrase * phrase_bonus
                + self.w_concept * concept_score
            )
            out.append(RerankedChunk(
                chunk=cand.chunk, vector_score=cand.score, rerank_score=score,
                matched_terms=matched, matched_concepts=sorted(c_matched),
            ))
        out.sort(key=lambda r: r.rerank_score, reverse=True)
        return out
