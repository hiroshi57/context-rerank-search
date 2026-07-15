import React, { useState } from "react";

// 検索UI: クエリ + 文書種別フィルタ + リランクトグル。結果は根拠付き。
export default function SearchUI({ onSearch, results, busy }) {
  const [q, setQ] = useState("契約をキャンセルしたい");
  const [docType, setDocType] = useState("");
  const [rerank, setRerank] = useState(true);
  return (
    <div className="card">
      <h2>文脈類似検索</h2>
      <input style={{ width: "100%" }} value={q} onChange={(e) => setQ(e.target.value)} />
      <label>文書種別
        <select value={docType} onChange={(e) => setDocType(e.target.value)}>
          <option value="">すべて</option><option>契約書</option><option>議事録</option></select>
      </label>
      <label><input type="checkbox" checked={rerank} onChange={(e) => setRerank(e.target.checked)} /> リランク有効</label>
      <button className="primary" disabled={busy}
        onClick={() => onSearch({ query: q, doc_type: docType || null, rerank })}>
        {busy ? "検索中..." : "検索"}
      </button>
      <ul>{(results || []).map((r, i) => (
        <li key={i}><b>{r.doc_id}</b>（score {r.rerank_score ?? r.score}）
          <div className="reasons">{(r.reasons || []).join(" / ")}</div>
          <div className="snippet">{r.snippet}</div></li>))}
      </ul>
    </div>
  );
}
