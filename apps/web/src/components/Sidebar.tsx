"use client";

type RecentQuery = {
  id: string;
  query: string;
  timestamp: string;
};

type SidebarProps = {
  recentQueries: RecentQuery[];
  isOpen: boolean;
  onClose: () => void;
  onNewSession: () => void;
};

function ScalesIcon() {
  return (
    <svg viewBox="0 0 48 48" aria-hidden="true" className="scales-icon">
      <path d="M24 6v34" />
      <path d="M14 14h20" />
      <path d="M24 14l-10 5-7 13h14l-7-13" />
      <path d="M24 14l10 5 7 13H27l7-13" />
      <path d="M18 40h12" />
      <path d="M15 44h18" />
    </svg>
  );
}

export function Sidebar({
  recentQueries,
  isOpen,
  onClose,
  onNewSession,
}: SidebarProps) {
  return (
    <>
      <aside className={`sidebar ${isOpen ? "is-open" : ""}`}>
        <div className="sidebar-header">
          <div className="wordmark">
            <ScalesIcon />
            <span>JusticeGuide</span>
          </div>
          <button type="button" className="sidebar-close" onClick={onClose}>
            ×
          </button>
        </div>

        <button type="button" className="new-session" onClick={onNewSession}>
          New Research Session
        </button>

        <div className="docket-label">Recent Docket</div>
        <div className="docket-list">
          {recentQueries.length === 0 ? (
            <p className="empty-docket">No recorded queries yet.</p>
          ) : (
            recentQueries.map((item) => (
              <article key={item.id} className="docket-item">
                <time>{item.timestamp}</time>
                <p>{item.query}</p>
              </article>
            ))
          )}
        </div>
      </aside>
      <button
        type="button"
        className={`sidebar-scrim ${isOpen ? "is-open" : ""}`}
        onClick={onClose}
        aria-label="Close docket"
      />
    </>
  );
}
