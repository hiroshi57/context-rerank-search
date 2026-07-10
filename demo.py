"""デモ(APIキー不要). `python demo.py`"""
import json
import os

from docsearch import SearchEngine, load_dir
from eval.evaluate import run as run_eval

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def main():
    engine = SearchEngine().build(load_dir(DATA_DIR))

    print("=== 文脈類似検索(キーワード不一致でもヒット) ===")
    q = "契約を途中でキャンセルしたい"  # 文書側は「解約」「中途解約」
    print(f"クエリ: {q}\n")
    for r in engine.search(q, top_k=3):
        print(f"[{r['rerank_score']:.3f}] {r['doc_id']} — {r['title']}")
        for reason in r["reasons"]:
            print(f"    根拠: {reason}")
        print(f"    抜粋: {r['snippet']}")
    print("\n=== 精度評価(vector-only vs +rerank) ===")
    print(json.dumps(run_eval(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
