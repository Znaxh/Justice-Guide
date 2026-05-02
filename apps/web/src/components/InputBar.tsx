"use client";

import { type FormEvent, type RefObject } from "react";

type InputBarProps = {
  query: string;
  isLoading: boolean;
  canSubmit: boolean;
  flash: boolean;
  textareaRef: RefObject<HTMLTextAreaElement | null>;
  onQueryChange: (value: string) => void;
  onSubmit: (event?: FormEvent) => void;
};

export function InputBar({
  query,
  isLoading,
  canSubmit,
  flash,
  textareaRef,
  onQueryChange,
  onSubmit,
}: InputBarProps) {
  function autoResize(el: HTMLTextAreaElement) {
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 84)}px`;
  }

  return (
    <form
      onSubmit={onSubmit}
      className={`input-area ${flash ? "input-area-flash" : ""}`}
    >
      <div className="terminal-input">
        <span className="prompt-mark" aria-hidden="true">
          §
        </span>
        <textarea
          ref={textareaRef}
          value={query}
          onChange={(e) => {
            onQueryChange(e.target.value);
            autoResize(e.target);
          }}
          placeholder="Ask about IPC §302, theft, cheating, culpable homicide..."
          rows={1}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              if (canSubmit) onSubmit();
            }
          }}
        />
        <button type="submit" disabled={!canSubmit} className="btn-submit">
          {isLoading ? "Reading..." : "⏎ Submit"}
        </button>
      </div>
      <p className="input-disclaimer">
        JusticeGuide is not a substitute for professional legal advice.
      </p>
    </form>
  );
}
