import type { Citation } from "@/lib/api";

function escapeRe(s: string) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function transformOutsideFences(
  segment: string,
  citations: Citation[]
): string {
  const withSection = citations.filter((c) => c.ipc_section);
  if (!withSection.length) return segment;

  let out = segment;

  const bySection = new Map<string, Citation>();
  for (const c of withSection) {
    const sec = c.ipc_section as string;
    if (!bySection.has(sec)) bySection.set(sec, c);
  }

  const orderedSections = [...bySection.entries()].sort(
    (a, b) => b[0].length - a[0].length
  );

  for (const [sec, cit] of orderedSections) {
    const re = new RegExp(
      `\\[\\s*§\\s*${escapeRe(sec)}\\s*\\](?!\\(#jg-cite-)`,
      "g"
    );
    out = out.replace(re, `[§${sec}](#jg-cite-${cit.citation_id})`);
  }

  /** RAG prompts use [0], [1], … — map those to IPC § links when metadata has a section. */
  const numericOrder = [...withSection].sort(
    (a, b) => b.citation_id - a.citation_id
  );
  for (const cit of numericOrder) {
    const re = new RegExp(
      `\\[${cit.citation_id}\\](?!\\(#jg-cite-)`,
      "g"
    );
    out = out.replace(
      re,
      `[§${cit.ipc_section}](#jg-cite-${cit.citation_id})`
    );
  }

  return out;
}

/**
 * Turns `[§302]` and retriever-style `[0]` markers into markdown links so
 * react-markdown renders them as CitationChip (outside fenced code blocks only).
 */
export function injectCitationAnchorLinks(
  markdown: string,
  citations: Citation[] | undefined
): string {
  if (!citations?.length || !markdown) return markdown;

  const hasSection = citations.some((c) => c.ipc_section);
  if (!hasSection) return markdown;

  const segments = markdown.split(/(```[\s\S]*?```)/g);
  return segments
    .map((segment) =>
      segment.startsWith("```")
        ? segment
        : transformOutsideFences(segment, citations)
    )
    .join("");
}

export function footnoteIndexForCitation(
  citations: Citation[] | undefined,
  citationId: number
): number {
  if (!citations?.length) return 0;
  const idx = citations.findIndex((c) => c.citation_id === citationId);
  return idx >= 0 ? idx + 1 : 0;
}
