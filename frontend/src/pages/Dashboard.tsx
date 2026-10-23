import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { parse, apiUrl } from '../services/api';

type Evidence = {
  authors: {
    total: number;
    confirmed: number;
    repeat: boolean;
    comments: { decision: string }[];
  }[];
};

export default function DashboardPage() {
  const [evidence, setEvidence] = useState<Evidence | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function refresh() {
    setLoading(true);
    setError('');
    try {
      setEvidence(await fetch(apiUrl('/moderation/authors')).then(parse));
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  const people = evidence?.authors || [];
  const stats = [
    ['Saved comments', evidence ? people.reduce((n, p) => n + p.total, 0) : '—'],
    ['Awaiting review', evidence ? people.reduce((n, p) => n + p.comments.filter((c) => c.decision === 'pending').length, 0) : '—'],
    ['Confirmed harmful', evidence ? people.reduce((n, p) => n + p.confirmed, 0) : '—'],
    ['Repeated patterns', evidence ? people.filter((p) => p.repeat).length : '—'],
  ];

  const tools = [
    ['01', 'Channel scanner', 'Analyze public channel comments for harmful or abusive behavior.', '/youtube'],
    ['02', 'Text analysis', 'Analyze text for toxic content with explainable AI feature scores.', '/analyzer'],
    ['03', 'Review center', 'Channel-level human review and moderation before taking action.', '/moderation'],
    ['04', 'Incident center', 'Confidential space to document, track, and review online incidents.', '/incidents'],
    ['05', 'Scam check', 'Analyze suspicious messages for phishing and social engineering cues.', '/scam-check'],
    ['06', 'Password check', 'Evaluate password resilience with real-time interactive charts.', '/password-check'],
    ['07', 'Live monitor', 'Monitor live stream messages and detect threats in real time.', '/live'],
  ];

  return (
    <div className="overview space-y-6">
      <section className="overview-hero">
        <div className="overview-copy">
          <span className="eyebrow flex items-center gap-2">
            <span>HIFAZAT AI (حفاظت AI)</span>
            <span className="text-slate-500">·</span>
            <span>DIGITAL PROTECTION SUITE</span>
          </span>
          <h1 className="horror-title">
            KEEP THE HARM<br />
            <span>OUT OF SIGHT.</span>
          </h1>
          <p>
            <strong className="text-sky-300 font-medium">HIFAZAT AI (حفاظت AI)</strong> — Your Digital World, Your Protection.<br />
            An AI-powered digital safety platform that helps users identify harmful online content,
            recognize suspicious messages, and improve their digital safety.
          </p>
          <div className="overview-actions">
            <Link className="btn" to="/youtube">Scan a channel ↗</Link>
            <Link className="btn-ghost" to="/moderation">Review evidence →</Link>
          </div>
          <span className="overview-caption">
            MULTILINGUAL THREAT DETECTION · ENGLISH · URDU (اردو) · ROMAN URDU · CODE-MIXED
          </span>
        </div>
        <div className="defense-art" aria-hidden="true">
          <div className="defense-ring ring-one" />
          <div className="defense-ring ring-two" />
          <div className="defense-halo" />
          <svg className="defense-shield" viewBox="0 0 200 240">
            <defs>
              <linearGradient id="shield-fill" x2="1" y2="1">
                <stop stopColor="#1f5683" stopOpacity=".7" />
                <stop offset="1" stopColor="#030912" />
              </linearGradient>
            </defs>
            <path
              d="M100 12 178 44v69c0 53-45 94-78 115-33-21-78-62-78-115V44Z"
              fill="url(#shield-fill)"
              stroke="#8ccfff"
              strokeWidth="2"
            />
            <path
              d="m100 31 62 25v56c0 43-34 79-62 98-28-19-62-55-62-98V56Z"
              fill="none"
              stroke="#477aa2"
            />
            <path
              d="m64 114 25 26 49-58"
              fill="none"
              stroke="#caeaff"
              strokeWidth="7"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <span className="art-caption">HIFAZAT / DETECT / DEFEND</span>
        </div>
      </section>

      <section aria-label="Saved review evidence">
        <div className="section-heading">
          <div>
            <span className="eyebrow">YOUR WORKSPACE</span>
            <h2>Evidence at a glance</h2>
          </div>
          <button className="text-button" disabled={loading} onClick={refresh}>
            {loading ? 'Updating…' : 'Refresh ↻'}
          </button>
        </div>
        {error && <p className="notice-error" role="alert">{error}</p>}
        <div className="stat-grid overview-stats">
          {stats.map(([label, value], i) => (
            <div className={'stat-box metric-' + i} key={label}>
              <small>{label}</small>
              <strong>{value}</strong>
            </div>
          ))}
        </div>
        <p className="overview-footnote">
          Saved, identified commenters only. Repeated patterns require three human-confirmed harmful comments within a channel.
        </p>
      </section>

      <section className="tool-grid" aria-label="Project tools">
        {tools.map(([num, title, description, to]) => (
          <Link className="tool-card" key={to} to={to}>
            <div>
              <span className="eyebrow">{num}</span>
              <span aria-hidden="true">↗</span>
            </div>
            <h2>{title}</h2>
            <p>{description}</p>
          </Link>
        ))}
      </section>
    </div>
  );
}
