/**
 * AI Business Analyst Conversational Service
 */

import api from "./apiClient";

export const analystService = {
  getSuggestions: () => api.get("analyst/suggestions"),

  askQuestion: (question, chatHistory = []) =>
    api.post("analyst/chat", {
      question,
      chat_history: chatHistory,
    }),

  getHistory: () => api.get("analyst/history"),

  clearHistory: () => api.delete("analyst/history"),
};

export default analystService;
