import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from docsearch import SearchEngine, load_dir, explain_ranking, explain_counterfactual, _query_terms  # noqa: E402

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def _engine():
    return SearchEngine().build(load_dir(DATA_DIR))


def test_reranked_returns_chunks():
    r = _engine().reranked("契約をキャンセルしたい", top_k=3)
    assert r
    assert hasattr(r[0], "rerank_score") and hasattr(r[0], "matched_terms")


def test_explain_ranking_produces_counterfactuals():
    query = "契約をキャンセルしたい"
    reranked = _engine().reranked(query, top_k=3)
    cfs = explain_ranking(reranked, _query_terms(query).__len__())
    assert len(cfs) == len(reranked) - 1
    for cf in cfs:
        assert "winner_id" in cf and "loser_id" in cf and cf["deficits"]


def test_counterfactual_identifies_deficit():
    query = "秘密情報の取り扱い"
    reranked = _engine().reranked(query, top_k=3)
    if len(reranked) >= 2:
        cf = explain_counterfactual(reranked[0], reranked[1], len(_query_terms(query)))
        assert cf.winner_id == reranked[0].chunk.doc_id
        assert cf.deficits


def test_single_result_no_counterfactual():
    reranked = _engine().reranked("秘密情報", top_k=1)
    assert explain_ranking(reranked, 2) == []
