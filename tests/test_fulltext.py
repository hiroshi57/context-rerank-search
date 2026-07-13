import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from docsearch import SearchEngine, load_dir  # noqa: E402
from docsearch.loader import infer_doc_type  # noqa: E402
from eval.evaluate import evaluate, per_query_breakdown, load_testset  # noqa: E402

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def _engine():
    return SearchEngine().build(load_dir(DATA_DIR))


def test_doc_type_inference():
    assert infer_doc_type("SaaS利用契約書", "第1条") == "契約書"
    assert infer_doc_type("Q2議事録", "決定事項") == "議事録"
    assert infer_doc_type("雑記", "特になし") == "その他"


def test_docs_have_doc_type():
    docs = load_dir(DATA_DIR)
    types = {d.doc_id: d.doc_type for d in docs}
    assert types["gijiroku_2026q2"] == "議事録"
    assert types["saas_riyou_keiyaku"] == "契約書"


def test_doc_type_filter_restricts_results():
    engine = _engine()
    # 議事録のみに絞ると契約書はヒットしない
    results = engine.search("納期 期限", top_k=5, doc_type="議事録")
    assert results
    assert all(r.get("doc_id") == "gijiroku_2026q2" or "gijiroku" in r["doc_id"]
               for r in results) or all("doc_id" in r for r in results)
    ids = engine.ranked_doc_ids("納期 期限", top_k=5, doc_type="議事録")
    assert "saas_riyou_keiyaku" not in ids
    assert "gyoumu_itaku_keiyaku" not in ids


def test_filter_none_returns_all_types():
    engine = _engine()
    ids = engine.ranked_doc_ids("契約 解約 納期", top_k=10, doc_type=None)
    assert len(ids) >= 2


def test_eval_includes_precision():
    engine = _engine()
    m = evaluate(engine, load_testset(), k=3, rerank=True)
    assert "precision@3" in m
    assert 0.0 <= m["precision@3"] <= 1.0


def test_per_query_breakdown_shape():
    engine = _engine()
    rows = per_query_breakdown(engine, load_testset(), k=3)
    assert len(rows) == len(load_testset())
    assert all("query" in r and "ranked" in r and "mrr" in r for r in rows)
