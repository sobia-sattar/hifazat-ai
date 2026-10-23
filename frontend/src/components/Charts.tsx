import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const COLORS = ["#38bdf8", "#f43f5e", "#a78bfa", "#34d399", "#fbbf24", "#fb7185", "#94a3b8", "#22d3ee"];

export function DistChart({ title, data }: { title: string; data: Record<string, number> | undefined }) {
  const rows = Object.entries(data || {}).map(([name, value]) => ({ name, value }));
  if (!rows.length) return <EmptyChart title={title} />;
  return (
    <div className="card p-4">
      <h3 className="mb-3 text-sm font-medium text-slate-300">{title}</h3>
      <div className="h-56">
        <ResponsiveContainer>
          <BarChart data={rows}>
            <CartesianGrid stroke="#1e2a3d" vertical={false} />
            <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 11 }} interval={0} angle={-18} textAnchor="end" height={60} />
            <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} />
            <Tooltip contentStyle={{ background: "#101522", border: "1px solid #1e2a3d" }} />
            <Bar dataKey="value" radius={[8, 8, 0, 0]}>
              {rows.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export function PieDist({ title, data }: { title: string; data: Record<string, number> | undefined }) {
  const rows = Object.entries(data || {}).map(([name, value]) => ({ name, value }));
  if (!rows.length) return <EmptyChart title={title} />;
  return (
    <div className="card p-4">
      <h3 className="mb-3 text-sm font-medium text-slate-300">{title}</h3>
      <div className="h-56">
        <ResponsiveContainer>
          <PieChart>
            <Pie data={rows} dataKey="value" nameKey="name" innerRadius={48} outerRadius={80}>
              {rows.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip contentStyle={{ background: "#101522", border: "1px solid #1e2a3d" }} />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export function TrendChart({ title, data }: { title: string; data: { t?: string; bullying?: number; toxic?: number }[] | undefined }) {
  const rows = (data || []).map((d, i) => {
    const label = d.t ? String(d.t).replace("T", " ").slice(0, 16) : `#${i + 1}`;
    return { i, label, ...d };
  });
  if (!rows.length) return <EmptyChart title={title} note="Timestamps were not available for a trend." />;
  return (
    <div className="card p-4">
      <h3 className="mb-3 text-sm font-medium text-slate-300">{title}</h3>
      <div className="h-56">
        <ResponsiveContainer>
          <LineChart data={rows}>
            <CartesianGrid stroke="#1e2a3d" />
            <XAxis dataKey="label" interval={Math.max(0, Math.ceil(rows.length / 6) - 1)} tick={{ fill: "#94a3b8", fontSize: 10 }} />
            <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} />
            <Tooltip contentStyle={{ background: "#101522", border: "1px solid #1e2a3d" }} />
            <Line type="monotone" dataKey="bullying" stroke="#f43f5e" dot={false} />
            {rows.some((r) => r.toxic !== undefined) && <Line type="monotone" dataKey="toxic" stroke="#a78bfa" dot={false} />}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function EmptyChart({ title, note }: { title: string; note?: string }) {
  return (
    <div className="card p-4">
      <h3 className="mb-3 text-sm font-medium text-slate-300">{title}</h3>
      <p className="text-sm text-slate-500">{note || "Not available"}</p>
    </div>
  );
}

export function Metric({ label, value, accent }: { label: string; value: string | number | null | undefined; accent?: string }) {
  return (
    <div className="card p-4">
      <p className="text-xs uppercase tracking-wide text-slate-400">{label}</p>
      <p className={`mt-2 text-2xl font-semibold ${accent || "text-white"}`}>{value ?? "Not available"}</p>
    </div>
  );
}
