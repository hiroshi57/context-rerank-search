"""検索 API(FastAPI). `uvicorn api.search_api:app --reload`"""
from __future__ import annotations

import os

from docsearch import SearchEngine, load_dir

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
ENGINE = SearchEngine().build(load_dir(DATA_DIR))


def create_app():  # pragma: no cover
    from fastapi import FastAPI
    from pydantic import BaseModel

    app = FastAPI(title="context-rerank-search", version="0.1.0")

    class Query(BaseModel):
        query: str
        top_k: int = 5
        rerank: bool = True

    @app.post("/search")
    def search(q: Query):
        return {"query": q.query, "results": ENGINE.search(q.query, top_k=q.top_k, rerank=q.rerank)}

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    return app


try:  # pragma: no cover
    app = create_app()
except Exception:
    app = None
