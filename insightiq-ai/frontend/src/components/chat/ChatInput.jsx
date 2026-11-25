import React, { useState } from "react";
import { Send, Trash2 } from "lucide-react";

export const ChatInput = ({
  onSend,
  onClear,
  loading = false,
  hasMessages = false,
  placeholder = "Ask a business question (e.g. 'Why did revenue decline last month?')...",
  className = "",
}) => {
  const [text, setText] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!text.trim() || loading) return;
    onSend(text.trim());
    setText("");
  };

  return (
    <div
      data-testid="chat-input-container"
      className={`bg-surface p-3 rounded-2xl border border-surface-border shadow-card ${className}`}
    >
      <form onSubmit={handleSubmit} className="flex items-center gap-2">
        {hasMessages && onClear && (
          <button
            type="button"
            onClick={onClear}
            disabled={loading}
            aria-label="Clear conversation"
            title="Clear conversation"
            className="p-2 text-navy-600 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition-colors disabled:opacity-50"
          >
            <Trash2 size={16} />
          </button>
        )}

        <input
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          disabled={loading}
          placeholder={placeholder}
          className="flex-1 px-3 py-2 text-xs bg-transparent text-navy-900 placeholder:text-navy-600 focus:outline-hidden"
        />

        <button
          type="submit"
          disabled={loading || !text.trim()}
          aria-label="Send inquiry"
          className="px-4 py-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-40 text-white text-xs font-semibold rounded-xl shadow-xs flex items-center gap-1.5 transition-colors"
        >
          {loading ? (
            <span className="inline-block animate-spin">⏳</span>
          ) : (
            <>
              <span>Ask Analyst</span>
              <Send size={13} />
            </>
          )}
        </button>
      </form>
    </div>
  );
};

export default ChatInput;
