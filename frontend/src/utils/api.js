import axios from "axios";
import { API_ENDPOINTS, API_BASE_URL } from "./constants.js";

const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

const UPLOAD_TIMEOUT_MS = 5 * 60 * 1000;

let createSessionPromise = null;

// Add session ID to all requests (only for JSON, not FormData)
axiosInstance.interceptors.request.use((config) => {
  const sessionId = localStorage.getItem("sessionId");
  if (sessionId && !(config.data instanceof FormData)) {
    config.data = config.data || {};
    config.data.session_id = sessionId;
  }
  return config;
});

// Handle errors
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("sessionId");
      window.location.href = "/";
    }
    return Promise.reject(error);
  },
);

export async function uploadDocument(file, agentType) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("agentType", agentType);
  const sessionId = localStorage.getItem("sessionId");
  if (sessionId) {
    formData.append("session_id", sessionId);
  }

  return axiosInstance.post(API_ENDPOINTS.UPLOAD, formData, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: UPLOAD_TIMEOUT_MS,
  });
}

export async function deleteDocument(documentId) {
  const sessionId = localStorage.getItem("sessionId");
  if (!sessionId) return Promise.resolve();

  return axiosInstance.delete(`/documents/${sessionId}/${documentId}`);
}

export async function sendMessage(message, agentType) {
  const sessionId = localStorage.getItem("sessionId");
  return axiosInstance.post(API_ENDPOINTS.CHAT, {
    session_id: sessionId,
    message,
    agent_type: agentType,
  });
}

export async function createSession() {
  const existingSessionId = localStorage.getItem("sessionId");
  if (existingSessionId) {
    return { session_id: existingSessionId };
  }

  if (createSessionPromise) {
    return createSessionPromise;
  }

  createSessionPromise = (async () => {
    try {
      const response = await axiosInstance.post("/session/create");
      if (response.data.session_id) {
        localStorage.setItem("sessionId", response.data.session_id);
        return response.data;
      }
    } catch (error) {
      console.error("Failed to create session:", error);
      throw error;
    } finally {
      createSessionPromise = null;
    }
  })();

  return createSessionPromise;
}

export async function updateAgent(agentType) {
  // This endpoint doesn't exist in FastAPI backend yet
  // Safe to ignore or remove if not needed
  return Promise.resolve({ status: "ok" });
}

export async function generateSummary(documentId) {
  return axiosInstance.post(`/upload/summary?document_id=${documentId}`);
}

export async function generateKeyPoints(documentId) {
  return axiosInstance.post(`/upload/key-points?document_id=${documentId}`);
}

export async function generateImportantQuestions(documentId) {
  return axiosInstance.post(
    `/upload/important-questions?document_id=${documentId}`,
  );
}

export async function clearSession() {
  const sessionId = localStorage.getItem("sessionId");
  if (!sessionId) return Promise.resolve();

  return axiosInstance.delete(`/session/${sessionId}`);
}

export async function getSessionInfo() {
  const sessionId = localStorage.getItem("sessionId");
  if (!sessionId) return null;

  return axiosInstance.get(API_ENDPOINTS.GET_SESSION, {
    params: { session_id: sessionId },
  });
}

export default axiosInstance;
