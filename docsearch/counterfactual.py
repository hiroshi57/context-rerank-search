"""反実仮想説明(尖った武器). 「なぜこの文書が選ばれ、他が選ばれなかったか」を説明する.

上位文書と下位文書のリランク因子(ベクトル類似/語被覆/完全一致/同義概念)を差分比較し、
"何が足りずに負けたか"を人間可読で示す(説明責任のある検索)。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .reranker import RerankedChunk

_FACTOR_LABEL = {
    "vector": "文脈ベクトル類似", "coverage": "クエリ語の被覆",
    "phrase": "完全一致フレーズ", "concept": "同義概念の一致",
}


def _factors(r: RerankedChunk, query_terms: int) -> Dict[str, float]:
    return {
        "vector": round(r.vector_score, 3),
        "coverage": round(len(r.matched_terms) / query_terms, 3) if query_terms else 0.0,
        "phrase": 1.0 if any(len(t) >= 3 for t in r.matched_terms) else 0.0,
        "concept": round(len(r.matched_concepts), 3),
    }


@dataclass
class Counterfactual:
    winner_id: str
    loser_id: str
    deficits: List[str]       # loser が winner に劣る因子の説明

    def as_dict(self):
        return {"winner_id": self.winner_id, "loser_id": self.loser_id, "deficits": self.deficits}


def explain_counterfactual(winner: RerankedChunk, loser: RerankedChunk,
                           query_terms: int) -> Counterfactual:
    """loser が winner に負けた理由(不足因子)を説明する."""
    wf = _factors(winner, query_terms)
    lf = _factors(loser, query_terms)
    deficits: List[str] = []
    for key in ("vector", "coverage", "phrase", "concept"):
        if lf[key] < wf[key]:
            label = _FACTOR_LABEL[key]
            deficits.append(f"{label}が不足({loser.chunk.doc_id}={lf[key]} < {winner.chunk.doc_id}={wf[key]})")
    if not deficits:
        deficits.append("僅差(総合スコアの微差で決定)")
    return Counterfactual(winner_id=winner.chunk.doc_id, loser_id=loser.chunk.doc_id,
                          deficits=deficits)


def explain_ranking(reranked: List[RerankedChunk], query_terms: int) -> List[Dict]:
    """1位に対して2位以降がなぜ負けたかを一括説明する."""
    if len(reranked) < 2:
        return []
    winner = reranked[0]
    return [explain_counterfactual(winner, loser, query_terms).as_dict()
            for loser in reranked[1:]]
