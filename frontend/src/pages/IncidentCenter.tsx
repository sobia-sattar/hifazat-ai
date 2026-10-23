import { useState, useEffect } from "react";
import { apiUrl } from "../services/api";
import IncidentReportModal from "../components/IncidentReportModal";

const STATUS_CONFIG: Record<
  string,
  { label: string; color: string; badgeClass: string; desc: string }
> = {
  submitted: {
    label: "Pending Review",
    color: "#94a3b8",
    badgeClass: "bg-slate-800 text-slate-300 border-slate-700",
    desc: "Report received and waiting for reviewer intake.",
  },
  in_review: {
    label: "Under Review",
    color: "#38bdf8",
    badgeClass: "bg-sky-500/20 text-sky-300 border-sky-500/30",
    desc: "A safety reviewer is actively examining this incident.",
  },
  needs_info: {
    label: "Needs Details",
    color: "#f59e0b",
    badgeClass: "bg-amber-500/20 text-amber-300 border-amber-500/30",
    desc: "Additional proof, link, or context is required.",
  },
  actioned: {
    label: "Resolved",
    color: "#10b981",
    badgeClass: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
    desc: "Safety action completed or content dealt with.",
  },
  escalated: {
    label: "Escalated",
    color: "#f43f5e",
    badgeClass: "bg-rose-500/20 text-rose-300 border-rose-500/30",
    desc: "Escalated for immediate moderator or platform attention.",
  },
  dismissed: {
    label: "Dismissed",
    color: "#64748b",
    badgeClass: "bg-slate-800 text-slate-400 border-slate-700",
    desc: "Reviewed and closed without further action.",
  },
};

