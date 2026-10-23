const envUrl = import.meta.env.VITE_API_URL;
const isCloudDeploy = typeof window !== "undefined" && (
  window.location.hostname.includes("onrender.com") || 
  window.location.hostname.includes("vercel.app")
);
const fallbackCloudBackend = "https://hifazat-ai-backend-m0m0.onrender.com";

export const API_BASE = (envUrl || (isCloudDeploy ? fallbackCloudBackend : "")).replace(/\/$/, "");
export const API = `${API_BASE}/api`;
export const apiUrl = (path: string) => `${API}${path.startsWith("/") ? path : `/${path}`}`;

export async function parse(res: Response) {
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const validation = Array.isArray(data?.detail)
      ? data.detail.map((item: any) => `${item.loc?.slice(1).join(".") || "Input"}: ${item.msg}`).join("; ")
      : "";
    const msg =
      (typeof data?.detail === "string" ? data.detail : data?.detail?.message) ||
      validation ||
      data?.message ||
      `Request failed (${res.status}). Check that the backend is running and retry.`;
    throw new Error(msg);
  }
  return data;
}

export const api = {
  health: () => fetch(apiUrl("/health")).then(parse),
  dashboard: () => fetch(apiUrl("/dashboard")).then(parse),
  analyzeText: (text: string, include_genai = true, safer_rephrase = false) =>
    fetch(apiUrl("/analyze/text"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, include_genai, safer_rephrase }),
    }).then(parse),
  analyzeYoutube: (url: string, max_comments = 200) =>
    fetch(apiUrl("/youtube/analyze"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, max_comments, include_genai_summary: false }),
    }).then(parse),
  latest: () => fetch(apiUrl("/youtube/latest")).then(parse),
  comment: (id: number) => fetch(apiUrl(`/comments/${id}`)).then(parse),
  review: (id: number, decision: string, notes = "") =>
    fetch(apiUrl(`/comments/${id}/review`), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision, notes }),
    }).then(parse),
  research: () => fetch(apiUrl("/research/metrics")).then(parse),
  researchErrors: () => fetch(apiUrl("/research/errors")).then(parse),
  liveStart: (url: string) =>
    fetch(apiUrl("/live/start"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    }).then(parse),
  livePause: () => fetch(apiUrl("/live/pause"), { method: "POST" }).then(parse),
  liveResume: () => fetch(apiUrl("/live/resume"), { method: "POST" }).then(parse),
  liveStop: () => fetch(apiUrl("/live/stop"), { method: "POST" }).then(parse),
  liveStatus: () => fetch(apiUrl("/live/status")).then(parse),
  settings: () => fetch(apiUrl("/settings")).then(parse),
  saveSettings: (body: Record<string, any>) =>
    fetch(apiUrl("/settings"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(parse),
  exportUrl: (analysisId: number, kind: "csv" | "json" | "pdf") => apiUrl(`/export/${analysisId}/${kind}`),
};
