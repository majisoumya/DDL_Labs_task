import React from "react";
import { Sparkles } from "lucide-react";

export const SuggestedQuestions = ({
  questions = [],
  onSelect,
  className = "",
}) => {
  if (!questions || questions.length === 0) return null;

  return (
    <div data-testid="suggested-questions" className={`space-y-2 ${className}`}>
      <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-navy-600">
        <Sparkles size={13} className="text-brand-500" />
        <span>Suggested Inquiries</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {questions.map((q, idx) => (
          <button
            key={idx}
            onClick={() => onSelect(q)}
            className="text-xs px-3 py-1.5 bg-surface hover:bg-surface-subtle border border-surface-border hover:border-brand-300 text-navy-800 rounded-lg shadow-2xs transition-all text-left flex items-center gap-1.5"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-brand-500" />
            <span>{q}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

export default SuggestedQuestions;
