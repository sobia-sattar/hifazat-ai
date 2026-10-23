import { useState, useEffect } from "react";
import { apiUrl } from "../services/api";

interface IncidentReportModalProps {
  initialText?: string;
  onClose: () => void;
  onSuccess?: () => void;
}

export default function IncidentReportModal({
  initialText = "",
  onClose,
  onSuccess,
}: IncidentReportModalProps) {
  const [platform, setPlatform] = useState("youtube");
  const [incidentText, setIncidentText] = useState(initialText);
  const [evidenceUrl, setEvidenceUrl] = useState("");
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  // Retrieve or initialize local anonymous reporter token
  const [reporterToken] = useState(() => {
    let t = localStorage.getItem("hifazat_reporter_token") || localStorage.getItem("bullylens_reporter_token");
    if (!t) {
      t = "tok_" + Math.random().toString(36).substring(2) + Date.now().toString(36);
      localStorage.setItem("hifazat_reporter_token", t);
    }
    return t;
  });

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  async function submitReport() {
    if (!incidentText.trim()) return;
    setBusy(true);
    setError("");
    try {
      const res = await fetch(apiUrl("/incidents"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Reporter-Token": reporterToken,
        },
        body: JSON.stringify({
          platform,
          incident_text: incidentText,
          evidence_url: evidenceUrl.trim() || null,
          reporter_notes: notes.trim() || null,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Failed to submit incident report.");
      }
      setSuccessMsg("Incident report logged securely. Status: Submitted.");
      setTimeout(() => {
        if (onSuccess) onSuccess();
        onClose();
      }, 1500);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="modal-backdrop">
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="report-modal-title"
        className="card modal-panel max-w-xl w-full p-6 space-y-4"
      >
        <div className="flex justify-between items-center border-b border-line pb-3">
          <div>
            <span className="eyebrow">DIGITAL SAFETY · EVIDENCE PRESERVATION</span>
            <h2 id="report-modal-title" className="text-xl font-bold">
              Report an Online Incident
            </h2>
          </div>
          <button className="btn-ghost" onClick={onClose} disabled={busy}>
            ✕
          </button>
        </div>

        <p className="text-xs text-slate-400">
          Save abusive comments, threats, or harassment as timestamped evidence. Your report is private and stored securely.
        </p>

        {error && <p role="alert" className="notice-error">{error}</p>}
        {successMsg && <p role="status" className="notice">{successMsg}</p>}

        <div className="space-y-3 text-sm">
          <div>
            <label className="block text-slate-300 font-medium mb-1">Platform</label>
            <select
              className="input w-full"
              value={platform}
              onChange={(e) => setPlatform(e.target.value)}
              disabled={busy}
            >
              <option value="youtube">YouTube</option>
              <option value="twitter">X / Twitter</option>
              <option value="facebook">Facebook</option>
              <option value="instagram">Instagram</option>
              <option value="tiktok">TikTok</option>
              <option value="whatsapp">WhatsApp / Messaging</option>
              <option value="other">Other / Web</option>
            </select>
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">
              Incident or Harassing Content *
            </label>
            <textarea
              className="input w-full min-h-24"
              dir="auto"
              required
              maxLength={4000}
              placeholder="Paste harassing or abusive message..."
              value={incidentText}
              onChange={(e) => setIncidentText(e.target.value)}
              disabled={busy}
            />
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">
              Evidence URL (Optional)
            </label>
            <input
              type="url"
              className="input w-full"
              placeholder="https://platform.com/post/123"
              maxLength={512}
              value={evidenceUrl}
              onChange={(e) => setEvidenceUrl(e.target.value)}
              disabled={busy}
            />
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">
              Additional Context / Notes (Optional)
            </label>
            <textarea
              className="input w-full min-h-16"
              placeholder="Describe what occurred, targeted person, or previous history..."
              maxLength={1000}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              disabled={busy}
            />
          </div>
        </div>

        <div className="flex justify-end gap-2 pt-2 border-t border-line">
          <button className="btn-ghost" onClick={onClose} disabled={busy}>
            Cancel
          </button>
          <button
            className="btn"
            disabled={busy || !incidentText.trim()}
            onClick={submitReport}
          >
            {busy ? "Submitting…" : "Submit Incident Report ↗"}
          </button>
        </div>
      </section>
    </div>
  );
}
