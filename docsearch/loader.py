"""文書ローダ + チャンカ. 社内文書(契約書/議事録)を段落チャンクに分解."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Doc:
    doc_id: str
    title: str
    text: str


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    doc_id: str
    title: str
    text: str


def chunk_text(doc: Doc, max_chars: int = 200) -> List[Chunk]:
    """空行区切りの段落 -> max_chars 目安でチャンク化."""
    paras = [p.strip() for p in doc.text.split("\n\n") if p.strip()]
    chunks: List[Chunk] = []
    buf = ""
    idx = 0
    for p in paras:
        if buf and len(buf) + len(p) > max_chars:
            chunks.append(Chunk(f"{doc.doc_id}#{idx}", doc.doc_id, doc.title, buf.strip()))
            idx += 1
            buf = p
        else:
            buf = (buf + "\n" + p).strip()
    if buf:
        chunks.append(Chunk(f"{doc.doc_id}#{idx}", doc.doc_id, doc.title, buf.strip()))
    return chunks


def load_dir(data_dir: str) -> List[Doc]:
    docs: List[Doc] = []
    for name in sorted(os.listdir(data_dir)):
        if not name.lower().endswith(".md"):
            continue
        path = os.path.join(data_dir, name)
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        title = text.splitlines()[0].lstrip("# ").strip() if text else name
        docs.append(Doc(doc_id=os.path.splitext(name)[0], title=title, text=text))
    return docs
