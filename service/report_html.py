"""検索結果 HTMLレポート(標準ライブラリのみ)."""
from __future__ import annotations

import html
from typing import List, Dict


def build_html_report(query: str, results: List[Dict]) -> str:
    rows = ""
    for r in results:
        reasons = "<br>".join(html.escape(x) for x in r.get("reasons", []))
        rows += (f'<tr><td>{html.escape(r["doc_id"])}</td>'
                 f'<td>{r.get("rerank_score", r.get("score", 0))}</td>'
                 f'<td>{reasons}</td><td>{html.escape(r.get("snippet", ""))}</td></tr>')
    return f"""<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8">
<title>文脈類似検索 結果</title>
<style>body{{font-family:system-ui,sans-serif;margin:24px;color:#1a1a2e}}
h1{{color:#5a3fb8}} table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #dde;padding:6px 10px;vertical-align:top}} th{{background:#efeafb}}</style></head><body>
<h1>文脈類似検索 結果</h1>
<p>クエリ: <b>{html.escape(query)}</b></p>
<table><tr><th>文書ID</th><th>スコア</th><th>根拠</th><th>抜粋</th></tr>{rows}</table>
</body></html>"""
