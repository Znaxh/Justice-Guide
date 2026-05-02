"use client";

import { type Citation } from "@/lib/api";

type ReferencePanelProps = {
  citation: Citation | null;
  isOpen: boolean;
  bnsMode: boolean;
  onToggle: () => void;
};

export function ReferencePanel({
  citation,
  isOpen,
  bnsMode,
  onToggle,
}: ReferencePanelProps) {
  return (
    <aside className={`reference-panel ${isOpen ? "is-open" : ""}`}>
      <div className="reference-header">
        <div>
          <span className="panel-kicker">IPC Reference</span>
          <h2>{citation?.ipc_section ? `Section ${citation.ipc_section}` : "Source Text"}</h2>
        </div>
        <button type="button" className="btn-ghost" onClick={onToggle}>
          {isOpen ? "Hide" : "Show"}
        </button>
      </div>

      {bnsMode && (
        <div className="reference-banner">
          Showing Bharatiya Nyaya Sanhita equivalents where available.
        </div>
      )}

      {citation ? (
        <div className="reference-body">
          <dl>
            <div>
              <dt>Source</dt>
              <dd>{citation.source_file}</dd>
            </div>
            <div>
              <dt>Page</dt>
              <dd>{citation.page}</dd>
            </div>
          </dl>
          <pre>{citation.text}</pre>
        </div>
      ) : (
        <p className="reference-empty">
          Select a citation chip to inspect the raw IPC text in this panel.
        </p>
      )}
    </aside>
  );
}
