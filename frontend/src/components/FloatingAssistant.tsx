import { useState, useEffect, useRef } from "react";
import { useLocation } from "react-router-dom";
import { apiUrl } from "../services/api";

interface Message {
  id: string;
  sender: "user" | "assistant";
  text: string;
  source?: string;
  isCrisis?: boolean;
  timestamp: string;
}

const INITIAL_WELCOME: Message = {
  id: "init",
  sender: "assistant",
  text: "Hello! I am your HIFAZAT AI Cyber Guardian (حفاظت AI). I'm here to help you identify online threats, analyze suspicious messages, understand detection scores, and improve your digital safety. How can I protect you today?",
  source: "static_curated",
  timestamp: "Just now",
};

const QUICK_ACTIONS = [
  { label: "Explain Detection", query: "Can you explain how HIFAZAT AI detects harmful content and what model scores mean?" },
  { label: "Cyber Safety Tips", query: "What are the best immediate safety steps if someone is targeting me online?" },
  { label: "Analyze Scam Signs", query: "What warning signs should I look for in suspicious or phishing messages?" },
  { label: "How to Report Abuse", query: "How do I preserve evidence and file an official report for online harassment?" },
];

export default function FloatingAssistant() {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([INITIAL_WELCOME]);
  const [busy, setBusy] = useState(false);
  const [hasNewPagePulse, setHasNewPagePulse] = useState(false);
  const [crisisList, setCrisisList] = useState<any[]>([]);

  const location = useLocation();
  const chatScrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Trigger subtle beacon pulse when route changes without popping the window open
  useEffect(() => {
    setHasNewPagePulse(true);
    const t = setTimeout(() => setHasNewPagePulse(false), 2200);
    return () => clearTimeout(t);
  }, [location.pathname]);

  // Load crisis resources once
  useEffect(() => {
    fetch(apiUrl("/assistant/crisis-resources"))
      .then((r) => r.json())
      .then((d) => setCrisisList(d.resources || []))
      .catch(() => {});
  }, []);

  // Auto-scroll chat to bottom
  useEffect(() => {
    if (isOpen && chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight;
    }
  }, [messages, isOpen, busy]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 150);
    }
  }, [isOpen]);

  // Close on Escape key
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape" && isOpen) {
        setIsOpen(false);
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen]);

  async function handleSend(customText?: string) {
    const textToSend = (customText || input).trim();
    if (!textToSend || busy) return;

    const timeStr = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    const userMsg: Message = {
      id: Date.now().toString(),
      sender: "user",
      text: textToSend,
      timestamp: timeStr,
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
        throw new Error(data.detail || "Unable to reach safety assistant.");
      }

      const botMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: "assistant",
        text: data.reply,
        source: data.source,
        isCrisis: data.is_crisis,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (e: any) {
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: "assistant",
        text: `Notice: ${e.message || "Unable to retrieve response. Check connection."}`,
        source: "error",
        timestamp: timeStr,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setBusy(false);
    }
  }

  function handleReset() {
    setMessages([INITIAL_WELCOME]);
  }

  return (
    <>
      {/* Floating Avatar Trigger Button */}
      <div className="fixed bottom-6 right-6 z-[9990] flex items-center">
        {/* Subtle unread/page change helper pill */}
        {!isOpen && hasNewPagePulse && (
          <div
            className="mr-3 px-3 py-1.5 rounded-full text-xs font-medium text-sky-200 bg-slate-900/90 border border-sky-400/40 shadow-lg pointer-events-none transition-all duration-300 animate-fade-in"
            role="status"
          >
            <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 mr-2 shadow-[0_0_8px_#38dea9]" />
            Cyber Guardian Active
          </div>
        )}

        <button
          type="button"
          aria-label={isOpen ? "Close Cyber Safety AI Assistant" : "Open Cyber Safety AI Assistant"}
          aria-expanded={isOpen}
          onClick={() => setIsOpen(!isOpen)}
          className={`relative group flex items-center justify-center w-14 h-14 rounded-full transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-sky-400/80 ${
            isOpen
              ? "bg-slate-900 border-2 border-sky-400 shadow-[0_0_25px_rgba(140,207,255,0.45)] scale-95"
              : "bg-slate-950 border-2 border-sky-400/70 shadow-[0_0_20px_rgba(56,222,169,0.35),0_0_12px_rgba(140,207,255,0.3)] hover:scale-110 hover:border-sky-300"
          }`}
          style={{
            animation: !isOpen ? "guardian-float 4.5s ease-in-out infinite" : "none",
          }}
        >
          {/* Animated Ambient Ring */}
          <span
            className={`absolute -inset-1 rounded-full pointer-events-none transition-opacity duration-300 ${
              hasNewPagePulse ? "opacity-100 ring-2 ring-emerald-400/60 animate-ping" : "opacity-0"
            }`}
          />

          {/* Guardian SVG Icon */}
          <svg
            className="w-8 h-8 text-sky-200 transition-transform duration-300 group-hover:rotate-3"
            viewBox="0 0 100 100"
            fill="none"
            aria-hidden="true"
          >
            <defs>
              <linearGradient id="guardian-shield" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#8ccfff" />
                <stop offset="100%" stopColor="#38dea9" />
              </linearGradient>
              <linearGradient id="guardian-core" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="#0a2342" />
                <stop offset="100%" stopColor="#040c1b" />
              </linearGradient>
            </defs>

            {/* Futuristic Shield Helmet */}
            <path
              d="M50 10 L82 24 C82 58 66 80 50 90 C34 80 18 58 18 24 Z"
              fill="url(#guardian-core)"
              stroke="url(#guardian-shield)"
              strokeWidth="4"
              strokeLinejoin="round"
            />

            {/* Cyber Visor / Eyes */}
            <path
              d="M32 42 Q50 36 68 42 Q50 48 32 42 Z"
              fill="#caeaff"
              opacity="0.95"
            />
            <circle cx="43" cy="42" r="3.5" fill="#040c1b" />
            <circle cx="57" cy="42" r="3.5" fill="#040c1b" />

            {/* Neural Crest Line */}
            <line x1="50" y1="20" x2="50" y2="34" stroke="#8ccfff" strokeWidth="3" strokeLinecap="round" />
            <circle cx="50" cy="18" r="2.5" fill="#38dea9" />
          </svg>

          {/* Status Light Beacon */}
          <span
            className="absolute top-0 right-0 w-3.5 h-3.5 rounded-full bg-emerald-400 border-2 border-slate-950 shadow-[0_0_8px_#38dea9]"
            title="Guardian Online"
          />
        </button>
      </div>

      {/* Modern Pop-Up Chat Panel Overlay */}
      {isOpen && (
        <section
          role="dialog"
          aria-modal="true"
          aria-labelledby="guardian-chat-title"
          className="fixed bottom-[86px] right-4 sm:right-6 w-[calc(100vw-32px)] sm:w-[400px] h-[min(600px,80vh)] z-[9995] flex flex-col rounded-2xl bg-slate-950/95 border border-sky-400/30 backdrop-blur-xl shadow-[0_20px_60px_rgba(0,0,0,0.7),0_0_35px_rgba(56,222,169,0.15)] animate-panel-rise overflow-hidden"
        >
          {/* Header */}
          <header className="flex items-center justify-between px-4 py-3.5 border-b border-sky-400/20 bg-gradient-to-r from-slate-900/90 via-slate-900/60 to-slate-950">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-full bg-slate-900 border border-sky-400/40 flex items-center justify-center text-sky-300">
                <svg className="w-5 h-5" viewBox="0 0 100 100" fill="none">
                  <path
                    d="M50 12 L80 25 C80 56 65 76 50 86 C35 76 20 56 20 25 Z"
                    fill="#081b33"
                    stroke="#8ccfff"
                    strokeWidth="5"
                  />
                  <path d="M34 42 Q50 36 66 42 Q50 48 34 42 Z" fill="#caeaff" />
                </svg>
              </div>
              <div>
                <h2 id="guardian-chat-title" className="text-sm font-semibold text-slate-100 flex items-center gap-1.5">
                  HIFAZAT AI Guardian
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_6px_#38dea9]" />
                </h2>
                <p className="text-[10px] text-sky-300/80">Digital Safety Assistant · حفاظت AI</p>
              </div>
            </div>

            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={handleReset}
                title="Start new conversation"
                className="px-2 py-1 text-xs rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 transition"
              >
                ↻ Clear
              </button>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                title="Close chat"
                className="w-7 h-7 rounded flex items-center justify-center text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
              >
                ✕
              </button>
            </div>
          </header>

          {/* Quick Actions Scroll Bar */}
          <div className="flex gap-1.5 px-3 py-2 border-b border-slate-800/80 bg-slate-950/60 overflow-x-auto text-xs no-scrollbar">
            {QUICK_ACTIONS.map((action, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleSend(action.query)}
                disabled={busy}
                className="px-2.5 py-1 rounded-full whitespace-nowrap bg-slate-900 border border-slate-800 text-sky-300/90 hover:border-sky-400 hover:bg-slate-800/70 transition disabled:opacity-40"
              >
                {action.label}
              </button>
            ))}
          </div>

          {/* Message Thread Area */}
          <div
            ref={chatScrollRef}
            className="flex-1 overflow-y-auto p-4 space-y-3 text-xs leading-relaxed"
          >
            {messages.map((m) => (
              <div
                key={m.id}
                className={`flex flex-col ${m.sender === "user" ? "items-end" : "items-start"}`}
              >
                <div
                  className={`max-w-[88%] rounded-xl p-3 whitespace-pre-wrap ${
                    m.sender === "user"
                      ? "bg-sky-600 text-white rounded-br-none shadow-md"
                      : m.isCrisis
                      ? "bg-rose-950/90 border border-rose-500/70 text-rose-100 rounded-bl-none shadow-[0_0_20px_rgba(244,63,94,0.2)]"
                      : "bg-slate-900/90 border border-slate-800 text-slate-200 rounded-bl-none shadow-sm"
                  }`}
                >
                  {m.text}

                  {/* If crisis detected, show direct hotline links */}
                  {m.isCrisis && crisisList.length > 0 && (
                    <div className="mt-3 pt-2.5 border-t border-rose-500/40 space-y-2">
                      <span className="font-bold text-rose-300 block">Immediate Helplines:</span>
                      {crisisList.slice(0, 2).map((c: any, i: number) => (
                        <div key={i} className="p-2 rounded bg-slate-950/80 border border-rose-500/30">
                          <strong className="block text-slate-200">{c.region}</strong>
                          <span className="font-mono text-rose-300 block">{c.helpline}</span>
                          <span className="text-[10px] text-slate-400">{c.description}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="flex items-center gap-1.5 mt-1 px-1 text-[10px] text-slate-500">
                  <span>{m.timestamp}</span>
                  {m.sender === "assistant" && (
                    <span>
                      · {m.source === "gemini"
                        ? "Gemini AI"
                        : m.source === "openai"
                        ? "OpenAI"
                        : m.source === "crisis_override"
                        ? "Crisis Safety Mode"
                        : "Curated Safety Guidance"}
                    </span>
                  )}
                </div>
              </div>
            ))}

            {busy && (
              <div className="flex items-center gap-2 p-2.5 text-xs text-sky-300/80 bg-slate-900/70 border border-slate-800 rounded-xl w-fit">
                <span className="flex gap-1 items-center">
                  <span className="w-1.5 h-1.5 rounded-full bg-sky-400 animate-bounce" style={{ animationDelay: "0ms" }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-sky-400 animate-bounce" style={{ animationDelay: "150ms" }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-sky-400 animate-bounce" style={{ animationDelay: "300ms" }} />
                </span>
                Formulating safety guidance…
              </div>
            )}
          </div>

          {/* Footer Notice & Input Form */}
          <footer className="p-3 border-t border-slate-800 bg-slate-950/95 space-y-2">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
              className="flex items-center gap-2"
            >
              <input
                ref={inputRef}
                type="text"
                placeholder="Ask about safety, evidence, or scams..."
                maxLength={1000}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={busy}
                className="flex-1 bg-slate-900 border border-slate-700/80 rounded-lg px-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-400 transition"
              />
              <button
                type="submit"
                disabled={busy || !input.trim()}
                className="px-3 py-2 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs disabled:opacity-40 transition shadow-[0_0_12px_rgba(56,189,248,0.3)]"
                title="Send message"
              >
                ↗
              </button>
            </form>

            <p className="text-[10px] text-center text-slate-500 leading-tight">
              AI Cyber Safety Guidance · Not an automated prediction or human crisis service
            </p>
          </footer>
        </section>
      )}

      {/* Custom Styles for Floating Guardian & Animations */}
      <style>{`
        @keyframes guardian-float {
          0%, 100% {
            transform: translateY(0px);
          }
          50% {
            transform: translateY(-8px);
          }
        }
        @keyframes panel-rise {
          from {
            opacity: 0;
            transform: translateY(16px) scale(0.97);
          }
          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }
        .animate-panel-rise {
          animation: panel-rise 0.25s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
        [data-motion="off"] .animate-panel-rise,
        [data-motion="off"] button[style*="guardian-float"] {
          animation: none !important;
          transition: none !important;
        }
        @media (prefers-reduced-motion: reduce) {
          .animate-panel-rise,
          button[style*="guardian-float"] {
            animation: none !important;
            transition: none !important;
          }
        }
        .no-scrollbar::-webkit-scrollbar {
          display: none;
        }
        .no-scrollbar {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
      `}</style>
    </>
  );
}
