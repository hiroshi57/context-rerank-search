import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402

from service.db import ServiceDB  # noqa: E402
from service.report_html import build_html_report  # noqa: E402

DOCS = [
    {"doc_id": "saas", "title": "SaaS利用契約書", "text": "第4条 利用者は30日前の通知で解約できる。"},
    {"doc_id": "nda", "title": "秘密保持契約書", "text": "秘密情報を第三者に開示してはならない。"},
]


def test_docs_roundtrip_and_doc_type_inferred():
    db = ServiceDB(":memory:")
    for d in DOCS:
        db.add_doc("t-a", d["doc_id"], d["title"], d["text"])
    docs = db.get_docs("t-a")
    assert len(docs) == 2
    assert {d.doc_type for d in docs} == {"契約書"}


def test_tenant_isolation():
    db = ServiceDB(":memory:")
    db.add_doc("t-a", "saas", "SaaS利用契約書", "解約条項")
    assert db.get_docs("t-b") == []


def test_html_report():
    results = [{"doc_id": "saas", "rerank_score": 0.3,
                "reasons": ["同義概念で一致: 解約"], "snippet": "…30日前の通知で解約…"}]
    html = build_html_report("契約 キャンセル", results)
    assert "文脈類似検索 結果" in html and "saas" in html and "解約" in html


def test_html_report_escapes():
    html = build_html_report("<script>", [])
    assert "<script>" not in html and "&lt;script&gt;" in html


def test_api_e2e_and_tenant_isolation():
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient
    from service.api import create_app
    c = TestClient(create_app())
    ha, hb = {"X-Tenant-Id": "t-a"}, {"X-Tenant-Id": "t-b"}
    assert c.post("/v1/docs", json={"docs": DOCS}, headers=ha).json()["added"] == 2
    # tenant-b は文書なし
    assert c.post("/v1/search", json={"query": "解約"}, headers=hb).status_code == 404
    res = c.post("/v1/search", json={"query": "契約をキャンセルしたい"}, headers=ha).json()
    assert res["results"]
    r = c.get("/v1/report?query=解約", headers=ha)
    assert r.status_code == 200 and "文脈類似検索 結果" in r.text
