# context-rerank-search

社内文書（契約書・議事録等）を対象に、キーワードでは拾えない **"文脈類似"** の高度ドキュメント検索を
RAG 構成（**埋め込み → ベクトル検索 → リランキング**）で実装した最小版。

## 差別化ポイント

1. **根拠説明生成** — 各ヒットに「なぜ一致したか」（一致したクエリ語／同義概念／抜粋）を付与。
   ブラックボックスな類似度スコアだけでなく、人間が検索結果を検証できる。
2. **精度 eval を標準同梱** — `eval/testset.jsonl`（クエリ×正解文書）と `evaluate.py` により
   **recall@k / MRR / nDCG** を計測し、**ベクトルのみ vs +リランク**を常時比較できる。
3. **キーワード非依存** — 類義語グループ展開（例: 解約＝解除＝キャンセル、納期＝納入期限）を
   埋め込みに組み込み、語が一致しなくても同義文書をヒットさせる。

すべて **API キー・ネットワーク不要**（ローカル埋め込み）で動作。本番は `Embedder` を
外部埋め込みAPIに差し替えるだけでパイプラインは不変。

## パイプライン

```
クエリ ──embed──▶ ベクトル検索(recall, top_n) ──rerank(precision)──▶ 根拠説明付き top_k
                                                 └ cross特徴: 語被覆/完全一致/同義概念
```

## 全機能

- 埋め込み→検索→リランキング（差別化コア）＋ **根拠説明** ＋ **eval同梱**
- **メタデータ構造化フィルタ**（`doc_type`: 契約書/議事録）= 真のハイブリッド検索
- **eval拡張**: recall@k / **precision@k** / MRR / nDCG ＋ **クエリ別内訳**
- **CLI**（`python -m docsearch`）/ 検索API（FastAPI）

## クイックスタート

```bash
python demo.py                 # 文脈類似検索 + 根拠説明 + 精度評価
python -m docsearch --query "契約 解約" --doc-type 契約書   # CLI(構造化フィルタ)
python -m eval.evaluate        # vector-only vs +rerank の指標比較
python -m pytest -q            # テスト16件相当(外部依存なし)
uvicorn api.search_api:app --reload   # 検索API
```

## 構成

```
docsearch/
  embed.py        # ローカル埋め込み(文字n-gram TFIDF + 類義語展開)
  loader.py       # 文書ロード + チャンク化
  vectorstore.py  # ベクトル検索(recall段)
  reranker.py     # リランク(precision段, cross特徴)
  explain.py      # 根拠説明生成(差別化)
  search.py       # パイプライン統合
data/             # サンプル契約書/議事録
eval/
  testset.jsonl   # クエリ×正解文書ペア
  evaluate.py     # recall@k / MRR / nDCG (vector-only vs +rerank)
api/search_api.py
tests/            # 類義語一致・根拠説明・リランク非劣化を検証
```
