import { useState, useId } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie,
} from "recharts";
import { evaluatePassword } from "../utils/passwordStrength";

// Gauge Segment Configuration
const GAUGE_SEGMENTS = [
  { label: "Very Weak", color: "#f43f5e", range: [0, 20] },
  { label: "Weak", color: "#fb923c", range: [20, 40] },
  { label: "Moderate", color: "#facc15", range: [40, 60] },
  { label: "Strong", color: "#38bdf8", range: [60, 80] },
  { label: "Very Strong", color: "#38dea9", range: [80, 100] },
];

const COMPOSITION_COLORS: Record<string, string> = {
  Lowercase: "#38bdf8",
  Uppercase: "#818cf8",
  Numbers: "#38dea9",
  Symbols: "#f472b6",
};

export default function PasswordChecker() {
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const passwordInputId = useId();

  const feedback = evaluatePassword(password);

  // Prepare criteria data for Recharts Bar Chart
  const criteriaChartData = feedback.criteria.map((c) => ({
    name: c.name,
    score: c.score,
    met: c.met,
    detail: c.detail,
  }));

  // Prepare composition data for Donut Chart
  const compositionData = [
    { name: "Lowercase", value: feedback.counts.lowercase },
    { name: "Uppercase", value: feedback.counts.uppercase },
    { name: "Numbers", value: feedback.counts.numbers },
    { name: "Symbols", value: feedback.counts.symbols },
  ].filter((item) => item.value > 0);

  // Calculate Gauge Needle Rotation (from -90deg to +90deg across 0-100%)
  const needleAngle = -90 + (feedback.scorePercent / 100) * 180;

  return (
    <div className="space-y-6 max-w-5xl">
      <header className="page-heading">
        <span className="eyebrow">DEFENSE / CREDENTIAL RESILIENCE</span>
        <h1>Password Strength Analysis</h1>
        <p>
          Evaluate computational entropy, pattern resistance, and character distribution locally in real time.
        </p>
      </header>

      {/* Strict Privacy Notice */}
      <div className="notice" role="note">
        <strong>Strict Local Privacy:</strong> All password analysis and chart rendering execute 100% inside your browser.
        No passwords, metrics, or telemetry are ever sent over the network, saved in storage, or logged.
      </div>

      {/* Password Input Card */}
      <section className="card p-6 space-y-4" aria-labelledby="input-heading">
        <h2 id="input-heading" className="text-xl font-semibold text-slate-100">
          Interactive Password Evaluation
        </h2>

        <div>
          <label htmlFor={passwordInputId} className="block text-sm font-medium mb-2 text-slate-300">
            Type or paste password to analyze
          </label>
          <div className="relative flex items-center">
            <input
              id={passwordInputId}
              type={showPassword ? "text" : "password"}
              className="input pr-24 font-mono w-full text-base tracking-wider"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password..."
              autoComplete="off"
              spellCheck="false"
              maxLength={128}
            />
            <button
              type="button"
              className="absolute right-2 px-3 py-1.5 text-xs font-semibold rounded bg-slate-800 text-slate-200 hover:bg-slate-700 transition"
              onClick={() => setShowPassword(!showPassword)}
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? "Hide" : "Show"}
            </button>
          </div>
        </div>

        {/* Quick Strength Bar */}
        <div>
          <div className="flex justify-between items-center text-xs mb-1.5">
            <span className="text-slate-400">Security rating:</span>
            <span className={`font-bold ${feedback.colorClass}`}>{feedback.tier}</span>
          </div>
          <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden flex gap-1 p-0.5 border border-slate-800">
            {[0, 1, 2, 3].map((step) => {
              const active = feedback.score > step;
              let fillBg = "bg-slate-800";
              if (active) {
                if (feedback.score === 1) fillBg = "bg-rose-500";
                else if (feedback.score === 2) fillBg = "bg-amber-400";
                else if (feedback.score === 3) fillBg = "bg-sky-400";
                else fillBg = "bg-emerald-400";
              }
              return (
                <div
                  key={step}
                  className={`flex-1 h-full rounded transition-all duration-300 ${fillBg}`}
                />
              );
            })}
          </div>
        </div>
      </section>

      {/* Visual Analytics Grid: Gauge + Composition */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Requirement 1: Password Strength Gauge */}
        <section className="card p-6 flex flex-col items-center justify-between space-y-4" aria-labelledby="gauge-heading">
          <div className="w-full flex justify-between items-center border-b border-line pb-3">
            <h3 id="gauge-heading" className="text-sm font-semibold uppercase tracking-wider text-slate-300">
              Strength Gauge
            </h3>
            <span className="text-xs px-2.5 py-0.5 rounded bg-slate-900 border border-slate-800 font-mono text-slate-300">
              {feedback.entropyBits} bits entropy
            </span>
          </div>

          {/* Semi-Circular SVG Speedometer Gauge */}
          <div className="relative w-full max-w-[280px] h-[155px] flex items-center justify-center pt-2">
            <svg viewBox="0 0 200 110" className="w-full h-full overflow-visible">
              <defs>
                <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#f43f5e" />
                  <stop offset="35%" stopColor="#fb923c" />
                  <stop offset="55%" stopColor="#facc15" />
                  <stop offset="75%" stopColor="#38bdf8" />
                  <stop offset="100%" stopColor="#38dea9" />
                </linearGradient>
                <filter id="gaugeGlow">
                  <feGaussianBlur stdDeviation="3" result="blur" />
                  <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
              </defs>

              {/* Background Arc */}
              <path
                d="M 20 100 A 80 80 0 0 1 180 100"
                fill="none"
                stroke="#1e293b"
                strokeWidth="16"
                strokeLinecap="round"
              />

              {/* Active Gradient Arc */}
              <path
                d="M 20 100 A 80 80 0 0 1 180 100"
                fill="none"
                stroke="url(#gaugeGradient)"
                strokeWidth="16"
                strokeLinecap="round"
                strokeDasharray="251.2"
                strokeDashoffset={251.2 - (251.2 * feedback.scorePercent) / 100}
                filter="url(#gaugeGlow)"
                className="transition-all duration-500 ease-out"
              />

              {/* Indicator Needle */}
              <g
                transform={`translate(100, 100) rotate(${needleAngle})`}
                className="transition-transform duration-500 ease-out"
              >
                <polygon points="-3,-5 0,-85 3,-5" fill={feedback.accentColor} filter="url(#gaugeGlow)" />
                <circle cx="0" cy="0" r="7" fill="#0f172a" stroke={feedback.accentColor} strokeWidth="3" />
              </g>

              {/* Ticks & Labels */}
              <text x="18" y="112" fill="#64748b" fontSize="8" textAnchor="middle">0%</text>
              <text x="100" y="24" fill="#64748b" fontSize="8" textAnchor="middle">50%</text>
              <text x="182" y="112" fill="#64748b" fontSize="8" textAnchor="middle">100%</text>
            </svg>
          </div>

          {/* Central Tier Badge & Brute-Force Estimate */}
          <div className="text-center pt-1">
            <span
              className={`text-2xl font-black tracking-tight block ${feedback.colorClass}`}
              style={{ textShadow: `0 0 20px ${feedback.accentColor}55` }}
            >
              {feedback.tier}
            </span>
            <span className="text-xs text-slate-400 mt-1 block">
              Estimated offline crack resistance: <strong className="text-slate-200">{feedback.timeToCrack}</strong>
            </span>
          </div>

          {/* Gauge Legend */}
          <div className="w-full flex justify-between gap-1 text-[10px] text-slate-400 pt-2 border-t border-line/60">
            {GAUGE_SEGMENTS.map((seg) => (
              <span key={seg.label} className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full inline-block" style={{ backgroundColor: seg.color }} />
                {seg.label}
              </span>
            ))}
          </div>
        </section>

        {/* Character Pool & Composition Donut Chart */}
        <section className="card p-6 flex flex-col justify-between space-y-4" aria-labelledby="comp-heading">
          <div className="w-full flex justify-between items-center border-b border-line pb-3">
            <h3 id="comp-heading" className="text-sm font-semibold uppercase tracking-wider text-slate-300">
              Character Distribution
            </h3>
            <span className="text-xs text-slate-400">Total: {feedback.length} chars</span>
          </div>

          <div className="h-44 w-full flex items-center justify-center">
            {compositionData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={compositionData}
                    dataKey="value"
                    nameKey="name"
                    innerRadius={46}
                    outerRadius={68}
                    paddingAngle={4}
                    stroke="#0b1329"
                    strokeWidth={2}
                  >
                    {compositionData.map((entry) => (
                      <Cell key={entry.name} fill={COMPOSITION_COLORS[entry.name] || "#38bdf8"} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#030c1b",
                      borderColor: "#1e293b",
                      borderRadius: "8px",
                      fontSize: "12px",
                      color: "#e2e8f0",
                    }}
                    formatter={(val: any, name: any) => [`${val} chars`, name]}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex flex-col items-center justify-center text-slate-500 text-xs">
                <span className="w-16 h-16 rounded-full border-2 border-dashed border-slate-800 flex items-center justify-center mb-2">
                  0
                </span>
                Type characters to see distribution
              </div>
            )}
          </div>

          {/* Counts Matrix */}
          <div className="grid grid-cols-4 gap-2 pt-2 border-t border-line/60 text-center">
            <div className="p-2 rounded bg-slate-900 border border-slate-800">
              <span className="text-[10px] text-slate-400 block">Lowercase</span>
              <strong className="text-sm text-sky-400 font-mono">{feedback.counts.lowercase}</strong>
            </div>
            <div className="p-2 rounded bg-slate-900 border border-slate-800">
              <span className="text-[10px] text-slate-400 block">Uppercase</span>
              <strong className="text-sm text-indigo-400 font-mono">{feedback.counts.uppercase}</strong>
            </div>
            <div className="p-2 rounded bg-slate-900 border border-slate-800">
              <span className="text-[10px] text-slate-400 block">Numbers</span>
              <strong className="text-sm text-emerald-400 font-mono">{feedback.counts.numbers}</strong>
            </div>
            <div className="p-2 rounded bg-slate-900 border border-slate-800">
              <span className="text-[10px] text-slate-400 block">Symbols</span>
              <strong className="text-sm text-pink-400 font-mono">{feedback.counts.symbols}</strong>
            </div>
          </div>
        </section>
      </div>

      {/* Requirement 2: Strength Breakdown Chart */}
      <section className="card p-6 space-y-4" aria-labelledby="criteria-chart-heading">
        <div className="flex justify-between items-center border-b border-line pb-3">
          <div>
            <h3 id="criteria-chart-heading" className="text-sm font-semibold uppercase tracking-wider text-slate-300">
              Criteria Fulfillment Breakdown
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Measures compliance across key security parameters (Length, Cases, Numbers, Symbols).
            </p>
          </div>
          <span className="text-xs text-slate-400">
            {feedback.criteria.filter((c) => c.met).length} / {feedback.criteria.length} criteria met
          </span>
        </div>

        <div className="h-56 w-full pt-2">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={criteriaChartData}
              layout="vertical"
              margin={{ top: 5, right: 30, left: 40, bottom: 5 }}
            >
              <XAxis type="number" domain={[0, 100]} tick={{ fill: "#64748b", fontSize: 11 }} unit="%" />
              <YAxis
                type="category"
                dataKey="name"
                tick={{ fill: "#94a3b8", fontSize: 12 }}
                width={110}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#030c1b",
                  borderColor: "#1e293b",
                  borderRadius: "8px",
                  fontSize: "12px",
                  color: "#e2e8f0",
                }}
                formatter={(val: any, _: any, item: any) => [
                  `${val}% · ${item.payload.detail}`,
                  item.payload.met ? "Status: Passed" : "Status: Missing",
                ]}
              />
              <Bar dataKey="score" radius={[0, 6, 6, 0]} barSize={18}>
                {criteriaChartData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.met ? "#38dea9" : entry.score > 0 ? "#facc15" : "#334155"}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      {/* Requirement 3: Security Feedback & Recommendations */}
      <section className="card p-6 space-y-4" aria-labelledby="feedback-heading">
        <h3 id="feedback-heading" className="text-base font-semibold text-slate-200 border-b border-line pb-3">
          Security Feedback & Actionable Improvements
        </h3>

        {/* Warnings / Vulnerabilities Identified */}
        {feedback.warnings.length > 0 && (
          <div className="p-4 rounded-lg border border-rose-500/30 bg-rose-500/10 text-sm space-y-2">
            <span className="font-semibold text-rose-300 flex items-center gap-2">
              <span className="inline-block w-2 h-2 rounded-full bg-rose-400" />
              Identified Vulnerability Signals ({feedback.warnings.length}):
            </span>
            <ul className="list-disc list-inside text-rose-200/90 text-xs space-y-1">
              {feedback.warnings.map((warn, i) => (
                <li key={i}>{warn}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Improvement Suggestions */}
        {feedback.suggestions.length > 0 && (
          <div className="p-4 rounded-lg border border-sky-500/30 bg-sky-500/10 text-sm space-y-2">
            <span className="font-semibold text-sky-300 flex items-center gap-2">
              <span className="inline-block w-2 h-2 rounded-full bg-sky-400" />
              Recommendations to Increase Entropy:
            </span>
            <ul className="list-disc list-inside text-sky-200/90 text-xs space-y-1">
              {feedback.suggestions.map((sug, i) => (
                <li key={i}>{sug}</li>
              ))}
            </ul>
          </div>
        )}

        {/* When Password is Strong / Very Strong */}
        {feedback.score >= 3 && feedback.warnings.length === 0 && (
          <div className="p-4 rounded-lg border border-emerald-500/30 bg-emerald-500/10 text-sm text-emerald-200 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_#38dea9]" />
            High computational entropy achieved! This credential resists offline dictionary and rainbow table lookups.
          </div>
        )}

        {/* Security Boundary Disclaimer */}
        <p className="text-xs text-slate-500 leading-relaxed pt-3 border-t border-line/60">
          <strong>Security Notice:</strong> A strength estimate indicates mathematical resistance against automated brute-force
          guessing. It does not protect against phishing attacks, malware, keyloggers, or credential stuffing from compromised third-party
          databases. Use unique passwords for each service and enable Multi-Factor Authentication (MFA).
        </p>
      </section>
    </div>
  );
}
