"use client";

import { useMemo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Components } from "react-markdown";

import { type Citation } from "@/lib/api";
import {
  footnoteIndexForCitation,
  injectCitationAnchorLinks,
} from "@/lib/citation-md";
import { CitationChip } from "./CitationChip";

const NO_CITATIONS: Citation[] = [];

export type BriefMessage = {
  id: string;
  content: string;
  citations?: Citation[];
  bnsNotes?: string[];
  disclaimer?: string;
  llmUsed?: string;
  isStreaming?: boolean;
  error?: string;
  phase?: string;
};

type ResponseBlockProps = {
  query: string;
  queryTime: string;
  msg: BriefMessage;
  copiedId: string | null;
  bnsMode: boolean;
  onCopy: (id: string, content: string) => void;
  onRetry: (id: string) => void;
  onSelectCitation: (citation: Citation) => void;
};

const PHASE_LABELS: Record<string, string> = {
  enhancing: "Analysing your question",
  retrieving: "Searching legal documents",
  generating: "Generating answer",
};

function bnsSectionFor(ipcSection: string | null, notes: string[] = []) {
  if (!ipcSection) return undefined;
  const escaped = ipcSection.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const pattern = new RegExp(
    `IPC Section ${escaped}[^→]*→\\s*BNS Section\\s*([^\\n]+)`,
    "i"
  );
  const note = notes.find((item) => pattern.test(item));
  return note?.match(pattern)?.[1]?.trim();
}

function footnoteTitle(citation: Citation) {
  const base = citation.source_file.replace(/\.[^.]+$/, "").replace(/_/g, " ");
  const raw = citation.text?.trim() ?? "";
  const short =
    raw.length > 90 ? `${raw.slice(0, 87).trim()}…` : raw;
  return { base, short };
}

function sourceTitle(citation: Citation) {
  if (citation.ipc_section) return `IPC §${citation.ipc_section}`;
  return `Source ${citation.citation_id}`;
}

export function ResponseBlock({
  query,
  queryTime,
  msg,
  copiedId,
  bnsMode,
  onCopy,
  onRetry,
  onSelectCitation,
}: ResponseBlockProps) {
  const citationList = msg.citations ?? NO_CITATIONS;

  const markdownSource = useMemo(
    () => injectCitationAnchorLinks(msg.content, citationList),
    [msg.content, citationList]
  );

  const mdComponents: Components = useMemo(
    () => ({
      a({ href, children, node, ...rest }) {
        void node;
        if (href?.startsWith("#jg-cite-")) {
          const id = Number.parseInt(href.slice("#jg-cite-".length), 10);
          const cit = citationList.find((c) => c.citation_id === id);
          if (!cit) return <span>{children}</span>;
          const fn = footnoteIndexForCitation(citationList, id);
          return (
            <CitationChip
              section={cit.ipc_section}
              bnsSection={bnsSectionFor(cit.ipc_section, msg.bnsNotes)}
              bnsMode={bnsMode}
              preview={cit.text}
              footnoteIndex={fn}
              onSelect={() => onSelectCitation(cit)}
            />
          );
        }
        const isHttp =
          href?.startsWith("http://") || href?.startsWith("https://");
        return (
          <a
            href={href}
            {...(isHttp
              ? { rel: "noreferrer noopener", target: "_blank" }
              : {})}
            {...rest}
          >
            {children}
          </a>
        );
      },
    }),
    [bnsMode, citationList, msg.bnsNotes, onSelectCitation]
  );

  return (
    <article className="brief-stack">
      <div className="query-brief">
        <div className="query-meta">
          <span>QUERY</span>
          <time>{queryTime}</time>
        </div>
        <p>{query}</p>
      </div>

      <section className="answer-brief">
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

        {msg.error && (
          <p className="error-text">
            {msg.error}
            <button type="button" onClick={() => onRetry(msg.id)}>
              Retry
            </button>
          </p>
        )}

        {msg.content && (
          <div className="answer-content">
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={mdComponents}>
              {markdownSource}
            </ReactMarkdown>
            {msg.isStreaming && <span className="cursor-blink">|</span>}
          </div>
        )}

        {(msg.citations?.length || msg.bnsNotes?.length) ? (
          <div className="citations-section">
            <hr />
            <div className="citations-title">Citations</div>
            {msg.citations?.map((citation, index) => {
              const bnsSection = bnsSectionFor(
                citation.ipc_section,
                msg.bnsNotes
              );
              const { base, short } = footnoteTitle(citation);
              return (
                <div
                  className="citation-footnote"
                  key={`${citation.citation_id}-${citation.source_file}`}
                >
                  <span>{index + 1}</span>
                  <div>
                    <strong>
                      {sourceTitle(citation)} — {base}
                    </strong>
                    <p className="citation-footnote-preview">{short}</p>
                    {bnsSection ? (
                      <p className="bns-equivalent">
                        BNS Equivalent: §{bnsSection}
                      </p>
                    ) : null}
                    <p>
                      Source: Indian Penal Code, 1860
                      {citation.page !== "n/a" ? `, p. ${citation.page}` : ""}
                    </p>
                  </div>
                </div>
              );
            })}
            {msg.bnsNotes?.length ? (
              <div className="bns-notes">
                {msg.bnsNotes.map((note) => (
                  <p key={note}>{note}</p>
                ))}
              </div>
            ) : null}
          </div>
        ) : null}

        {!msg.isStreaming && msg.content ? (
          <div className="message-actions">
            <button
              type="button"
              className={`btn-icon ${copiedId === msg.id ? "copied" : ""}`}
              onClick={() => onCopy(msg.id, msg.content)}
            >
              {copiedId === msg.id ? "Copied" : "Copy brief"}
            </button>
            {msg.llmUsed ? <span className="model-note">{msg.llmUsed}</span> : null}
            {msg.disclaimer ? (
              <span className="disclaimer">{msg.disclaimer}</span>
            ) : null}
          </div>
        ) : null}
      </section>
    </article>
  );
}
