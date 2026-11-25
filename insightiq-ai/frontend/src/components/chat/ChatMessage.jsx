import React, { useState } from "react";
import { User, Bot, HelpCircle, ArrowRight, Copy, Check, Sparkles, ChevronDown, ChevronUp, ShieldCheck } from "lucide-react";
import ToolStatusPanel from "./ToolStatusPanel";
import EvidencePanel from "./EvidencePanel";
import { DynamicChart } from "../charts/DynamicChart";
import { MarkdownView } from "../common";

export const ChatMessage = ({
  message,
  onSelectFollowUp,
  className = "",
}) => {
  const [copied, setCopied] = useState(false);
  const [showTechnicalAudit, setShowTechnicalAudit] = useState(false);
  const isUser = message.role === "user";

  const handleCopy = () => {
    const textToCopy = message.content || message.summary || "";
    if (textToCopy && navigator.clipboard) {
      navigator.clipboard.writeText(textToCopy);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (isUser) {
    return (
      <div
        data-testid="chat-message-user"
        className={`flex justify-end gap-3 ${className}`}
      >
        <div className="max-w-xl bg-gradient-to-r from-navy-900 to-navy-800 text-white px-4 py-3 rounded-2xl rounded-tr-xs shadow-subtle text-xs leading-relaxed font-normal">
          {message.content}
        </div>
        <div className="w-8 h-8 rounded-full bg-navy-800 text-brand-300 flex items-center justify-center shrink-0 shadow-xs border border-navy-700">
          <User size={15} />
        </div>
      </div>
    );
  }

  // Assistant Response Structure
  const {
    summary,
    insights = [],
    metrics_referenced = [],
    chart_spec = null,
    tool_executions = [],
    suggested_follow_ups = [],
    data_limitations_noted = null,
    needs_clarification = false,
    clarification_question = null,
  } = message;

  const hasAuditData = (metrics_referenced && metrics_referenced.length > 0) ||
                       (insights && insights.length > 0) ||
                       (tool_executions && tool_executions.length > 0) ||
                       data_limitations_noted;

  return (
    <div
      data-testid="chat-message-assistant"
      className={`flex items-start gap-3 ${className}`}
    >
      <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-brand-600 via-brand-500 to-indigo-600 text-white flex items-center justify-center shrink-0 shadow-sm mt-0.5 border border-brand-400/30">
        <Bot size={16} />
      </div>

      <div className="flex-1 max-w-3xl space-y-3">
        {/* Main ChatGPT-like Response Card */}
        <div className="bg-surface rounded-2xl rounded-tl-xs border border-surface-border shadow-subtle text-xs overflow-hidden">
          {/* Header Bar */}
          <div className="px-4 py-2.5 bg-surface-subtle/70 border-b border-surface-border flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="font-bold text-navy-900 text-xs tracking-tight">
                InsightIQ Analyst
              </span>
              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px] font-medium bg-brand-50 text-brand-700 border border-brand-200">
                <Sparkles size={9} />
                <span>Audited AI</span>
              </span>
            </div>

            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={handleCopy}
                title="Copy response"
                className="p-1 text-navy-400 hover:text-navy-700 hover:bg-surface-muted rounded-md transition-colors flex items-center gap-1 text-[11px]"
              >
                {copied ? (
                  <>
                    <Check size={12} className="text-emerald-600" />
                    <span className="text-emerald-700 text-[10px] font-medium">Copied</span>
                  </>
                ) : (
                  <>
                    <Copy size={12} />
                    <span className="text-[10px] text-navy-500">Copy</span>
                  </>
                )}
              </button>
            </div>
          </div>

          <div className="p-5 space-y-4">
            {/* Clarification Alert if needed */}
            {needs_clarification && clarification_question && (
              <div className="p-3.5 bg-amber-50/80 border border-amber-200 rounded-xl flex items-start gap-2.5 text-amber-900 text-xs shadow-2xs">
                <HelpCircle size={16} className="text-amber-600 shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold block mb-0.5 text-amber-950">Clarification Needed:</span>
                  <span className="leading-relaxed">{clarification_question}</span>
                </div>
              </div>
            )}

            {/* Conversational Markdown Response */}
            {summary && (
              <div data-testid="chat-message-summary" className="text-navy-800 text-[13px] leading-relaxed">
                <MarkdownView content={summary} />
              </div>
            )}

            {/* Dynamic Recharts Chart if requested or relevant */}
            {chart_spec && (
              <div className="pt-2 rounded-xl border border-surface-border bg-surface-subtle/40 p-3 shadow-2xs">
                <div className="text-[11px] font-semibold text-navy-700 mb-2 flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-brand-500" />
                  <span>{chart_spec.title || "Interactive Data Visualization"}</span>
                </div>
                <DynamicChart spec={chart_spec} height={280} />
              </div>
            )}

            {/* Evidence, Ground-Truth Metrics, and Tool Execution Panels */}
            {hasAuditData && (
              <div className="pt-2 border-t border-surface-border/60">
                <button
                  type="button"
                  onClick={() => setShowTechnicalAudit(!showTechnicalAudit)}
                  className="w-full py-1.5 px-2.5 rounded-lg bg-surface-subtle hover:bg-surface-muted border border-surface-border flex items-center justify-between text-navy-700 text-[11px] font-medium transition-colors"
                >
                  <div className="flex items-center gap-1.5">
                    <ShieldCheck size={13} className="text-emerald-600" />
                    <span>Audited Evidence & Database Tool Execution</span>
                    <span className="text-[10px] text-navy-600 bg-surface px-1.5 py-0.5 rounded border border-surface-border font-mono">
                      {metrics_referenced.length} metrics • {tool_executions.length} queries
                    </span>
                  </div>
                  <div className="flex items-center gap-1 text-navy-600 text-[11px]">
                    <span>{showTechnicalAudit ? "Hide Details" : "View Audit Trail"}</span>
                    {showTechnicalAudit ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                  </div>
                </button>

                {/* Collapsible / Expandable Audit Details */}
                <div className={`mt-3 space-y-3 ${showTechnicalAudit ? "block" : "hidden sm:block"}`}>
                  <EvidencePanel
                    metrics={metrics_referenced}
                    insights={insights}
                    dataLimitations={data_limitations_noted}
                  />

                  {tool_executions && tool_executions.length > 0 && (
                    <ToolStatusPanel toolExecutions={tool_executions} />
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Suggested Contextual Follow-Up Buttons */}
        {suggested_follow_ups && suggested_follow_ups.length > 0 && onSelectFollowUp && (
          <div className="pl-1 space-y-1.5">
            <span className="text-[10px] font-semibold text-navy-600 uppercase tracking-wider block">
              Suggested Follow-Ups
            </span>
            <div className="flex flex-wrap gap-1.5">
              {suggested_follow_ups.map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => onSelectFollowUp(q)}
                  className="text-xs px-3 py-1.5 bg-surface hover:bg-surface-subtle border border-surface-border hover:border-brand-400 text-navy-700 hover:text-navy-950 rounded-xl transition-all flex items-center gap-1.5 shadow-2xs hover:shadow-xs"
                >
                  <span>{q}</span>
                  <ArrowRight size={11} className="text-navy-400 group-hover:text-brand-500" />
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatMessage;