export default function IncidentCenter() {
  const [tab, setTab] = useState<"queue" | "my">("queue");
  const [queue, setQueue] = useState<any[]>([]);
  const [myReports, setMyReports] = useState<any[]>([]);
  const [statusFilter, setStatusFilter] = useState("all");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [showModal, setShowModal] = useState(false);

  // Status update modal state
  const [selectedReport, setSelectedReport] = useState<any>(null);
  const [newStatus, setNewStatus] = useState("in_review");
  const [statusNotes, setStatusNotes] = useState("");

  const reporterToken =
    localStorage.getItem("hifazat_reporter_token") ||
    localStorage.getItem("bullylens_reporter_token") ||
    "";

  async function loadData() {
    setBusy(true);
    setError("");
    try {
      const qRes = await fetch(
        apiUrl(`/incidents/queue${statusFilter !== "all" ? `?status=${statusFilter}` : ""}`)
      );
      if (qRes.ok) setQueue(await qRes.json());

      if (reporterToken) {
        const mRes = await fetch(apiUrl("/incidents/my"), {
          headers: { "X-Reporter-Token": reporterToken },
        });
        if (mRes.ok) setMyReports(await mRes.json());
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    loadData();
  }, [statusFilter]);

  async function updateStatus() {
    if (!selectedReport) return;
    setBusy(true);
    setError("");
    try {
      const res = await fetch(apiUrl(`/incidents/${selectedReport.id}/status`), {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus, notes: statusNotes }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to update status.");
      setNotice(`Report #${selectedReport.id} status updated to ${STATUS_CONFIG[newStatus]?.label || newStatus}.`);
      setSelectedReport(null);
      setStatusNotes("");
      loadData();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function deleteMyReport(id: number) {
    if (!confirm("Are you sure you want to permanently delete this report?")) return;
    setBusy(true);
    try {
      const res = await fetch(apiUrl(`/incidents/${id}`), {
        method: "DELETE",
        headers: { "X-Reporter-Token": reporterToken },
      });
      if (!res.ok) throw new Error("Failed to delete report.");
      setNotice("Your incident report was deleted.");
      loadData();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Friendly Header */}
      <header className="page-heading">
        <span className="eyebrow flex items-center gap-2">
          <span>DIGITAL SAFETY</span>
          <span className="text-slate-500">·</span>
          <span>EVIDENCE LOG</span>
        </span>
        <h1 className="text-3xl font-bold tracking-tight">Incident Center</h1>
        <p className="text-slate-400 max-w-2xl text-sm leading-relaxed">
          A confidential, safe space to report and track online harassment, cyberbullying, or threatening messages.
        </p>
      </header>

      {/* "What is this section about?" Card */}
      <section className="card p-5 bg-gradient-to-br from-slate-900/90 to-sky-950/20 border border-sky-500/20 space-y-4">
        <div className="flex items-center gap-2">
          <span className="text-lg">💡</span>
          <h2 className="text-base font-semibold text-slate-100">
            What is this section about?
          </h2>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed">
          When you or someone else faces abusive comments, threats, or harassment online, saving evidence is the most important first step. 
          The <strong>Incident Center</strong> allows you to log the message, preserve links, and track the status of the report.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2 border-t border-slate-800">
          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
            <span className="text-sky-400 font-mono text-xs font-bold block">1. Save Evidence</span>
            <p className="text-xs text-slate-400">
              Paste the abusive text, username, and the link to keep a permanent timestamped record.
            </p>
          </div>
          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
            <span className="text-sky-400 font-mono text-xs font-bold block">2. Completely Private</span>
            <p className="text-xs text-slate-400">
              Stored securely with a private key on your device. No public account or sign-up required.
            </p>
          </div>
          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
            <span className="text-sky-400 font-mono text-xs font-bold block">3. Track Progress</span>
            <p className="text-xs text-slate-400">
              Check whether the report is pending review, being investigated, or marked resolved.
            </p>
          </div>
        </div>
      </section>

      {/* Action Bar & Tabs */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
        <div className="segmented">
          <button
            className={tab === "queue" ? "active" : ""}
            onClick={() => setTab("queue")}
          >
            All Reported Incidents ({queue.length})
          </button>
          <button
            className={tab === "my" ? "active" : ""}
            onClick={() => setTab("my")}
          >
            My Saved Reports ({myReports.length})
          </button>
        </div>

        <div className="flex items-center gap-2">
          <button
            className="btn flex items-center gap-1.5"
            onClick={() => setShowModal(true)}
          >
            <span>+</span>
            <span>Report an Incident</span>
          </button>
          <button
            className="btn-ghost"
            disabled={busy}
            onClick={loadData}
            title="Refresh list"
          >
            Refresh ↻
          </button>
        </div>
      </div>

      {error && <p role="alert" className="notice-error">{error}</p>}
      {notice && <p role="status" className="notice">{notice}</p>}

      {/* TAB 1: ALL INCIDENTS QUEUE */}
      {tab === "queue" && (
        <section className="space-y-4">
          <div className="flex items-center gap-3">
            <label htmlFor="filter-select" className="text-xs text-slate-400">
              Filter by status:
            </label>
            <select
              id="filter-select"
              className="input text-xs py-1"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="all">All Statuses ({queue.length})</option>
              <option value="submitted">Pending Review</option>
              <option value="in_review">Under Review</option>
              <option value="needs_info">Needs Details</option>
              <option value="actioned">Resolved</option>
              <option value="escalated">Escalated</option>
              <option value="dismissed">Dismissed</option>
            </select>
          </div>

          {queue.length === 0 ? (
            <div className="card empty-state p-8 text-center text-slate-400 space-y-3">
              <p className="text-base font-medium">No incidents logged yet.</p>
              <p className="text-xs text-slate-500">
                Click "+ Report an Incident" above to document your first case of online harassment or threat.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {queue.map((r: any) => {
                const conf = STATUS_CONFIG[r.status] || STATUS_CONFIG.submitted;
                return (
                  <article key={r.id} className="card p-5 space-y-3">
                    <div className="flex flex-wrap justify-between items-start gap-3">
                      <div>
                        <div className="flex items-center gap-2 text-xs">
                          <span className="font-mono text-slate-400">Case #{r.id}</span>
                          <span className="px-2 py-0.5 rounded bg-sky-950/80 border border-sky-500/30 text-sky-300 uppercase font-semibold text-[10px]">
                            {r.platform}
                          </span>
                          <span className="text-slate-500">·</span>
                          <span className="text-slate-400">{r.created_at}</span>
                        </div>

                        {/* Incident Text */}
                        <div className="mt-2 p-3 rounded-lg bg-slate-950/80 border-l-2 border-sky-400">
                          <p className="text-sm text-slate-100 font-medium" dir="auto">
                            "{r.incident_text}"
                          </p>
                        </div>

                        {r.evidence_url && (
                          <p className="text-xs text-sky-400 mt-2 truncate flex items-center gap-1">
                            <span className="text-slate-500">Evidence Link:</span>
                            <span className="font-mono">{r.evidence_url}</span>
                          </p>
                        )}
                        {r.reporter_notes && (
                          <p className="text-xs text-slate-400 mt-1 italic">
                            Context: {r.reporter_notes}
                          </p>
                        )}
                      </div>

                      {/* Status Badge */}
                      <span
                        className={`text-xs px-2.5 py-1 rounded border font-semibold ${conf.badgeClass}`}
                        title={conf.desc}
                      >
                        {conf.label}
                      </span>
                    </div>

                    {/* Action Row */}
                    <div className="flex items-center justify-between pt-2 border-t border-line text-xs">
                      <span className="text-slate-500">
                        {conf.desc}
                      </span>
                      <button
                        className="btn-ghost text-xs py-1"
                        onClick={() => {
                          setSelectedReport(r);
                          setNewStatus(r.status);
                        }}
                      >
                        Change Status ⚙
                      </button>
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </section>
      )}

      {/* TAB 2: MY SUBMITTED REPORTS */}
      {tab === "my" && (
        <section className="space-y-4">
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-400">
            ℹ️ These reports were submitted from this browser. You can track their status or permanently delete them at any time.
          </div>

          {myReports.length === 0 ? (
            <div className="card empty-state p-8 text-center text-slate-400 space-y-2">
              <p className="text-base font-medium">You haven't submitted any reports from this device yet.</p>
              <p className="text-xs text-slate-500">
                Any reports you submit using "+ Report an Incident" will appear here automatically.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {myReports.map((r: any) => {
                const conf = STATUS_CONFIG[r.status] || STATUS_CONFIG.submitted;
                return (
                  <article key={r.id} className="card p-5 space-y-3">
                    <div className="flex flex-wrap justify-between items-start gap-3">
                      <div>
                        <div className="flex items-center gap-2 text-xs">
                          <span className="font-mono text-slate-400">Case #{r.id}</span>
                          <span className="px-2 py-0.5 rounded bg-sky-950/80 border border-sky-500/30 text-sky-300 uppercase font-semibold text-[10px]">
                            {r.platform}
                          </span>
                          <span className="text-slate-500">·</span>
                          <span className="text-slate-400">{r.created_at}</span>
                        </div>
                        <div className="mt-2 p-3 rounded-lg bg-slate-950/80 border-l-2 border-sky-400">
                          <p className="text-sm text-slate-100 font-medium" dir="auto">
                            "{r.incident_text}"
                          </p>
                        </div>
                        {r.evidence_url && (
                          <p className="text-xs text-sky-400 mt-2 truncate">
                            Evidence Link: {r.evidence_url}
                          </p>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`text-xs px-2.5 py-1 rounded border font-semibold ${conf.badgeClass}`}>
                          {conf.label}
                        </span>
                        <button
                          className="btn-ghost text-xs text-rose-400 hover:text-rose-300 py-1"
                          onClick={() => deleteMyReport(r.id)}
                        >
                          Delete ✕
                        </button>
                      </div>
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </section>
      )}

      {/* Simple Status Update Modal */}
      {selectedReport && (
        <div className="modal-backdrop">
          <section
            role="dialog"
            aria-modal="true"
            className="card modal-panel max-w-lg w-full p-6 space-y-4"
          >
            <div className="flex justify-between items-center border-b border-line pb-2">
              <h2 className="text-lg font-bold">
                Update Case #{selectedReport.id} Status
              </h2>
              <button
                className="btn-ghost text-xs"
                onClick={() => setSelectedReport(null)}
              >
                ✕
              </button>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">
                Current Status
              </label>
              <select
                className="input w-full text-sm"
                value={newStatus}
                onChange={(e) => setNewStatus(e.target.value)}
              >
                <option value="submitted">Pending Review (Waiting for review)</option>
                <option value="in_review">Under Review (Actively examining)</option>
                <option value="needs_info">Needs Details (Awaiting more evidence)</option>
                <option value="actioned">Resolved (Action taken / Content dealt with)</option>
                <option value="escalated">Escalated (Sent for urgent attention)</option>
                <option value="dismissed">Dismissed (No violation found)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">
                Reason / Status Notes *
              </label>
              <textarea
                className="input w-full min-h-20 text-sm"
                required
                placeholder="e.g., Reviewed comment, reported to platform, or marked resolved..."
                value={statusNotes}
                onChange={(e) => setStatusNotes(e.target.value)}
              />
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-line">
              <button
                className="btn-ghost"
                onClick={() => setSelectedReport(null)}
              >
                Cancel
              </button>
              <button
                className="btn"
                disabled={busy || !statusNotes.trim()}
                onClick={updateStatus}
              >
                {busy ? "Updating…" : "Save Status ↗"}
              </button>
            </div>
          </section>
        </div>
      )}

      {/* Log New Incident Modal */}
      {showModal && (
        <IncidentReportModal
          onClose={() => setShowModal(false)}
          onSuccess={loadData}
        />
      )}
    </div>
  );
}
