"""文脈類似検索 API(FastAPI). 文書投入 -> 検索(ハイブリッド/リランク) -> HTML結果. テナント分離.
`uvicorn service.api:app --reload`
"""
from docsearch import SearchEngine
from .db import ServiceDB
from .report_html import build_html_report

DB = ServiceDB(":memory:")


def _engine(tenant: str) -> SearchEngine:
    docs = DB.get_docs(tenant)
    return SearchEngine().build(docs) if docs else None


def create_app():  # pragma: no cover
    from fastapi import Depends, FastAPI, Header, HTTPException
    from fastapi.responses import HTMLResponse
    from pydantic import BaseModel

    app = FastAPI(title="Context Rerank Search", version="1.0.0")

    def tenant(x_tenant_id: str = Header(...)) -> str:
        if not x_tenant_id:
            raise HTTPException(401, "tenant required")
        return x_tenant_id

    class DocsIn(BaseModel):
        docs: list  # [{doc_id, title, text}]

    class SearchIn(BaseModel):
        query: str
        doc_type: str | None = None
        rerank: bool = True
        top_k: int = 5

    @app.post("/v1/docs")
    def add_docs(body: DocsIn, t: str = Depends(tenant)):
        for d in body.docs:
            DB.add_doc(t, d["doc_id"], d.get("title", d["doc_id"]), d.get("text", ""))
        return {"added": len(body.docs)}

    @app.post("/v1/search")
    def search(body: SearchIn, t: str = Depends(tenant)):
        engine = _engine(t)
        if engine is None:
            raise HTTPException(404, "no documents")
        return {"query": body.query,
                "results": engine.search(body.query, top_k=body.top_k,
                                         rerank=body.rerank, doc_type=body.doc_type)}

    @app.get("/v1/report", response_class=HTMLResponse)
    def report(query: str, t: str = Depends(tenant)):
        engine = _engine(t)
        if engine is None:
            raise HTTPException(404, "no documents")
        return build_html_report(query, engine.search(query, top_k=5))

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    return app


try:  # pragma: no cover
    app = create_app()
except Exception:
    app = None
