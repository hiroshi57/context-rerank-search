"""ローカル埋め込み. 外部API不要で "文脈類似" を近似する.

- 文字 n-gram(bi/tri) TF ベクトル + コーパス IDF 重み
- 類義語グループ展開(例: 解約=解除=キャンセル)により、キーワード不一致でも
  同義の文書をヒットさせる(= キーワード検索では拾えない文脈類似の最小再現)
- L2 正規化した疎ベクトルの内積 = コサイン類似度

本番では OpenAI/Cohere 等の埋め込みに差し替え可能(Embedder インターフェース)。
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, Iterable, List

# 類義語グループ: どの表層が来ても同じ概念トークン(syn:<id>)を付与する
SYNONYM_GROUPS = {
    "cancel": ["解約", "解除", "キャンセル", "中途解約", "取りやめ", "取り消し"],
    "deadline": ["納期", "納入期限", "締切", "締め切り", "期日", "納品期限"],
    "fee": ["料金", "利用料", "費用", "月額", "価格", "対価"],
    "confidential": ["秘密", "機密", "守秘", "秘密保持", "非公開"],
    "renew": ["更新", "自動更新", "継続", "延長"],
    "inspect": ["検収", "受入検査", "検品", "確認完了"],
}
_SURFACE_TO_GROUP = {s: gid for gid, surfaces in SYNONYM_GROUPS.items() for s in surfaces}

_ASCII_RE = re.compile(r"[a-zA-Z0-9]+")
_CJK_RE = re.compile(r"[぀-ヿ一-鿿々〆ぁ-んァ-ヶ]+")


def _char_ngrams(run: str) -> List[str]:
    grams: List[str] = []
    if len(run) == 1:
        return [run]
    grams += [run[i:i + 2] for i in range(len(run) - 1)]
    grams += [run[i:i + 3] for i in range(len(run) - 2)]
    return grams


def analyze(text: str) -> List[str]:
    low = text.lower()
    tokens: List[str] = list(_ASCII_RE.findall(low))
    for run in _CJK_RE.findall(text):
        tokens.extend(_char_ngrams(run))
    # 類義語グループトークンを付与(表層が本文に含まれれば概念トークンを足す)
    for surface, gid in _SURFACE_TO_GROUP.items():
        if surface in text:
            tokens.append(f"syn:{gid}")
    return tokens


@dataclass
class Embedder:
    idf: Dict[str, float] = field(default_factory=dict)

    def fit(self, corpus: Iterable[str]) -> "Embedder":
        docs = [set(analyze(t)) for t in corpus]
        n = len(docs) or 1
        df: Counter = Counter()
        for d in docs:
            df.update(d)
        self.idf = {tok: math.log((n + 1) / (c + 1)) + 1.0 for tok, c in df.items()}
        return self

    def embed(self, text: str) -> Dict[str, float]:
        tf = Counter(analyze(text))
        vec: Dict[str, float] = {}
        for tok, c in tf.items():
            w = self.idf.get(tok, 1.0)     # 未知語は idf=1
            vec[tok] = c * w
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        return {k: v / norm for k, v in vec.items()}


def cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
    if len(a) > len(b):
        a, b = b, a
    return sum(v * b.get(k, 0.0) for k, v in a.items())
