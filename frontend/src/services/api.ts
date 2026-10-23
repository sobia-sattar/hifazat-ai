export const API = `${(import.meta.env.VITE_API_URL || "").replace(/\/$/, "")}/api`;
export const apiUrl = (path: string) => `${API}${path}`;

export async function parse(res: Response) {
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const validation = Array.isArray(data?.detail) ? data.detail.map((item:any)=>`${item.loc?.slice(1).join('.') || 'Input'}: ${item.msg}`).join('; ') : '';
    const msg = (typeof data?.detail === "string" ? data.detail : data?.detail?.message) || validation || data?.message || `Request failed (${res.status}). Check that the backend is running and retry.`;
    throw new Error(msg);
  }
  return data;
}

export const api = {
  health: () => fetch(`${API}/health`).then(parse),
  dashboard: () => fetch(`${API}/dashboard`).then(parse),
  analyzeText: (text: string, include_genai = true, safer_rephrase = false) =>
    fetch(`${API}/analyze/text`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, include_genai, safer_rephrase }),
    }).then(parse),
  analyzeYoutube: (url: string, max_comments = 200) =>
    fetch(`${API}/youtube/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, max_comments, include_genai_summary: false }),
    }).then(parse),
  latest: () => fetch(`${API}/youtube/latest`).then(parse),
  comment: (id: number) => fetch(`${API}/comments/${id}`).then(parse),
  review: (id: number, decision: string, notes = "") =>
    fetch(`${API}/comments/${id}/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision, notes }),
    }).then(parse),
  research: () => fetch(`${API}/research/metrics`).then(parse),
  researchErrors: () => fetch(`${API}/research/errors`).then(parse),
  liveStart: (url: string) =>
    fetch(`${API}/live/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    }).then(parse),
  livePause: () => fetch(`${API}/live/pause`, { method: "POST" }).then(parse),
  liveResume: () => fetch(`${API}/live/resume`, { method: "POST" }).then(parse),
  liveStop: () => fetch(`${API}/live/stop`, { method: "POST" }).then(parse),
  liveStatus: () => fetch(`${API}/live/status`).then(parse),
  settings: () => fetch(`${API}/settings`).then(parse),
  saveSettings: (body: Record<string, any>) =>
    fetch(`${API}/settings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(parse),
  exportUrl: (analysisId: number, kind: "csv" | "json" | "pdf") => `${API}/export/${analysisId}/${kind}`,
};
