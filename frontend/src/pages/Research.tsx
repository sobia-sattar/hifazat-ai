import { useEffect, useMemo, useState } from "react";
import { DistChart } from "../components/Charts";
import { api } from "../services/api";

export default function ResearchPage() {
  const [data, setData] = useState<any>(null);
  useEffect(() => {
    api.research().then(setData);
  }, []);
  if (!data) return <p>Loading…</p>;
  if (!data.available) {
    return (
      <div className="card p-6">
        <h2 className="text-2xl font-semibold">Research Lab</h2>
        <p className="mt-2 text-slate-400">{data.message || "Requires training"}</p>
        <p className="mt-2 text-sm">Run <code>python research/acquire_data.py</code>, <code>python research/prepare_data.py</code>, then <code>python research/train.py</code>.</p>
      </div>
    );
  }
  const m = data.metrics;
  const cm = m.confusion_matrix_test || {};
  const fair = m.fairness_test || {};
  return (
    <div className="space-y-6">
      <header>
        <h2 className="text-3xl font-semibold">Research Lab</h2>
        <p className="text-slate-400">Real evaluation outputs only. Demo comments are excluded from these metrics.</p>
      </header>
      <section className="card overflow-x-auto p-5">
        <h3 className="mb-3 font-medium">Dataset distribution</h3>
        <pre className="text-xs text-slate-300">{JSON.stringify(m.dataset, null, 2)}</pre>
      </section>
      <Table title="Model comparison (validation)" rows={m.model_comparison_validation} />
      <Table title="Test set (once)" rows={[m.test]} keys={["accuracy", "precision", "recall", "macro_f1", "weighted_f1"]} />
      <section className="card p-5">
        <h3 className="mb-3 font-medium">Per-language test performance</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead><tr className="text-slate-400"><th className="py-2">Language</th><th>Precision</th><th>Recall</th><th>F1</th><th>FPR</th><th>FNR</th><th>n</th></tr></thead>
            <tbody>
              {["English", "Urdu", "Roman Urdu", "Code-mixed"].map((k) => {
                const r = m.per_language_test?.[k];
                if (!r?.available) return <tr key={k}><td className="py-2">{k}</td><td colSpan={6}>Not available</td></tr>;
                return (
                  <tr key={k} className="border-t border-line">
                    <td className="py-2">{k}</td>
                    <td>{fmt(r.precision)}</td>
                    <td>{fmt(r.recall)}</td>
                    <td>{fmt(r.binary_harmful_f1)}</td>
                    <td>{fmt(r.false_positive_rate)}</td>
                    <td>{fmt(r.false_negative_rate)}</td>
                    <td>{r.n}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
      <section className="card p-5">
        <h3 className="mb-3 font-medium">Per-category F1 (test)</h3>
        <table className="w-full text-left text-sm">
          <thead><tr className="text-slate-400"><th>Label</th><th>Precision</th><th>Recall</th><th>F1</th><th>Support</th></tr></thead>
          <tbody>
            {Object.entries(m.test?.per_class || {}).map(([k, v]: any) => (
              <tr key={k} className="border-t border-line">
                <td className="py-2">{k}</td>
                <td>{fmt(v.precision)}</td>
                <td>{fmt(v.recall)}</td>
                <td>{fmt(v.f1)}</td>
                <td>{v.support}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <section className="card p-5">
        <h3 className="mb-2 font-medium">Fairness gaps</h3>
        <p className="mb-3 text-sm text-slate-400">{fair.note || "Do not claim the model is unbiased."}</p>
        <p className="text-sm">Max−min F1 gap: {fair.gap_max_minus_min_f1 ?? "Not available"}</p>
      </section>
      <section className="card p-5">
        <h3 className="mb-3 font-medium">Confusion matrix (harmful vs safe)</h3>
        <p>TN {cm.tn} · FP {cm.fp} · FN {cm.fn} · TP {cm.tp}</p>
      </section>
      <DistChart title="Language distribution in training data" data={m.dataset?.by_language} />
      <DistChart title="Class counts" data={m.dataset?.class_counts} />
      <section className="card p-5">
        <h3 className="mb-3 font-medium">Ablation (validation)</h3>
        <pre className="overflow-x-auto text-xs">{JSON.stringify(m.ablation_validation, null, 2)}</pre>
      </section>
      <section className="card p-5">
        <h3 className="mb-3 font-medium">Calibration</h3>
        <pre className="overflow-x-auto text-xs">{JSON.stringify(m.calibration_test, null, 2)}</pre>
      </section>
      <section className="card p-5">
        <h3 className="mb-3 font-medium">Error analysis</h3>
        <pre className="overflow-x-auto text-xs">{JSON.stringify(m.error_analysis_test, null, 2)}</pre>
        <ErrorLab />
      </section>
      <p className="text-sm text-slate-500">{m.limitations}</p>
    </div>
  );
}

function Table({ title, rows, keys }: { title: string; rows: any[]; keys?: string[] }) {
  if (!rows?.length) return <div className="card p-5">{title}: Not available</div>;
  const cols = keys || Object.keys(rows[0]).filter((k) => typeof rows[0][k] !== "object");
  return (
    <section className="card overflow-x-auto p-5">
      <h3 className="mb-3 font-medium">{title}</h3>
      <table className="w-full text-left text-sm">
        <thead><tr className="text-slate-400">{cols.map((c) => <th key={c} className="py-2 pr-4">{c}</th>)}</tr></thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-t border-line">
              {cols.map((c) => <td key={c} className="py-2 pr-4">{fmt(r[c])}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

function fmt(v: any) {
  if (v === null || v === undefined) return "Not available";
  if (typeof v === "number") return Number.isInteger(v) ? String(v) : v.toFixed(4);
  if (typeof v === "object") return JSON.stringify(v);
  return String(v);
}

function ErrorLab() {
  const [data, setData] = useState<any>(null);
  const [language, setLanguage] = useState("all");
  const [tag, setTag] = useState("all");
  const [minConf, setMinConf] = useState(0.0);

  useEffect(() => {
    api.researchErrors().then(setData);
  }, []);

  const examples = data?.errors?.examples || [];
  const counts = data?.errors?.counts || {};

  const filtered = useMemo(() => {
    return examples
      .filter((e: any) => (language === "all" ? true : e.language === language))
      .filter((e: any) => (minConf <= 0 ? true : (e.confidence ?? 0) >= minConf))
      .filter((e: any) => (tag === "all" ? true : (e.tags || []).includes(tag)))
      .slice(0, 80);
  }, [examples, language, tag, minConf]);

  const langs = Array.from(new Set(examples.map((e: any) => e.language))).sort() as string[];
  const tagOptions = [
    { id: "all", label: "All error types" },
    { id: "false_positive", label: "False positives" },
    { id: "false_negative", label: "False negatives" },
    { id: "low_confidence", label: "Low-confidence cases" },
    { id: "roman_urdu", label: "Roman Urdu errors" },
    { id: "urdu", label: "Urdu errors" },
    { id: "code_mixing", label: "Code-mixing errors" },
    { id: "negation", label: "Negation issues" },
    { id: "sarcasm_candidate", label: "Sarcasm candidates" },
    { id: "slang", label: "Slang issues" },
    { id: "context_dependent_candidate", label: "Context-dependent cases" },
  ];

  if (!data) return <div className="mt-3 text-sm text-slate-500">Loading error analysis…</div>;
  if (!data.available) {
    return (
      <div className="mt-3 rounded-xl border border-line bg-white/5 p-4 text-sm text-slate-300">
        Error analysis unavailable. Requires training.
      </div>
    );
  }

  return (
    <div className="mt-3 space-y-3">
      <div className="grid gap-2 lg:grid-cols-4">
        <div className="card p-4">
          <p className="text-xs uppercase tracking-wide text-slate-400">Roman Urdu</p>
          <p className="mt-2 text-2xl font-semibold">{counts.roman_urdu ?? 0}</p>
        </div>
        <div className="card p-4">
          <p className="text-xs uppercase tracking-wide text-slate-400">Code-mixing</p>
          <p className="mt-2 text-2xl font-semibold">{counts.code_mixing ?? 0}</p>
        </div>
        <div className="card p-4">
          <p className="text-xs uppercase tracking-wide text-slate-400">False positives</p>
          <p className="mt-2 text-2xl font-semibold">{counts.false_positive ?? 0}</p>
        </div>
        <div className="card p-4">
          <p className="text-xs uppercase tracking-wide text-slate-400">False negatives</p>
          <p className="mt-2 text-2xl font-semibold">{counts.false_negative ?? 0}</p>
        </div>
      </div>

      <div className="card p-4">
        <div className="grid gap-2 md:grid-cols-3">
          <select className="input" value={language} onChange={(e) => setLanguage(e.target.value)}>
            <option value="all">Language: all</option>
            {langs.map((l: string) => (
              <option key={l} value={l}>
                {l}
              </option>
            ))}
          </select>
          <select className="input" value={tag} onChange={(e) => setTag(e.target.value)}>
            {tagOptions.map((t) => (
              <option key={t.id} value={t.id}>
                {t.label}
              </option>
            ))}
          </select>
          <label className="text-xs text-slate-400">
            Min confidence {minConf.toFixed(2)}
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={minConf}
              onChange={(e) => setMinConf(Number(e.target.value))}
              className="mt-1 w-full"
            />
          </label>
        </div>

        <div className="mt-4">
          <p className="text-sm text-slate-300">
            Showing {filtered.length} example error cases (heuristic tags; not gold labels).
          </p>
          <div className="mt-3 space-y-2">
            {filtered.map((e: any, i: number) => (
              <div key={i} className="rounded-xl border border-line bg-white/5 p-3">
                <div className="flex flex-wrap gap-2 text-xs text-slate-400">
                  <span>{e.language}</span>
                  <span>conf {(e.confidence * 100).toFixed(1)}%</span>
                  <span>trueH {String(e.true_harmful)}</span>
                  <span>predH {String(e.pred_harmful)}</span>
                </div>
                <p className="mt-2 text-sm">{e.text}</p>
                <div className="mt-2 flex flex-wrap gap-1">
                  {(e.tags || []).slice(0, 6).map((t: string) => (
                    <span key={t} className="rounded-full border border-line px-2 py-1 text-[11px] text-slate-200">
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            ))}
            {filtered.length === 0 && (
              <p className="text-sm text-slate-500">No matching error examples found.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
