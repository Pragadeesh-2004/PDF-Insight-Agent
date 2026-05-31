export const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000/api";

export const API_ENDPOINTS = {
  UPLOAD: `${API_BASE_URL}/upload/document`,
  CHAT: `${API_BASE_URL}/chat/message`,
  UPDATE_AGENT: `${API_BASE_URL}/chat/update-agent`,
  SUMMARY: `${API_BASE_URL}/upload/summary`,
  KEY_POINTS: `${API_BASE_URL}/upload/key-points`,
  IMPORTANT_QUESTIONS: `${API_BASE_URL}/upload/important-questions`,
  CLEAR_SESSION: `${API_BASE_URL}/session/clear`,
  GET_SESSION: `${API_BASE_URL}/session/info`,
};

export const AGENTS = {
  GENERAL_ASSISTANT: {
    id: "GENERAL_ASSISTANT",
    name: "General Assistant",
    description: "Chat with Gemini AI",
    icon: "MessageSquare",
  },
  PDF_INSIGHT_AGENT: {
    id: "PDF_INSIGHT_AGENT",
    name: "PDF Insight Agent",
    description: "Upload and analyze documents",
    icon: "FileText",
  },
};

export const COLORS = {
  primary: "#0066ff",
  secondary: "#00d4ff",
  dark: "#0a0e27",
  darker: "#050a1a",
  glass: "rgba(255, 255, 255, 0.05)",
};

export const ANIMATION_DURATION = {
  SHORT: 200,
  MEDIUM: 300,
  LONG: 500,
};
