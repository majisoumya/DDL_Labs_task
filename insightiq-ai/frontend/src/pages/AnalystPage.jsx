import React, { useState, useEffect } from "react";
import { Sparkles, History } from "lucide-react";
import { ChatThread, ChatInput, ExecutionHistoryDrawer } from "../components/chat";
import { ErrorState } from "../components/common";
import { analystService } from "../services";

const DEFAULT_STARTER_QUESTIONS = [
  "What is our total revenue?",
  "Show monthly revenue.",
  "Which products generate the most revenue?",
  "Who are our repeat customers?",
  "Why did revenue decline last month?",
  "Compare revenue by category.",
];

const CHAT_STORAGE_KEY = "insightiq_chat_history_v1";

export const AnalystPage = () => {
  const [messages, setMessages] = useState(() => {
    try {
      const saved = localStorage.getItem(CHAT_STORAGE_KEY);
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [suggestions, setSuggestions] = useState(DEFAULT_STARTER_QUESTIONS);
  const [showHistory, setShowHistory] = useState(false);

  // Automatically persist messages across page navigation
  useEffect(() => {
    try {
      localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(messages));
    } catch (err) {
      console.warn("Failed to persist conversation history:", err);
    }
  }, [messages]);

  useEffect(() => {
    const loadSuggestions = async () => {
      try {
        const res = await analystService.getSuggestions();
        if (Array.isArray(res) && res.length > 0) {
          setSuggestions(res);
        }
      } catch {
        // Fall back to default suggestions
      }
    };
    loadSuggestions();
  }, []);

  const handleSendMessage = async (userPrompt) => {
    if (!userPrompt || !userPrompt.trim() || loading) return;

    setError(null);
    const userMessage = { role: "user", content: userPrompt.trim() };
    const nextMessages = [...messages, userMessage];
    setMessages(nextMessages);
    setLoading(true);

    try {
      // Build history for backend context
      const historyContext = messages.map((m) => ({
        role: m.role,
        content: m.content || m.summary || (m.insights && m.insights.length > 0 ? m.insights[0].finding : ""),
      }));

      const response = await analystService.askQuestion(
        userPrompt.trim(),
        historyContext
      );

      const assistantMessage = {
        role: "assistant",
        summary: response.summary,
        insights: response.insights || [],
        metrics_referenced: response.metrics_referenced || [],
        chart_spec: response.chart_spec || null,
        tool_executions: response.tool_executions || [],
        suggested_follow_ups: response.suggested_follow_ups || [],
        data_limitations_noted: response.data_limitations_noted || null,
        needs_clarification: response.needs_clarification || false,
        clarification_question: response.clarification_question || null,
      };

      setMessages([...nextMessages, assistantMessage]);
      setLoading(false);
    } catch (err) {
      setError(err.message || "Failed to receive response from AI Analyst.");
      setLoading(false);
    }
  };

  const handleClearConversation = () => {
    setMessages([]);
    setError(null);
    try {
      localStorage.removeItem(CHAT_STORAGE_KEY);
    } catch {}
  };

  return (
    <div
      data-testid="analyst-studio-container"
      className="flex flex-col h-[calc(100vh-7.5rem)] max-w-5xl mx-auto bg-surface-subtle rounded-2xl border border-surface-border overflow-hidden shadow-card"
    >
      {/* Studio Header Bar */}
      <div className="px-6 py-3.5 bg-surface border-b border-surface-border flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-brand-600 to-brand-500 text-white flex items-center justify-center shadow-xs">
            <Sparkles size={16} />
          </div>
          <div>
            <h2 className="text-sm font-bold text-navy-900 tracking-tight">
              InsightIQ AI Business Analyst
            </h2>
            <p className="text-[11px] text-navy-600">
              Autonomous reasoning backed by audited PostgreSQL evidence
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowHistory(true)}
            data-testid="audit-history-trigger"
            className="flex items-center gap-1.5 px-2.5 py-1.5 bg-surface-subtle hover:bg-surface-muted border border-surface-border rounded-lg text-xs font-medium text-navy-700 shadow-xs transition-colors"
          >
            <History size={13} className="text-navy-600" />
            <span>Audit History</span>
          </button>

          <div className="text-[11px] text-navy-600 font-mono hidden sm:flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span>Active Analytical Engine</span>
          </div>
        </div>
      </div>

      {/* Global Error Banner if API Fails */}
      {error && (
        <div className="p-4 bg-rose-50 border-b border-rose-200">
          <ErrorState
            title="Analyst Service Disruption"
            message={error}
            onRetry={() => {
              if (messages.length > 0) {
                const lastUser = [...messages].reverse().find((m) => m.role === "user");
                if (lastUser) handleSendMessage(lastUser.content);
              }
            }}
          />
        </div>
      )}

      {/* Conversation Thread */}
      <ChatThread
        messages={messages}
        loading={loading}
        suggestedQuestions={suggestions}
        onSelectSuggested={handleSendMessage}
      />

      {/* Sticky Bottom Input Bar */}
      <div className="p-4 bg-surface/90 backdrop-blur-sm border-t border-surface-border">
        <ChatInput
          onSend={handleSendMessage}
          onClear={handleClearConversation}
          loading={loading}
          hasMessages={messages.length > 0}
        />
      </div>

      {/* Analytics Execution History Drawer */}
      <ExecutionHistoryDrawer
        isOpen={showHistory}
        onClose={() => setShowHistory(false)}
        onSelectQuery={handleSendMessage}
      />
    </div>
  );
};

export default AnalystPage;
