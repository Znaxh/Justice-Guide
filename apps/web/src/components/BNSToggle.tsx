"use client";

type BNSToggleProps = {
  enabled: boolean;
  onToggle: () => void;
};

export function BNSToggle({ enabled, onToggle }: BNSToggleProps) {
  return (
    <button
      type="button"
      className={`bns-toggle ${enabled ? "is-on" : ""}`}
      onClick={onToggle}
      aria-pressed={enabled}
    >
      <span className="bns-toggle-track" aria-hidden="true">
        <span className="bns-toggle-thumb" />
      </span>
      <span>BNS Mode</span>
    </button>
  );
}
