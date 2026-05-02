"use client";

type QueryCardProps = {
  tag: string;
  question: string;
  index: number;
  onClick: () => void;
};

export function QueryCard({ tag, question, index, onClick }: QueryCardProps) {
  return (
    <button
      type="button"
      className="query-card fade-in"
      style={{ animationDelay: `${160 + index * 80}ms` }}
      onClick={onClick}
    >
      <span className="query-card-tag">{tag}</span>
      <span className="query-card-question">{question}</span>
      <span className="query-card-arrow" aria-hidden="true">
        →
      </span>
    </button>
  );
}
