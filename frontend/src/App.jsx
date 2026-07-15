import React, { useState } from "react";
import SearchUI from "./screens/SearchUI.jsx";
import EvalView from "./screens/EvalView.jsx";
import { addDocs, search } from "./api.js";

const TENANT = "demo-tenant";
const SEED = [
  { doc_id: "saas", title: "SaaS利用契約書", text: "第4条 利用者は30日前の通知で本契約を解約できる。" },
  { doc_id: "gyoumu", title: "業務委託契約書", text: "第3条 いずれの当事者も1ヶ月前の予告で中途解約できる。" },
  { doc_id: "nda", title: "秘密保持契約書", text: "秘密情報を第三者に開示してはならない。" },
];
const DEMO_RESULTS = [
  { doc_id: "saas", rerank_score: 0.31, reasons: ["同義概念で一致(キャンセル→解約)"], snippet: "…30日前の通知で解約…" },
  { doc_id: "gyoumu", rerank_score: 0.28, reasons: ["同義概念で一致(中途解約)"], snippet: "…1ヶ月前の予告で中途解約…" },
];
const DEMO_EVAL = {
  vector_only: { "recall@3": 1.0, "precision@3": 0.47, MRR: 0.9, "nDCG@3": 0.939 },
  with_rerank: { "recall@3": 1.0, "precision@3": 0.53, MRR: 1.0, "nDCG@3": 0.984 },
};

export default function App() {
  const [tab, setTab] = useState("search");
  const [results, setResults] = useState(DEMO_RESULTS);
  const [busy, setBusy] = useState(false);

  const doSearch = async (body) => {
    setBusy(true);
    try {
      await addDocs(TENANT, SEED);
      const res = await search(TENANT, body);
      setResults(res.results || []);
    } catch (e) {
      alert("バックエンド未起動の可能性: " + e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="wrap">
      <h1>文脈類似ドキュメント検索</h1>
      <nav>
        <button onClick={() => setTab("search")} disabled={tab === "search"}>検索</button>
        <button onClick={() => setTab("eval")} disabled={tab === "eval"}>精度評価</button>
      </nav>
      {tab === "search"
        ? <SearchUI onSearch={doSearch} results={results} busy={busy} />
        : <EvalView evalResult={DEMO_EVAL} />}
    </div>
  );
}
