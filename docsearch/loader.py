"""文書ローダ + チャンカ. 社内文書(契約書/議事録)を段落チャンクに分解."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List


def infer_doc_type(title: str, text: str) -> str:
    """タイトル/本文から文書種別を推定(構造化フィルタ用のメタデータ)."""
    blob = title + "\n" + text[:200]
    if "議事録" in blob:
        return "議事録"
    if "契約" in blob or "規程" in blob or "規約" in blob:
        return "契約書"
    return "その他"


@dataclass(frozen=True)
class Doc:
    doc_id: str
    title: str
    text: str
    doc_type: str = "その他"


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    doc_id: str
    title: str
    text: str
    doc_type: str = "その他"


def chunk_text(doc: Doc, max_chars: int = 200) -> List[Chunk]:
    """空行区切りの段落 -> max_chars 目安でチャンク化."""
    paras = [p.strip() for p in doc.text.split("\n\n") if p.strip()]
    chunks: List[Chunk] = []
    buf = ""
    idx = 0
    for p in paras:
        if buf and len(buf) + len(p) > max_chars:
            chunks.append(Chunk(f"{doc.doc_id}#{idx}", doc.doc_id, doc.title, buf.strip(), doc.doc_type))
            idx += 1
            buf = p
        else:
            buf = (buf + "\n" + p).strip()
    if buf:
        chunks.append(Chunk(f"{doc.doc_id}#{idx}", doc.doc_id, doc.title, buf.strip(), doc.doc_type))
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
        docs.append(Doc(doc_id=os.path.splitext(name)[0], title=title, text=text,
                        doc_type=infer_doc_type(title, text)))
    return docs
