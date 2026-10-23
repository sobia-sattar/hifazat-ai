import { useState, useEffect } from "react";
import { apiUrl } from "../services/api";

interface Message {
  id: string;
  sender: "user" | "assistant";
  text: string;
  source?: string;
  isCrisis?: boolean;
}

export default function SafetyAssistant() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "initial",
      sender: "assistant",
      text: "Hello. I am the HIFAZAT AI Digital Safety Assistant (حفاظت AI). I can help guide you on evidence collection, platform reporting steps, de-escalation tactics, and personal digital wellbeing. How can I support you today?",
      source: "static_curated",
    },
  ]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [crisisList, setCrisisList] = useState<any[]>([]);

  useEffect(() => {
    fetch(apiUrl("/assistant/crisis-resources"))
      .then((r) => r.json())
      .then((d) => setCrisisList(d.resources || []))
      .catch(() => {});
  }, []);

  async function send(queryText?: string) {
    const textToSend = (queryText || input).trim();
    if (!textToSend || busy) return;

    setError("");
    const userMsg: Message = {
      id: Date.now().toString(),
      sender: "user",
      text: textToSend,
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setBusy(true);

    try {
      const res = await fetch(apiUrl("/assistant/chat"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: textToSend }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Unable to reach assistant.");
      }

      const botMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: "assistant",
        text: data.reply,
        source: data.source,
        isCrisis: data.is_crisis,
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <header className="page-heading">
        <span className="eyebrow">HIFAZAT AI (حفاظت AI) · DIGITAL WELLBEING</span>
        <h1>AI Cyber Safety Assistant</h1>
        <p>
          Practical, supportive guidance on navigating online harassment, preserving evidence, and digital safety.
        </p>
      </header>

      {/* Required Disclaimer Notice */}
      <div className="notice" role="note">
        <strong>Important Notice:</strong> AI assistant guidance — not a prediction from the detection model and not a substitute for human help.
        If you or someone else is in immediate physical danger, contact emergency services directly.
      </div>

      {/* Quick Prompts Bar */}
      <div className="flex flex-wrap gap-2 text-xs">
        <span className="text-slate-400 py-1">Quick guidance topics:</span>
        <button
          className="px-2.5 py-1 rounded bg-slate-900 border border-slate-700 hover:border-sky-400 text-slate-300 transition"
          onClick={() => send("How do I properly preserve screenshots and evidence of harassment?")}
        >
          Preserving Evidence
        </button>
        <button
          className="px-2.5 py-1 rounded bg-slate-900 border border-slate-700 hover:border-sky-400 text-slate-300 transition"
          onClick={() => send("Someone is sending abusive messages. How should I de-escalate?")}
        >
          De-escalation Advice
        </button>
        <button
          className="px-2.5 py-1 rounded bg-slate-900 border border-slate-700 hover:border-sky-400 text-slate-300 transition"
          onClick={() => send("Where and how can I file an official cyberbullying complaint in Pakistan?")}
        >
          Reporting Procedures
        </button>
      </div>

      {/* Chat Display Box */}
      <section className="card p-5 space-y-4">
        <div className="min-h-72 max-h-[30rem] overflow-y-auto space-y-3.5 pr-2">
          {messages.map((m) => (
            <div
              key={m.id}
              className={`flex flex-col ${
                m.sender === "user" ? "items-end" : "items-start"
              }`}
            >
              <div
                className={`max-w-[85%] rounded-lg p-4 text-sm leading-relaxed whitespace-pre-wrap ${
                  m.sender === "user"
                    ? "bg-sky-600 text-white"
                    : m.isCrisis
                    ? "bg-rose-950/80 border border-rose-500 text-rose-100"
                    : "bg-slate-900/90 border border-slate-800 text-slate-200"
                }`}
              >
                {m.text}
              </div>
              <span className="text-[10px] text-slate-500 mt-1 px-1">
                {m.sender === "user"
                  ? "You"
                  : m.source === "gemini"
                  ? "AI Assistant (Gemini)"
                  : m.source === "openai"
                  ? "AI Assistant (OpenAI)"
                  : "Curated Safety Guidance (Offline)"}
              </span>
            </div>
          ))}
          {busy && (
            <div className="flex items-center gap-2 text-xs text-slate-400 p-2">
              <span className="animate-spin inline-block">⌁</span> Formulating guidance…
            </div>
          )}
        </div>

        {error && <p role="alert" className="notice-error">{error}</p>}

        <form
          className="flex gap-2 pt-2 border-t border-line"
          onSubmit={(e) => {
            e.preventDefault();
            send();
          }}
        >
          <input
            className="input flex-1"
            placeholder="Ask about digital safety, reporting steps, or evidence preservation..."
            maxLength={1000}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={busy}
          />
          <button className="btn" disabled={busy || !input.trim()}>
            Send ↗
          </button>
        </form>
      </section>

      {/* Emergency Crisis Helpline Accordion */}
      {crisisList.length > 0 && (
        <details className="card p-5">
          <summary className="font-semibold text-rose-300 cursor-pointer">
            Emergency Crisis Helplines & Support Contacts
          </summary>
          <div className="grid gap-3 sm:grid-cols-2 mt-4">
            {crisisList.map((c: any, i: number) => (
              <div key={i} className="p-3.5 rounded bg-slate-950 border border-slate-800 text-xs space-y-1">
                <span className="font-bold text-slate-200 block">{c.region}</span>
                <span className="font-mono text-sky-300 block">{c.helpline}</span>
                <p className="text-slate-400">{c.description}</p>
                <small className="text-slate-500 italic block">{c.confirmation_status}</small>
              </div>
            ))}
          </div>
        </details>
      )}
    </div>
  );
}
