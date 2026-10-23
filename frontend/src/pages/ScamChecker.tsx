import { useState } from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
} from "recharts";

export default function ScamChecker() {
  const [text, setText] = useState("");
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function check() {
    if (!text.trim()) return;
    setBusy(true);
    setError("");
    setResult(null);
    try {
      const res = await fetch("/api/scam/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Analysis failed");
      }
      setResult(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  // Prepare chart data for graphical breakdown
  const chartData = [
    {
      name: "Urgency",
      category: "High Urgency",
      score:
        result?.triggered_rules.find((r: any) => r.id === "urgency")?.weight ||
        0,
      active: !!result?.triggered_rules.some((r: any) => r.id === "urgency"),
    },
    {
      name: "Credentials",
      category: "Data Harvesting",
      score:
        result?.triggered_rules.find((r: any) => r.id === "credentials")
          ?.weight || 0,
      active: !!result?.triggered_rules.some(
        (r: any) => r.id === "credentials"
      ),
    },
    {
      name: "Financial",
      category: "Payment Demands",
      score:
        result?.triggered_rules.find((r: any) => r.id === "financial")
          ?.weight || 0,
      active: !!result?.triggered_rules.some((r: any) => r.id === "financial"),
    },
    {
      name: "Links",
      category: "Suspicious Links",
      score:
        result?.triggered_rules.find((r: any) => r.id === "suspicious_links")
          ?.weight || 0,
      active: !!result?.triggered_rules.some(
        (r: any) => r.id === "suspicious_links"
      ),
    },
    {
      name: "Impersonation",
      category: "Fake Brand/Support",
      score:
        result?.triggered_rules.find((r: any) => r.id === "impersonation")
          ?.weight || 0,
      active: !!result?.triggered_rules.some(
        (r: any) => r.id === "impersonation"
      ),
    },
  ];

  const scorePercentage = Math.min(100, Math.round(((result?.score || 0) / 10) * 100));

  return (
    <div className="space-y-6 max-w-4xl">
      <header className="page-heading">
        <span className="eyebrow flex items-center gap-2">
          <span>DIGITAL DEFENSE</span>
          <span className="text-slate-500">·</span>
          <span>SOCIAL ENGINEERING CHECK</span>
        </span>
        <h1 className="text-3xl font-bold tracking-tight">
          Scam & Phishing Text Checker
        </h1>
        <p className="text-slate-400 text-sm">
          Analyze suspicious messages, emails, or SMS text for phishing patterns, urgency tactics, and deceptive cues.
        </p>
      </header>

      {/* Safety Guardrail Banner */}
      <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-300 flex items-start gap-2.5">
        <span className="text-base">🛡️</span>
        <p className="leading-relaxed">
          <strong>100% Private & Safe:</strong> Your text is analyzed in-memory and never stored.
          Any links inside are automatically neutralized (e.g. <code>hxxps://</code>) so they cannot be clicked.
        </p>
      </div>

      {/* Input Form */}
      <section className="card p-6 space-y-4">
        <label
          htmlFor="scam-text-input"
          className="block text-sm font-medium text-slate-200"
        >
          Paste suspicious message, SMS, or email text
        </label>
        <textarea
          id="scam-text-input"
          dir="auto"
          className="input min-h-32 text-sm"
          maxLength={5000}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Paste full text here... (English, Urdu, or Roman Urdu)&#10;e.g. 'URGENT: Your bank account will be suspended within 24 hours. Verify your identity at http://secure-bank-login.example.com'"
        />
        <div className="flex flex-wrap items-center gap-3">
          <button
            className="btn"
            disabled={busy || !text.trim()}
            onClick={check}
          >
            {busy ? "Analyzing Patterns…" : "Analyze for Scam Indicators ↗"}
          </button>
          <button
            type="button"
            className="btn-ghost"
            disabled={busy || !text}
            onClick={() => {
              setText("");
              setResult(null);
              setError("");
            }}
          >
            Clear
          </button>
        </div>
        {error && <p role="alert" className="notice-error">{error}</p>}
      </section>

      {/* VISUAL GRAPHICAL RESULTS */}
      {result && (
        <section className="card p-6 space-y-6 result-in" aria-live="polite">
          {/* Header Row: Threat Level + Visual Score Gauge */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center border-b border-line pb-6">
            {/* Visual Circular Gauge */}
            <div className="flex flex-col items-center justify-center p-4 rounded-2xl bg-slate-950/70 border border-slate-800/80">
              <div className="relative w-32 h-32 flex items-center justify-center">
                <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
                  <circle
                    cx="50"
                    cy="50"
                    r="40"
                    stroke="#1e293b"
                    strokeWidth="10"
                    fill="transparent"
                  />
                  <circle
                    cx="50"
                    cy="50"
                    r="40"
                    stroke={
                      result.risk_class === "HIGH"
                        ? "#f43f5e"
                        : result.risk_class === "MEDIUM"
                        ? "#f59e0b"
                        : "#10b981"
                    }
                    strokeWidth="10"
                    strokeDasharray={2 * Math.PI * 40}
                    strokeDashoffset={
                      2 * Math.PI * 40 * (1 - scorePercentage / 100)
                    }
                    strokeLinecap="round"
                    fill="transparent"
                    className="transition-all duration-1000 ease-out"
                  />
                </svg>
                <div className="absolute flex flex-col items-center text-center">
                  <span className="text-2xl font-bold font-mono tracking-tight text-white">
                    {result.score}/10
                  </span>
                  <span className="text-[10px] text-slate-400 uppercase tracking-widest font-semibold">
                    Risk Score
                  </span>
                </div>
              </div>
            </div>

            {/* Verdict Box */}
            <div className="md:col-span-2 space-y-2">
              <div className="flex items-center gap-2">
                <span
                  className={`text-xs px-2.5 py-1 rounded font-bold uppercase tracking-wider ${
                    result.risk_class === "HIGH"
                      ? "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                      : result.risk_class === "MEDIUM"
                      ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                      : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                  }`}
                >
                  {result.risk_class === "HIGH"
                    ? "🚨 High Scam Risk"
                    : result.risk_class === "MEDIUM"
                    ? "⚠️ Suspicious Warning"
                    : "✅ Likely Safe Message"}
                </span>
                <span className="text-xs text-slate-400">
                  ({result.triggered_rules.length} indicator(s) triggered)
                </span>
              </div>

              <h2
                className={`text-2xl font-bold ${
                  result.risk_class === "HIGH"
                    ? "text-rose-400"
                    : result.risk_class === "MEDIUM"
                    ? "text-amber-400"
                    : "text-emerald-400"
                }`}
              >
                {result.risk_level}
              </h2>

              <p className="text-xs text-slate-300 leading-relaxed">
                {result.risk_class === "HIGH"
                  ? "This message contains aggressive urgency tactics or requests for sensitive credentials. It has very high similarity to known phishing scams."
                  : result.risk_class === "MEDIUM"
                  ? "This message contains some pressure words or unfamiliar patterns. Do not click links without verifying the sender."
                  : "No obvious scam phrases, artificial urgency, or credential demands were detected in this text."}
              </p>
            </div>
          </div>

          {/* Graphical Breakdown Chart */}
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <span>📊</span>
                <span>Graphical Scam Pattern Breakdown</span>
              </h3>
              <span className="text-xs text-slate-400">Higher bar = greater risk</span>
            </div>

            <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800">
              <div className="h-44 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={chartData}
                    layout="vertical"
                    margin={{ top: 5, right: 20, left: 20, bottom: 5 }}
                  >
                    <XAxis type="number" domain={[0, 4]} hide />
                    <YAxis
                      dataKey="name"
                      type="category"
                      stroke="#94a3b8"
                      fontSize={11}
                      width={90}
                    />
                    <Tooltip
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          const data = payload[0].payload;
                          return (
                            <div className="p-2 rounded bg-slate-900 border border-slate-700 text-xs">
                              <p className="font-semibold text-white">
                                {data.category}
                              </p>
                              <p className="text-slate-300">
                                Status:{" "}
                                <span
                                  className={
                                    data.active
                                      ? "text-rose-400 font-bold"
                                      : "text-slate-500"
                                  }
                                >
                                  {data.active ? "Triggered (+ " + data.score + " pts)" : "Clean"}
                                </span>
                              </p>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Bar dataKey="score" radius={[0, 6, 6, 0]} barSize={16}>
                      {chartData.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={
                            entry.active
                              ? entry.score >= 3
                                ? "#f43f5e"
                                : "#f59e0b"
                              : "#334155"
                          }
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Triggered Indicators Cards */}
          {result.triggered_rules.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-slate-200">
                Triggered Warning Details ({result.triggered_rules.length})
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {result.triggered_rules.map((rule: any) => (
                  <div
                    key={rule.id}
                    className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2"
                  >
                    <div className="flex justify-between items-center">
                      <span className="text-xs font-bold text-rose-300">
                        {rule.category}
                      </span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300 font-mono">
                        +{rule.weight} Weight
                      </span>
                    </div>
                    <p className="text-xs text-slate-300">{rule.description}</p>
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {rule.matches.map((m: string, idx: number) => (
                        <span
                          key={idx}
                          className="text-xs px-2 py-0.5 rounded bg-rose-500/20 text-rose-200 border border-rose-500/30 font-mono"
                        >
                          "{m}"
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Defanged Inert URLs Card */}
          {result.defanged_urls.length > 0 && (
            <div className="space-y-2.5 p-4 rounded-xl bg-slate-950/80 border border-slate-800">
              <div className="flex items-center gap-2 text-xs font-bold text-amber-300">
                <span>🔗</span>
                <span>Neutralized Embedded Links ({result.defanged_urls.length})</span>
              </div>
              <p className="text-xs text-slate-400">
                {result.url_warning}
              </p>
              <div className="space-y-1 font-mono text-xs">
                {result.defanged_urls.map((u: any, idx: number) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-amber-300 select-all"
                  >
                    {u.defanged}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* What to do next checklist */}
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
            <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wide">
              Recommended Next Steps
            </h4>
            <ul className="text-xs text-slate-300 space-y-1">
              <li>• <strong>Do not reply</strong> or confirm any personal details over text.</li>
              <li>• <strong>Never click</strong> unfamiliar links or open downloaded files.</li>
              <li>• <strong>Verify independently</strong> by visiting the official website or dialing customer support directly.</li>
            </ul>
          </div>
        </section>
      )}
    </div>
  );
}
