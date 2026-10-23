import { useEffect, useState } from "react";
import { api } from "../services/api";

export default function ExplainabilityPage() {
  const [data, setData] = useState<any>(null);
  useEffect(() => {
    api.dashboard().then(setData);
  }, []);
  const comments = (data?.comments || []).filter((c: any) => c.classification !== "SAFE").slice(0, 12);
  return (
    <div className="space-y-6">
      <header>
        <h2 className="text-3xl font-semibold">Explainability</h2>
        <p className="text-slate-400">XAI is computed from the trained model (coefficients or token occlusion). GenAI only narrates that evidence.</p>
      </header>
      {comments.length === 0 && <p className="text-slate-500">Analyze a video or text first. If the model is untrained, explanations show “Requires training”.</p>}
      {comments.map((c: any) => (
        <article key={c.id} className="card p-5">
          <p className="text-sm text-slate-400">{c.language} · {c.classification} · {(c.confidence * 100).toFixed(1)}%</p>
          <p className="mt-1">{c.original_text}</p>
          <p className="mt-3 text-sky-300">XAI: {c.xai?.structured_evidence?.summary || "Not available"}</p>
          <p className="text-xs text-slate-500">Method {c.xai?.method}</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {(c.xai?.highlights || []).map((h: any, i: number) => (
              <span key={i} className={`rounded-full px-2 py-1 text-xs ${h.direction === "harmful" ? "bg-rose-500/20 text-rose-200" : "bg-emerald-500/20"}`}>
                {h.term} ({h.contribution})
              </span>
            ))}
          </div>
          <p className="mt-3 text-violet-300">GenAI: {c.genai_explanation || "GenAI explanation unavailable. Model and XAI results remain available."}</p>
        </article>
      ))}
    </div>
  );
}
