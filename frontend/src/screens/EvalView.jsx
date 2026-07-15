import React from "react";

// 精度評価ビュー: vector-only vs +rerank の指標比較。
export default function EvalView({ evalResult }) {
  const rows = Object.entries(evalResult || {});
  return (
    <div className="card">
      <h2>精度評価（vector-only vs +rerank）</h2>
      <table><thead><tr><th>パイプライン</th><th>recall@3</th><th>precision@3</th><th>MRR</th><th>nDCG@3</th></tr></thead>
        <tbody>{rows.map(([name, m]) => (
          <tr key={name}><td>{name}</td><td>{m["recall@3"]}</td><td>{m["precision@3"]}</td>
            <td>{m.MRR}</td><td>{m["nDCG@3"]}</td></tr>))}
        </tbody></table>
      <p className="note">※リランクは非劣化かつ多くのケースで MRR/nDCG を改善（距離撹乱に強い）。</p>
    </div>
  );
}
