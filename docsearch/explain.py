"""根拠説明生成(差別化). なぜこの文書がヒットしたかを人間可読で返す."""
from __future__ import annotations

from typing import Dict

from .embed import SYNONYM_GROUPS
from .reranker import RerankedChunk

_CONCEPT_LABEL = {
    "cancel": "解約・キャンセル", "deadline": "納期・期限", "fee": "料金・費用",
    "confidential": "秘密保持", "renew": "更新・継続", "inspect": "検収",
}


def _snippet(text: str, terms, width: int = 60) -> str:
    for t in terms:
        i = text.find(t)
        if i >= 0:
            start = max(0, i - width // 2)
            return ("…" if start > 0 else "") + text[start:start + width].replace("\n", " ") + "…"
    return text[:width].replace("\n", " ") + "…"


def explain(query: str, r: RerankedChunk) -> Dict:
    reasons = []
    if r.matched_terms:
        reasons.append(f"クエリ語に一致: {', '.join(r.matched_terms)}")
    if r.matched_concepts:
        labels = [_CONCEPT_LABEL.get(c, c) for c in r.matched_concepts]
        reasons.append(f"同義概念で一致(キーワード不一致でも該当): {', '.join(labels)}")
    if not reasons:
        reasons.append("文脈ベクトルの類似のみで一致")
    return {
        "doc_id": r.chunk.doc_id,
        "title": r.chunk.title,
        "rerank_score": round(r.rerank_score, 4),
        "vector_score": round(r.vector_score, 4),
        "reasons": reasons,
        "snippet": _snippet(r.chunk.text, r.matched_terms or [query]),
    }
