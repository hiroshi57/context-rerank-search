const BASE = import.meta.env?.VITE_API || "http://localhost:8000";
const h = (t) => ({ "Content-Type": "application/json", "X-Tenant-Id": t });

export async function addDocs(t, docs) {
  return (await fetch(`${BASE}/v1/docs`, { method: "POST", headers: h(t), body: JSON.stringify({ docs }) })).json();
}
export async function search(t, body) {
  return (await fetch(`${BASE}/v1/search`, { method: "POST", headers: h(t), body: JSON.stringify(body) })).json();
}
