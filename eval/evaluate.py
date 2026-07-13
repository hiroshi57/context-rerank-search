"""検索精度評価(標準同梱の差別化). recall@k / MRR / nDCG を、
ベクトルのみ vs ベクトル+リランク で比較する。
"""
from __future__ import annotations

import json
import math
import os
import sys
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from docsearch import SearchEngine, load_dir  # noqa: E402

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
TESTSET = os.path.join(os.path.dirname(os.path.abspath(__file__)), "testset.jsonl")


def load_testset(path: str = TESTSET) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _recall_at_k(ranked: List[str], relevant: List[str], k: int) -> float:
    topk = ranked[:k]
    hit = sum(1 for r in relevant if r in topk)
    return hit / len(relevant) if relevant else 0.0


def _mrr(ranked: List[str], relevant: List[str]) -> float:
    for i, doc in enumerate(ranked, start=1):
        if doc in relevant:
            return 1.0 / i
    return 0.0


def _ndcg_at_k(ranked: List[str], relevant: List[str], k: int) -> float:
    dcg = sum((1.0 / math.log2(i + 1)) for i, doc in enumerate(ranked[:k], start=1) if doc in relevant)
    ideal = sum((1.0 / math.log2(i + 1)) for i in range(1, min(len(relevant), k) + 1))
    return dcg / ideal if ideal else 0.0


def _precision_at_k(ranked: List[str], relevant: List[str], k: int) -> float:
    topk = ranked[:k]
    if not topk:
        return 0.0
    return sum(1 for d in topk if d in relevant) / len(topk)


def evaluate(engine: SearchEngine, testset: List[Dict], k: int = 3, rerank: bool = True) -> Dict:
    recalls, precs, mrrs, ndcgs = [], [], [], []
    for case in testset:
        ranked = engine.ranked_doc_ids(case["query"], top_n=10, top_k=k, rerank=rerank)
        recalls.append(_recall_at_k(ranked, case["relevant"], k))
        precs.append(_precision_at_k(ranked, case["relevant"], k))
        mrrs.append(_mrr(ranked, case["relevant"]))
        ndcgs.append(_ndcg_at_k(ranked, case["relevant"], k))
    n = len(testset) or 1
    return {
        f"recall@{k}": round(sum(recalls) / n, 4),
        f"precision@{k}": round(sum(precs) / n, 4),
        "MRR": round(sum(mrrs) / n, 4),
        f"nDCG@{k}": round(sum(ndcgs) / n, 4),
    }


def per_query_breakdown(engine: SearchEngine, testset: List[Dict], k: int = 3,
                        rerank: bool = True) -> List[Dict]:
    """クエリ別の内訳(どのクエリでリランクが効いたか可視化)."""
    rows = []
    for case in testset:
        ranked = engine.ranked_doc_ids(case["query"], top_n=10, top_k=k, rerank=rerank)
        rows.append({"query": case["query"], "ranked": ranked,
                     "mrr": round(_mrr(ranked, case["relevant"]), 3),
                     "recall": round(_recall_at_k(ranked, case["relevant"], k), 3)})
    return rows


def run() -> Dict:
    engine = SearchEngine().build(load_dir(DATA_DIR))
    testset = load_testset()
    return {
        "vector_only": evaluate(engine, testset, k=3, rerank=False),
        "with_rerank": evaluate(engine, testset, k=3, rerank=True),
    }


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    vo, wr = result["vector_only"]["nDCG@3"], result["with_rerank"]["nDCG@3"]
    print(f"\nnDCG@3: vector_only={vo} -> with_rerank={wr} "
          f"({'改善' if wr >= vo else '悪化'} {wr - vo:+.4f})")
