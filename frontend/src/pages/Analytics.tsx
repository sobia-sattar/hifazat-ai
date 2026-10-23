import { useEffect, useState } from "react";
import CommentDetail from "../components/CommentDetail";
import { DistChart, PieDist, TrendChart } from "../components/Charts";
import { api } from "../services/api";
import type { CommentRow } from "../types";

export default function AnalyticsPage() {
  const [data, setData] = useState<any>(null);
  const [open, setOpen] = useState<CommentRow | null>(null);
  useEffect(() => {
    api.dashboard().then(setData);
  }, []);
  const stats = data?.stats || {};
  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-semibold">Analytics</h2>
      <div className="grid gap-4 lg:grid-cols-2">
        <PieDist title="Safe vs bullying" data={{ Safe: stats.safe || 0, Bullying: stats.bullying || 0 }} />
        <DistChart title="Bullying vs remaining comments" data={{ Bullying: stats.bullying || 0, Remaining: (stats.total || 0) - (stats.bullying || 0) }} />
        <DistChart title="Harmful categories" data={stats.category_distribution} />
        <DistChart title="Language" data={stats.language_distribution} />
        <DistChart title="Risk" data={stats.risk_distribution} />
        <DistChart title="Confidence" data={stats.confidence_distribution} />
        <TrendChart title="Toxicity trend" data={stats.trend} />
      </div>
      <div className="card p-4">
        <h3 className="mb-2 text-sm">High-risk queue</h3>
        {(data?.recent_high_risk || []).map((c: CommentRow) => (
          <button key={c.id} className="mb-2 block w-full rounded-xl border border-line px-3 py-2 text-left text-sm" onClick={() => setOpen(c)}>
            {c.original_text}
          </button>
        ))}
      </div>
      {open && <CommentDetail row={open} onClose={() => setOpen(null)} />}
    </div>
  );
}
