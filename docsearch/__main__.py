"""CLI: コーパスを検索。 `python -m docsearch --query "契約 解約" [--doc-type 契約書]`"""
from __future__ import annotations

import argparse
import json
import os

from .loader import load_dir
from .search import SearchEngine

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="docsearch", description="文脈類似ドキュメント検索")
    ap.add_argument("--query", required=True)
    ap.add_argument("--data", default=DATA_DIR)
    ap.add_argument("--top-k", type=int, default=3)
    ap.add_argument("--doc-type", default=None, help="契約書 / 議事録 で構造化フィルタ")
    ap.add_argument("--no-rerank", action="store_true")
    args = ap.parse_args(argv)

    engine = SearchEngine().build(load_dir(args.data))
    results = engine.search(args.query, top_k=args.top_k,
                            rerank=not args.no_rerank, doc_type=args.doc_type)
    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
