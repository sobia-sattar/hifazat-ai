import { useEffect, useState } from "react";
import { api, apiUrl } from "../services/api";

export default function SettingsPage() {
  const [data, setData] = useState<any>(null);
  const [moderation, setModeration] = useState<any>(null);
  const [high, setHigh] = useState(0.75);
  const [low, setLow] = useState(0.55);
  const [message, setMessage] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [busy, setBusy] = useState(false);

  // YouTube API Key state
  const [apiKeyInput, setApiKeyInput] = useState("");
  const [showKey, setShowKey] = useState(false);

  async function load() {
    setBusy(true);
    setErrorMsg("");
    try {
      const d = await api.settings();
      setData(d);
      setHigh(d.high_confidence_threshold);
      setLow(d.low_confidence_threshold);

      const r = await fetch(apiUrl("/moderation/status"));
      if (r.ok) {
        setModeration(await r.json());
      }
    } catch (e: any) {
      setErrorMsg(e.message || "Failed to load settings");
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function saveThresholds() {
    setBusy(true);
    setMessage("");
    setErrorMsg("");
    try {
      const updated = await api.saveSettings({
        high_confidence_threshold: high,
        low_confidence_threshold: low,
      });
      setData(updated);
      setMessage("Review sensitivity thresholds saved successfully.");
    } catch (e: any) {
      setErrorMsg(e.message || "Failed to save thresholds");
    } finally {
      setBusy(false);
    }
  }

  async function saveApiKey() {
    if (!apiKeyInput.trim()) {
      setErrorMsg("Please enter a valid YouTube Data API key.");
      return;
    }
    setBusy(true);
    setMessage("");
    setErrorMsg("");
    try {
      const updated = await api.saveSettings({
        youtube_api_key: apiKeyInput.trim(),
        force_demo_mode: false,
      });
      setData(updated);
      setApiKeyInput("");
      setMessage("✓ YouTube API key connected and activated! Real channel and video comment scans are now live.");
    } catch (e: any) {
      setErrorMsg(e.message || "Failed to save YouTube API key");
    } finally {
      setBusy(false);
    }
  }

  async function clearApiKey() {
    setBusy(true);
    setMessage("");
    setErrorMsg("");
    try {
      const updated = await api.saveSettings({
        youtube_api_key: "",
      });
      setData(updated);
      setApiKeyInput("");
      setMessage("✓ YouTube API key removed. Channel and video scans returned to Demo / Sample mode.");
    } catch (e: any) {
      setErrorMsg(e.message || "Failed to disconnect key");
    } finally {
      setBusy(false);
    }
  }

  async function toggleForceDemo(enabled: boolean) {
    setBusy(true);
    setMessage("");
    setErrorMsg("");
    try {
      const updated = await api.saveSettings({
        force_demo_mode: enabled,
      });
      setData(updated);
      setMessage(
        enabled
          ? "✓ Demo Mode activated: offline sample comments will be used without contacting YouTube."
          : "✓ Demo Mode disabled: live scans with your configured YouTube API key are now active."
      );
    } catch (e: any) {
      setErrorMsg(e.message || "Failed to update demo mode");
    } finally {
      setBusy(false);
    }
  }

  const isConnected = data?.youtube_configured && !data?.force_demo_mode;

  return (
    <div className="space-y-6">
      <header className="page-heading">
        <span className="eyebrow">HIFAZAT AI / SYSTEM SETTINGS &amp; CONNECTIONS</span>
        <h1>Settings &amp; API Configuration</h1>
        <p>Configure live YouTube Data API access, reviewer sensitivity, and detection thresholds.</p>
      </header>

      {/* Status Alerts */}
      {message && <div role="status" className="notice">{message}</div>}
      {errorMsg && <div role="alert" className="notice-error">{errorMsg}</div>}

      {/* Top Stat Grid */}
      <div className="stat-grid">
        <div className="stat-box">
          <small>YouTube API Access</small>
          <p className="mt-3 font-medium">
            {data ? (
              isConnected ? (
                <span className="text-emerald-400">
                  ● Connected {data.youtube_api_key_masked ? `(${data.youtube_api_key_masked})` : ""}
                </span>
              ) : data.force_demo_mode ? (
                <span className="text-amber-300">○ Demo Mode Forced</span>
              ) : (
                <span className="text-slate-400">○ Sample / Demo Mode</span>
              )
            ) : (
              "Checking…"
            )}
          </p>
        </div>

        <div className="stat-box">
          <small>Channel Owner Moderation</small>
          <p className="mt-3 font-medium">
            {moderation ? (
              moderation.configured ? (
                <span className="text-emerald-400">● OAuth Active</span>
              ) : (
                <span className="text-slate-400">○ Read-Only</span>
              )
            ) : (
              "Checking…"
            )}
          </p>
        </div>

        <div className="stat-box">
          <small>AI Detection Engine</small>
          <p className="mt-3 font-medium">
            {data?.model?.ready ? (
              <span className="text-cyan-300">● Ready ({data.model.selected_model})</span>
            ) : (
              <span className="text-rose-400">Unavailable</span>
            )}
          </p>
        </div>
      </div>

      <button className="btn-ghost" disabled={busy} onClick={load}>
        Refresh Status ↻
      </button>

      {/* YouTube Data API Key Management Card */}
      <section className="card p-6 space-y-5">
        <div className="section-heading">
          <div>
            <span className="eyebrow">GOOGLE YOUTUBE DATA API V3</span>
            <h2 className="text-xl font-medium mt-1">Connect YouTube API Key</h2>
            <p className="text-sm text-slate-400">
              Required to scan real public channels and live YouTube comment sections. Without an API key, the system safely uses bundled sample comments.
            </p>
          </div>
          <span
            className={
              isConnected
                ? "flag-badge border-emerald-500/40 text-emerald-300 bg-emerald-950/30"
                : "neutral-badge"
            }
          >
            {isConnected ? "LIVE API ACTIVE" : "SAMPLE / DEMO MODE"}
          </span>
        </div>

        {isConnected && (
          <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-500/30 text-sm text-emerald-200 flex items-center justify-between">
            <div>
              <strong>Active Key:</strong> <code>{data.youtube_api_key_masked}</code>
              <p className="text-xs text-emerald-300/80 mt-1">
                Real channels and video comments can now be fetched directly.
              </p>
            </div>
            <button
              className="btn-ghost text-rose-300 border-rose-500/30 hover:border-rose-400"
              disabled={busy}
              onClick={clearApiKey}
            >
              Disconnect Key
            </button>
          </div>
        )}

        <div className="space-y-3">
          <label className="field-label" htmlFor="yt-key-input">
            {isConnected ? "UPDATE OR REPLACE YOUTUBE API KEY" : "ENTER YOUTUBE DATA API V3 KEY"}
          </label>
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <input
                id="yt-key-input"
                className="input w-full pr-12 font-mono text-sm"
                type={showKey ? "text" : "password"}
                placeholder="AIzaSy..."
                value={apiKeyInput}
                onChange={(e) => setApiKeyInput(e.target.value)}
                disabled={busy}
              />
              <button
                type="button"
                className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-400 hover:text-cyan-300"
                onClick={() => setShowKey(!showKey)}
              >
                {showKey ? "Hide" : "Show"}
              </button>
            </div>
            <button
              className="btn"
              disabled={busy || !apiKeyInput.trim()}
              onClick={saveApiKey}
            >
              {busy ? "Saving…" : "Save & Connect Key ↗"}
            </button>
          </div>
          <p className="text-xs text-slate-400">
            Keys are stored securely in your local environment file and never exposed in client bundles or public endpoints.
          </p>
        </div>

        {/* Demo Mode Toggle */}
        <div className="pt-2 border-t border-slate-800 flex items-center justify-between">
          <div>
            <strong className="text-sm text-slate-200">Force Demo Mode</strong>
            <p className="text-xs text-slate-400">
              When checked, scans will use bundled offline sample comments instead of consuming your YouTube API quota.
            </p>
          </div>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              className="cursor-pointer"
              checked={Boolean(data?.force_demo_mode)}
              onChange={(e) => toggleForceDemo(e.target.checked)}
              disabled={busy}
            />
            <span className="text-xs text-slate-300">Force Demo</span>
          </label>
        </div>

        {/* Step-by-Step Instructions */}
        <details className="mt-4 pt-3 border-t border-slate-800 text-sm text-slate-300">
          <summary className="cursor-pointer text-cyan-300 hover:text-cyan-200 font-medium">
            How to get a free YouTube Data API key (3 quick steps)
          </summary>
          <div className="space-y-2 mt-3 pl-3 text-xs leading-relaxed text-slate-300">
            <p>1. Open the <a className="text-sky-300 underline" href="https://console.cloud.google.com/" target="_blank" rel="noreferrer">Google Cloud Console ↗</a> and create or select a project.</p>
            <p>2. Navigate to <strong>APIs &amp; Services → Library</strong>, search for <strong>YouTube Data API v3</strong>, and click <strong>Enable</strong>.</p>
            <p>3. Go to <strong>APIs &amp; Services → Credentials</strong>, click <strong>+ Create Credentials → API Key</strong>, copy the key (starts with <code>AIzaSy...</code>), and paste it above.</p>
          </div>
        </details>
      </section>

      {/* How to Connect Your Channel (OAuth Moderation) */}
      <details className="card p-6">
        <summary className="cursor-pointer font-medium text-slate-200">
          Advanced: Channel Owner Moderation (OAuth Token)
        </summary>
        <div className="space-y-3 mt-4 text-sm text-slate-300">
          <p>
            Read-only comment analysis only requires an API key. To perform actions like posting warnings or rejecting comments on your own channel, an owner-authorized OAuth token is needed.
          </p>
          <p>
            Tokens stay strictly server-side. Ownership is validated for every action. Never share OAuth tokens publicly.
          </p>
          <div className="flex gap-4 pt-2">
            <a
              className="text-sky-300 text-xs hover:underline"
              href="https://developers.google.com/youtube/v3/guides/authentication"
              target="_blank"
              rel="noreferrer"
            >
              Official YouTube OAuth Guide ↗
            </a>
            <a
              className="text-sky-300 text-xs hover:underline"
              href="https://studio.youtube.com"
              target="_blank"
              rel="noreferrer"
            >
              Open YouTube Studio ↗
            </a>
          </div>
        </div>
      </details>

      {/* Review Sensitivity */}
      <section className="card space-y-5 p-6">
        <div className="section-heading">
          <div>
            <span className="eyebrow">REVIEW SENSITIVITY</span>
            <h2 className="text-xl font-medium mt-1">Classification Sensitivity</h2>
            <p className="text-sm text-slate-400">
              Adjust thresholds for flagging comments for human review in video and live analysis.
            </p>
          </div>
        </div>

        <label className="block text-sm">
          High-confidence risk threshold: <strong>{high.toFixed(2)}</strong>
          <input
            className="w-full mt-3"
            type="range"
            min={0.5}
            max={0.99}
            step={0.01}
            value={high}
            onChange={(e) => setHigh(Number(e.target.value))}
          />
        </label>

        <label className="block text-sm">
          Review threshold: <strong>{low.toFixed(2)}</strong>
          <input
            className="w-full mt-3"
            type="range"
            min={0.2}
            max={0.8}
            step={0.01}
            value={low}
            onChange={(e) => setLow(Number(e.target.value))}
          />
        </label>

        {low >= high && (
          <p className="notice-error">Review threshold must be lower than high confidence threshold.</p>
        )}

        <button
          className="btn"
          disabled={busy || !data || low >= high}
          onClick={saveThresholds}
        >
          Save Review Preferences
        </button>
      </section>
    </div>
  );
}
