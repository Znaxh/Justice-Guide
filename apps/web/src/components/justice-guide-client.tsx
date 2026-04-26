"use client";

import {
  type FormEvent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { type Citation, type StreamDoneMetadata, streamAsk } from "@/lib/api";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  bnsNotes?: string[];
  disclaimer?: string;
  llmUsed?: string;
  isStreaming?: boolean;
  error?: string;
  phase?: string;
}

const EXAMPLE_QUESTIONS = [
  "What is IPC section 302?",
  "Difference between IPC 299 and IPC 300?",
  "What is punishment for theft under IPC?",
  "What is criminal breach of trust?",
  "How is unlawful assembly defined in IPC?",
  "What is IPC section 420?",
];

const PHASE_LABELS: Record<string, string> = {
  enhancing: "Analysing your question",
  retrieving: "Searching legal documents",
  generating: "Generating answer",
};

export function JusticeGuideClient() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [query, setQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const saved = localStorage.getItem("jg-theme");
    if (saved === "light" || saved === "dark") setTheme(saved);
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("jg-theme", theme);
  }, [theme]);

  const scrollToBottom = useCallback(() => {
    requestAnimationFrame(() => {
      scrollRef.current?.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: "smooth",
      });
    });
  }, []);

  useEffect(scrollToBottom, [messages, scrollToBottom]);

  const canSubmit = useMemo(
    () => query.trim().length > 0 && !isLoading,
    [query, isLoading]
  );

  function updateLastAssistant(
    updater: (prev: Message) => Partial<Message>
  ) {
    setMessages((prev) => {
      const idx = prev.length - 1;
      if (idx < 0 || prev[idx].role !== "assistant") return prev;
      const updated = { ...prev[idx], ...updater(prev[idx]) };
      return [...prev.slice(0, idx), updated];
    });
  }

  async function handleSubmit(e?: FormEvent) {
    e?.preventDefault();
    if (!canSubmit) return;

    const userQuery = query.trim();
    setQuery("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: userQuery,
    };
    const assistantMsg: Message = {
      id: crypto.randomUUID(),
      role: "assistant",
      content: "",
      isStreaming: true,
      phase: "enhancing",
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setIsLoading(true);

    try {
      await streamAsk({
        query: userQuery,
        sessionId,
        onStatus(phase) {
          updateLastAssistant(() => ({ phase }));
        },
        onToken(text) {
          updateLastAssistant((prev) => ({
            content: prev.content + text,
            phase: undefined,
          }));
        },
        onCitations(citations, bnsNotes) {
          updateLastAssistant(() => ({ citations, bnsNotes }));
        },
        onDone(metadata: StreamDoneMetadata) {
          if (metadata.session_id) setSessionId(metadata.session_id);
          updateLastAssistant(() => ({
            isStreaming: false,
            disclaimer: metadata.disclaimer,
            llmUsed: metadata.llm_used,
          }));
        },
        onError(message) {
          updateLastAssistant((prev) => ({
            isStreaming: false,
            error: message,
            content: prev.content || "",
          }));
        },
      });
    } catch {
      updateLastAssistant((prev) => ({
        isStreaming: false,
        error: "Network error — check your connection and try again.",
        content: prev.content || "",
      }));
    } finally {
      setIsLoading(false);
    }
  }

  function handleRetry(msgId: string) {
    const idx = messages.findIndex((m) => m.id === msgId);
    if (idx < 1) return;
    const userMsg = messages[idx - 1];
    if (userMsg.role !== "user") return;

    setMessages((prev) => prev.slice(0, idx - 1));
    setQuery(userMsg.content);
    setTimeout(() => {
      setQuery(userMsg.content);
      handleSubmit();
    }, 50);
  }

  function handleNewChat() {
    setMessages([]);
    setSessionId(null);
    setQuery("");
    textareaRef.current?.focus();
  }

  function handleCopy(id: string, content: string) {
    navigator.clipboard.writeText(content).then(() => {
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    });
  }

  function handleExampleClick(q: string) {
    setQuery(q);
    textareaRef.current?.focus();
  }

  function autoResize(el: HTMLTextAreaElement) {
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 120) + "px";
  }

  return (
    <div className="app-shell">
      {/* ---- Header ---- */}
      <header className="app-header">
        <h1>JusticeGuide</h1>
        <div className="header-actions">
          {messages.length > 0 && (
            <button onClick={handleNewChat} className="btn-ghost">
              New Chat
            </button>
          )}
          <button
            onClick={() => setTheme((t) => (t === "dark" ? "light" : "dark"))}
            className="btn-ghost"
            title="Toggle theme"
          >
            {theme === "dark" ? "Light" : "Dark"}
          </button>
        </div>
      </header>

      {/* ---- Conversation ---- */}
      <div className="conversation-area" ref={scrollRef}>
        {messages.length === 0 ? (
          <div className="empty-state">
            <h2>Ask about Indian Penal Code</h2>
            <p className="subtitle">
              Get answers with citations from IPC legal text, now with BNS
              (Bharatiya Nyaya Sanhita) equivalents.
            </p>
            <div className="example-list">
              {EXAMPLE_QUESTIONS.map((q) => (
                <button
                  key={q}
                  onClick={() => handleExampleClick(q)}
                  className="example-chip"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="messages">
            {messages.map((msg) => (
              <div key={msg.id} className={`message message-${msg.role}`}>
                {msg.role === "user" ? (
                  <div className="user-bubble">{msg.content}</div>
                ) : (
                  <AssistantMessage
                    msg={msg}
                    copiedId={copiedId}
                    onCopy={handleCopy}
                    onRetry={handleRetry}
                  />
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ---- Input ---- */}
      <form onSubmit={handleSubmit} className="input-area">
        <textarea
          ref={textareaRef}
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            autoResize(e.target);
          }}
          placeholder="Ask about any IPC section..."
          rows={1}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              if (canSubmit) handleSubmit();
            }
          }}
        />
        <button type="submit" disabled={!canSubmit} className="btn-send">
          {isLoading ? "..." : "Send"}
        </button>
      </form>
    </div>
  );
}

/* ==================================================================
 * AssistantMessage — renders answer, citations, BNS notes, actions
 * ================================================================== */

function AssistantMessage({
  msg,
  copiedId,
  onCopy,
  onRetry,
}: {
  msg: Message;
  copiedId: string | null;
  onCopy: (id: string, content: string) => void;
  onRetry: (id: string) => void;
}) {
  return (
    <div className="assistant-bubble">
      {/* Phase indicator (skeleton) */}
      {msg.isStreaming && !msg.content && msg.phase && (
        <div className="status-indicator">
          <div className="dot-pulse">
            <span />
            <span />
            <span />
          </div>
          {PHASE_LABELS[msg.phase] || msg.phase}
        </div>
      )}

      {/* Error */}
      {msg.error && (
        <p className="error-text">
          {msg.error}
          <button onClick={() => onRetry(msg.id)}>Retry</button>
        </p>
      )}

      {/* Answer content */}
      {msg.content && (
        <div className="answer-content">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {msg.content}
          </ReactMarkdown>
          {msg.isStreaming && <span className="cursor-blink">|</span>}
        </div>
      )}

      {/* Citations */}
      {msg.citations && msg.citations.length > 0 && (
        <details className="citations-section">
          <summary>
            Citations ({msg.citations.length})
          </summary>
          <ul>
            {msg.citations.map((c) => (
              <li key={`${c.citation_id}-${c.source_file}`}>
                <strong>[{c.citation_id}]</strong> {c.source_file}{" "}
                (p.&nbsp;{c.page}) &mdash;{" "}
                {c.text.length > 250
                  ? c.text.slice(0, 250) + "..."
                  : c.text}
              </li>
            ))}
          </ul>
        </details>
      )}

      {/* BNS equivalents */}
      {msg.bnsNotes && msg.bnsNotes.length > 0 && (
        <div className="bns-notes">
          <div className="bns-title">
            BNS Equivalents (effective 1 July 2024)
          </div>
          <ul>
            {msg.bnsNotes.map((note, i) => (
              <li key={i}>{note}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Actions: copy + disclaimer */}
      {!msg.isStreaming && msg.content && (
        <div className="message-actions">
          <button
            className={`btn-icon ${copiedId === msg.id ? "copied" : ""}`}
            onClick={() => onCopy(msg.id, msg.content)}
          >
            {copiedId === msg.id ? "Copied!" : "Copy"}
          </button>
          {msg.disclaimer && (
            <span className="disclaimer">{msg.disclaimer}</span>
          )}
        </div>
      )}
    </div>
  );
}
