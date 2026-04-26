export type Citation = {
  citation_id: number;
  source_file: string;
  page: string;
  ipc_section: string | null;
  chunk_index: number | null;
  score: number | null;
  text: string;
};

export type AskResponse = {
  ok: boolean;
  session_id?: string;
  answer: string;
  citations: Citation[];
  bns_notes?: string[];
  enhanced_query?: string;
  prompt_version?: string;
  estimated_tokens?: number | null;
  llm_used?: string;
  disclaimer?: string;
  message?: string;
  error?: string;
  retry_after_seconds?: number;
};

export type StreamDoneMetadata = {
  session_id?: string;
  enhanced_query?: string;
  latency_ms?: number;
  prompt_version?: string;
  llm_used?: string;
  disclaimer?: string;
};

export interface StreamCallbacks {
  query: string;
  sessionId?: string | null;
  onStatus?: (phase: string) => void;
  onToken: (text: string) => void;
  onCitations: (citations: Citation[], bnsNotes: string[]) => void;
  onDone: (metadata: StreamDoneMetadata) => void;
  onError: (message: string) => void;
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function askJusticeGuide(
  query: string,
  sessionId?: string | null
): Promise<AskResponse> {
  const response = await fetch(`${API_BASE_URL}/api/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, session_id: sessionId }),
    cache: "no-store",
  });

  const payload = (await response.json()) as AskResponse;
  if (!response.ok) {
    return {
      ok: false,
      answer: "",
      citations: [],
      message: payload.message ?? `Request failed (${response.status}).`,
      error: payload.error,
      disclaimer: payload.disclaimer,
      retry_after_seconds: payload.retry_after_seconds,
    };
  }
  return payload;
}

export async function streamAsk(params: StreamCallbacks): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/ask/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query: params.query,
      session_id: params.sessionId,
    }),
  });

  if (!response.ok) {
    let msg = `Request failed (${response.status})`;
    try {
      const payload = await response.json();
      if (payload.message) msg = payload.message;
    } catch {
      /* ignore parse errors */
    }
    params.onError(msg);
    return;
  }

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let currentEvent = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("event: ")) {
        currentEvent = line.slice(7).trim();
      } else if (line.startsWith("data: ")) {
        try {
          const data = JSON.parse(line.slice(6));
          switch (currentEvent) {
            case "status":
              params.onStatus?.(data.phase);
              break;
            case "token":
              params.onToken(data.text);
              break;
            case "citations":
              params.onCitations(data.citations || [], data.bns_notes || []);
              break;
            case "done":
              params.onDone(data as StreamDoneMetadata);
              break;
            case "error":
              params.onError(data.message || "An unknown error occurred.");
              break;
          }
        } catch {
          /* ignore malformed JSON lines */
        }
        currentEvent = "";
      }
    }
  }
}
