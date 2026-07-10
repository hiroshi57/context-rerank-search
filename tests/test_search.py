import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from docsearch import SearchEngine, Embedder, cosine, load_dir  # noqa: E402
from eval.evaluate import run as run_eval, load_testset  # noqa: E402

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def _engine():
    return SearchEngine().build(load_dir(DATA_DIR))


def test_synonym_beyond_keyword():
    # 「キャンセル」で検索しても、本文が「解約/中途解約」の契約書がヒットする
    engine = _engine()
    ids = engine.ranked_doc_ids("契約をキャンセルしたい", top_k=3)
    assert "saas_riyou_keiyaku" in ids or "gyoumu_itaku_keiyaku" in ids


def test_embedding_cosine_bounds():
    emb = Embedder().fit(["秘密情報の管理", "納期の調整", "利用料金の請求"])
    v1 = emb.embed("秘密情報")
    v2 = emb.embed("秘密情報")
    v3 = emb.embed("納期")
    assert abs(cosine(v1, v2) - 1.0) < 1e-6      # 同一文は cos≈1
    assert cosine(v1, v3) < cosine(v1, v2)       # 別概念はより低い


def test_search_returns_explanations():
    engine = _engine()
    results = engine.search("秘密情報の取り扱い", top_k=3)
    assert results
    assert "reasons" in results[0]
    assert "snippet" in results[0]
    assert results[0]["doc_id"] == "nda"


def test_rerank_improves_over_vector_only():
    result = run_eval()
    vo = result["vector_only"]
    wr = result["with_rerank"]
    # リランクは各指標でベクトルのみを下回らない(非劣化)
    assert wr["nDCG@3"] >= vo["nDCG@3"]
    assert wr["MRR"] >= vo["MRR"]
    assert wr["recall@3"] >= vo["recall@3"]
    # かつ、少なくとも MRR/nDCG は厳密に改善する
    # (distractor により vector-only が top1 を誤るケースをリランクが是正)
    assert wr["MRR"] > vo["MRR"]
    assert wr["nDCG@3"] > vo["nDCG@3"]


def test_all_relevant_found_in_top3():
    engine = _engine()
    for case in load_testset():
        ids = engine.ranked_doc_ids(case["query"], top_k=3)
        assert any(r in ids for r in case["relevant"]), case["query"]


def test_metrics_within_bounds():
    result = run_eval()
    for pipeline in result.values():
        for metric, val in pipeline.items():
            assert 0.0 <= val <= 1.0, (metric, val)
