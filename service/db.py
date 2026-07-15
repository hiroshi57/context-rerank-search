"""永続化層(SQLite, 標準ライブラリ). 文書コーパス保存. テナント分離."""
from __future__ import annotations

import sqlite3
from typing import List

from docsearch.loader import Doc, infer_doc_type

SCHEMA = """
CREATE TABLE IF NOT EXISTS docs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id TEXT NOT NULL,
    doc_id TEXT NOT NULL,
    title TEXT NOT NULL,
    text TEXT NOT NULL,
    doc_type TEXT NOT NULL
);
"""


class ServiceDB:
    def __init__(self, path: str = ":memory:") -> None:
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def add_doc(self, tenant_id: str, doc_id: str, title: str, text: str) -> None:
        self.conn.execute(
            "INSERT INTO docs(tenant_id, doc_id, title, text, doc_type) VALUES (?,?,?,?,?)",
            (tenant_id, doc_id, title, text, infer_doc_type(title, text)))
        self.conn.commit()

    def get_docs(self, tenant_id: str) -> List[Doc]:
        rows = self.conn.execute(
            "SELECT doc_id, title, text, doc_type FROM docs WHERE tenant_id=?", (tenant_id,)).fetchall()
        return [Doc(doc_id=r["doc_id"], title=r["title"], text=r["text"], doc_type=r["doc_type"])
                for r in rows]

    def close(self) -> None:
        self.conn.close()
