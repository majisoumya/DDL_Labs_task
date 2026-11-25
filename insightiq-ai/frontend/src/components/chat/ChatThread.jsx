import React, { useEffect, useRef } from "react";
import { Bot, Sparkles, Database } from "lucide-react";
import ChatMessage from "./ChatMessage";
import SuggestedQuestions from "./SuggestedQuestions";

export const ChatThread = ({
  messages = [],
  loading = false,
  suggestedQuestions = [],
  onSelectSuggested,
  className = "",
}) => {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView?.({ behavior: "smooth" });
  }, [messages, loading]);

  const isEmpty = messages.length === 0;

  return (
    <div
      data-testid="chat-thread"
      className={`flex-1 overflow-y-auto p-4 md:p-6 space-y-6 ${className}`}
    >
      {/* Welcome State when conversation is empty */}
      {isEmpty && (
        <div
          data-testid="chat-welcome-state"
          className="max-w-2xl mx-auto py-12 text-center space-y-6"
        >
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-brand-600 to-brand-500 text-white flex items-center justify-center mx-auto shadow-md">
            <Bot size={28} />
          </div>

          <div className="space-y-1.5">
            <h2 className="text-xl font-bold text-navy-900 tracking-tight">
              InsightIQ Autonomous Business Analyst
            </h2>
            <p className="text-xs text-navy-600 max-w-md mx-auto">
              Ask natural-language questions about enterprise revenue, product catalog velocity, customer cohorts, or multi-period variances.
            </p>
          </div>

          <div className="p-4 bg-surface rounded-2xl border border-surface-border shadow-subtle text-left max-w-lg mx-auto">
            <SuggestedQuestions
              questions={suggestedQuestions}
              onSelect={onSelectSuggested}
            />
          </div>

          <div className="flex items-center justify-center gap-4 text-[11px] text-navy-400">
            <span className="flex items-center gap-1">
              <Database size={12} className="text-emerald-500" />
              Direct Database Grounding
            </span>
            <span>•</span>
            <span>Zero Numerical Hallucination</span>
            <span>•</span>
            <span>Audited Execution Traces</span>
          </div>
        </div>
      )}

      {/* Message History */}
      {messages.map((msg, idx) => (
        <ChatMessage
          key={idx}
          message={msg}
          onSelectFollowUp={onSelectSuggested}
        />
      ))}

      {/* Thinking / Tool Execution Loading State */}
      {loading && (
        <div
          data-testid="chat-loading-indicator"
          className="flex items-center gap-3 text-xs text-navy-600"
        >
          <div className="w-8 h-8 rounded-full bg-brand-50 border border-brand-200 text-brand-600 flex items-center justify-center animate-pulse">
            <Sparkles size={16} />
          </div>
          <div className="p-3 bg-surface rounded-2xl rounded-tl-xs border border-surface-border shadow-subtle flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-brand-500 animate-ping" />
            <span className="font-medium">
              Querying analytics warehouse and synthesizing evidence...
            </span>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
};

export default ChatThread;
