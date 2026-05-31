import React, { useState, useEffect, useCallback } from "react";
import Sidebar from "./components/Sidebar.jsx";
import ChatInterface from "./components/ChatInterface.jsx";
import UploadModal from "./components/UploadModal.jsx";
import DocumentPanel from "./components/DocumentPanel.jsx";
import {
  uploadDocument,
  sendMessage,
  updateAgent,
  generateSummary,
  generateKeyPoints,
  generateImportantQuestions,
  clearSession,
  createSession,
  deleteDocument,
} from "./utils/api.js";
import { API_BASE_URL } from "./utils/constants.js";
import "./styles/global.css";

const MAX_DOCUMENTS = 5;

export function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentAgent, setCurrentAgent] = useState("GENERAL_ASSISTANT");
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [documentActionLoading, setDocumentActionLoading] = useState(null);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadedDocuments, setUploadedDocuments] = useState([]);

  const hasDocuments = uploadedDocuments.length > 0;
  const isAssistantLoading = isChatLoading || Boolean(documentActionLoading);

  useEffect(() => {
    let mounted = true;

    const initializeSession = async () => {
      let sessionId = localStorage.getItem("sessionId");

      if (sessionId) {
        console.log(`Using existing session: ${sessionId}`);
        return;
      }

      try {
        console.log("Creating new session...");
        const response = await createSession();

        if (mounted && response?.session_id) {
          sessionId = response.session_id;
          localStorage.setItem("sessionId", sessionId);
          console.log(`New session created: ${sessionId}`);
        }
      } catch (error) {
        if (mounted) {
          console.error("Failed to create session:", error);
          console.error("Session creation failed - the app may not work correctly");
        }
      }
    };

    initializeSession();

    const cleanupSession = () => {
      const sessionId = localStorage.getItem("sessionId");
      if (!sessionId) return;

      const apiUrl = `${API_BASE_URL}/session/${sessionId}/cleanup`;

      if (navigator.sendBeacon) {
        navigator.sendBeacon(apiUrl);
      } else {
        fetch(apiUrl, {
          method: "POST",
          keepalive: true,
        }).catch(() => {});
      }

      console.log(`Cleanup triggered for session: ${sessionId}`);
      localStorage.removeItem("sessionId");
    };

    window.addEventListener("pagehide", cleanupSession);

    return () => {
      mounted = false;
      window.removeEventListener("pagehide", cleanupSession);
    };
  }, []);

  useEffect(() => {
    const updateCurrentAgent = async () => {
      try {
        await updateAgent(currentAgent);
      } catch (error) {
        console.error("Failed to update agent:", error);
      }
    };

    updateCurrentAgent();
  }, [currentAgent]);

  const handleSendMessage = useCallback(
    async (message) => {
      if (!message.trim()) return;

      setMessages((prev) => [
        ...prev,
        {
          role: "user",
          content: message,
          timestamp: new Date(),
        },
      ]);
      setIsChatLoading(true);

      try {
        const response = await sendMessage(message, currentAgent);

        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: response.data.answer,
            source: response.data.source,
            chunksRetrieved: response.data.chunks_retrieved || 0,
            contextUsed: response.data.context_used || 0,
            model: response.data.model,
            timestamp: new Date(),
          },
        ]);
      } catch (error) {
        console.error("Failed to send message:", error);
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: `Error: ${error.response?.data?.detail || error.message}`,
            isError: true,
            timestamp: new Date(),
          },
        ]);
      } finally {
        setIsChatLoading(false);
      }
    },
    [currentAgent],
  );

  const handleUploadDocument = useCallback(
    async (file) => {
      if (uploadedDocuments.length >= MAX_DOCUMENTS) {
        throw new Error("You can upload up to 5 documents. Clear one to add another.");
      }

      setIsUploading(true);
      try {
        const response = await uploadDocument(file, "PDF_INSIGHT_AGENT");
        const uploaded = {
          id: response.data.document_id,
          name: response.data.filename,
          chunksCreated: response.data.chunks_created,
        };

        setUploadedDocuments((prev) => [...prev, uploaded]);
        setMessages((prev) => [
          ...prev,
          {
            type: "ACTION",
            content: `Document uploaded: ${uploaded.name} (${uploaded.chunksCreated} chunks processed)`,
            role: "system",
          },
        ]);
      } catch (error) {
        console.error("Upload error:", error);
        throw error;
      } finally {
        setIsUploading(false);
      }
    },
    [uploadedDocuments.length],
  );

  const runDocumentAction = useCallback(
    async ({ document, type, userPrompt, request, buildAssistantMessage, errorPrefix }) => {
      if (!document?.id || documentActionLoading) return;

      setMessages((prev) => [
        ...prev,
        {
          role: "user",
          content: `${userPrompt} for "${document.name}"`,
          timestamp: new Date(),
        },
      ]);
      setDocumentActionLoading({ documentId: document.id, type });

      try {
        const response = await request(document.id);
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: buildAssistantMessage(response.data),
            timestamp: new Date(),
          },
        ]);
      } catch (error) {
        console.error(`${type} error:`, error);
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: `${errorPrefix}: ${error.response?.data?.detail || error.message}`,
            isError: true,
            timestamp: new Date(),
          },
        ]);
      } finally {
        setDocumentActionLoading(null);
      }
    },
    [documentActionLoading],
  );

  const handleGenerateSummary = useCallback(
    async (document) => {
      await runDocumentAction({
        document,
        type: "summary",
        userPrompt: "Generate summary",
        request: generateSummary,
        buildAssistantMessage: (data) => `**Summary**\n\n${data.summary}`,
        errorPrefix: "Error generating summary",
      });
    },
    [runDocumentAction],
  );

  const handleGenerateKeyPoints = useCallback(
    async (document) => {
      await runDocumentAction({
        document,
        type: "keyPoints",
        userPrompt: "Extract key points",
        request: generateKeyPoints,
        buildAssistantMessage: (data) => `**Key Points**\n\n${data.keyPoints}`,
        errorPrefix: "Error extracting key points",
      });
    },
    [runDocumentAction],
  );

  const handleGenerateQuestions = useCallback(
    async (document) => {
      await runDocumentAction({
        document,
        type: "questions",
        userPrompt: "Generate questions",
        request: generateImportantQuestions,
        buildAssistantMessage: (data) => `**Important Questions**\n\n${data.questions}`,
        errorPrefix: "Error generating questions",
      });
    },
    [runDocumentAction],
  );

  const handleClearDocument = useCallback(
    async (documentId) => {
      const document = uploadedDocuments.find((item) => item.id === documentId);

      try {
        await deleteDocument(documentId);
        setUploadedDocuments((prev) => prev.filter((item) => item.id !== documentId));
        setMessages((prev) => [
          ...prev,
          {
            type: "ACTION",
            content: `Document cleared: ${document?.name || "document"}`,
            role: "system",
          },
        ]);
      } catch (error) {
        console.error("Clear document error:", error);
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: `Error clearing document: ${error.response?.data?.detail || error.message}`,
            isError: true,
            timestamp: new Date(),
          },
        ]);
      }
    },
    [uploadedDocuments],
  );

  const handleClearSession = useCallback(async () => {
    try {
      await clearSession();
      console.log("Session cleared successfully");

      setMessages([]);
      setInputValue("");
      setUploadedDocuments([]);
      setCurrentAgent("GENERAL_ASSISTANT");

      localStorage.removeItem("sessionId");
      await createSession();
    } catch (error) {
      console.error("Clear session error:", error);
      throw error;
    }
  }, []);

  return (
    <div className="h-screen w-screen flex bg-gradient-dark overflow-hidden">
      <Sidebar
        isOpen={sidebarOpen}
        setIsOpen={setSidebarOpen}
        currentAgent={currentAgent}
        setCurrentAgent={setCurrentAgent}
        onUploadClick={() => setUploadModalOpen(true)}
        onClearSession={handleClearSession}
      />

      <main className="flex-1 flex flex-col md:flex-row gap-4 p-4 overflow-hidden md:ml-0">
        <div className="flex-1 flex flex-col glass rounded-xl border border-white/10 overflow-hidden">
          <ChatInterface
            messages={messages}
            uploadedDocument={hasDocuments}
            inputValue={inputValue}
            setInputValue={setInputValue}
            onSendMessage={handleSendMessage}
            isLoading={isAssistantLoading}
            currentAgent={currentAgent}
          />
        </div>

        {currentAgent === "PDF_INSIGHT_AGENT" && hasDocuments && (
          <div className="w-full md:w-72 flex flex-col gap-4">
            <DocumentPanel
              documents={uploadedDocuments}
              onGenerateSummary={handleGenerateSummary}
              onGenerateKeyPoints={handleGenerateKeyPoints}
              onGenerateQuestions={handleGenerateQuestions}
              onClear={handleClearDocument}
              actionLoading={documentActionLoading}
            />
          </div>
        )}
      </main>

      <UploadModal
        isOpen={uploadModalOpen && currentAgent === "PDF_INSIGHT_AGENT"}
        onClose={() => setUploadModalOpen(false)}
        onUpload={handleUploadDocument}
        isUploading={isUploading}
      />
    </div>
  );
}

export default App;
