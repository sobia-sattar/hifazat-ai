import { useState } from 'react';

export default function TextAnalyzerPage() {
  const [text, setText] = useState('Aap ka din acha guzray.');
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function run() {
    setBusy(true);
    setError('');
    setResult(null);
    try {
      const response = await fetch('/api/v2/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(typeof data.detail === 'string' ? data.detail : 'Prediction failed');
      }
      setResult(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function batch(file: File) {
    setBusy(true);
    setError('');
    try {
      const body = new FormData();
      body.append('file', file);
      const response = await fetch('/api/v2/predict/batch', { method: 'POST', body });
      if (!response.ok) throw new Error(JSON.stringify((await response.json()).detail));
      const url = URL.createObjectURL(await response.blob());
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = 'predictions.csv';
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <header>
        <p className="text-xs uppercase tracking-[0.25em] text-sky-400">
          HIFAZAT AI (حفاظت AI) · Multilingual Threat Detection
        </p>
        <h2 className="text-3xl font-semibold">Multilingual text analysis</h2>
      </header>
      <p className="text-slate-400">
        AI-powered threat evaluation across English, Urdu, Roman Urdu, and code-mixed text. Language detection is heuristic.
      </p>

      <section className="card p-5 space-y-4">
        <label htmlFor="research-text">English, Urdu, Roman Urdu or mixed text</label>
        <textarea
          id="research-text"
          dir="auto"
          maxLength={8000}
          className="input min-h-32"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <button className="btn" disabled={busy || !text.trim()} onClick={run}>
          {busy ? 'Processing…' : 'Analyze'}
        </button>
        <label className="block text-sm">
          Batch CSV · text column · up to 1,000 rows
          <input
            className="block mt-2"
            type="file"
            accept=".csv"
            disabled={busy}
            onChange={(e) => {
              if (e.target.files?.[0]) batch(e.target.files[0]);
            }}
          />
        </label>
        {error && <p role="alert" className="text-rose-300">{error}</p>}
      </section>

      {result && (
        <section className="card p-6 space-y-4" aria-live="polite">
          <h3 className="text-3xl font-bold">{result.binary_prediction}</h3>
          <p>
            Harmful probability: {(100 * result.harmful_probability).toFixed(1)}% · binary threshold: {result.binary_threshold.toFixed(2)}
          </p>
          <p>
            Language: {result.language} · script: {result.script} · code-mixed: {String(result.code_mixed)}
          </p>
          {result.category_binary_disagreement && (
            <p className="text-amber-300">Binary and category heads disagree. Human review recommended.</p>
          )}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr>
                  <th>Category</th>
                  <th>Probability</th>
                  <th>Threshold</th>
                  <th>Validation coverage</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(result.categories).map(([label, value]: any) => (
                  <tr key={label} className="border-t border-line">
                    <td className="py-2">{label}</td>
                    <td>{(100 * value.probability).toFixed(1)}%</td>
                    <td>{value.threshold > 1 ? 'Disabled' : value.threshold.toFixed(2)}</td>
                    <td>{value.supported ? 'Evaluable' : 'Unsupported'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p>Category decisions: {result.labels.join(', ')}</p>
          <details>
            <summary>Model feature contributions</summary>
            <pre className="overflow-auto text-xs">{JSON.stringify(result.explanation, null, 2)}</pre>
          </details>
          <p className="text-xs text-slate-500">Artifact version: {result.model_version}</p>
        </section>
      )}
    </div>
  );
}
