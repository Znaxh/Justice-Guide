"use client";

type CitationChipProps = {
  section: string | null;
  bnsSection?: string;
  bnsMode: boolean;
  preview: string;
  footnoteIndex?: number;
  onSelect?: () => void;
};

export function CitationChip({
  section,
  bnsSection,
  bnsMode,
  preview,
  footnoteIndex,
  onSelect,
}: CitationChipProps) {
  const displaySection = bnsMode && bnsSection ? bnsSection : section;
  const code = displaySection ? `§${displaySection}` : "source";

  return (
    <span className="citation-chip-wrap">
      <button
        type="button"
        className={`citation-chip citation-chip-inline ${bnsMode && bnsSection ? "is-bns" : ""}`}
        onClick={onSelect}
      >
        [{code}]
        <span className="citation-popover" role="tooltip">
          {preview.length > 280 ? `${preview.slice(0, 280)}...` : preview}
        </span>
      </button>
      {footnoteIndex != null && footnoteIndex > 0 ? (
        <sup className="citation-footnote-ref" aria-hidden="true">
          {footnoteIndex}
        </sup>
      ) : null}
    </span>
  );
}
