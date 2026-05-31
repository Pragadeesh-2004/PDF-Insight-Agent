import React, { useEffect, useRef } from "react";
import { Send, Loader } from "lucide-react";
import MessageBubble from "./MessageBubble.jsx";

export function ChatInterface({
  messages,
  inputValue,
  setInputValue,
  onSendMessage,
  isLoading,
  currentAgent,
  uploadedDocument,
}) {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e) => {
    e.preventDefault();
    // Disable send if in PDF mode without a document
    if (currentAgent === "PDF_INSIGHT_AGENT" && !uploadedDocument) {
      return;
    }
    if (inputValue.trim() && !isLoading) {
      onSendMessage(inputValue);
      setInputValue("");
    }
  };

  const canSend =
    inputValue.trim() &&
    !isLoading &&
    (currentAgent !== "PDF_INSIGHT_AGENT" || uploadedDocument);

  return (
    <div className="flex flex-col h-full">
      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center flex-col text-center">
            <div className="text-5xl mb-4">👋</div>
            <h2 className="text-2xl font-bold gradient-text mb-2">
              Welcome to PDF Insight Agent
            </h2>
            <p className="text-white/60 mb-4">
              {currentAgent === "PDF_INSIGHT_AGENT"
                ? "Upload documents, extract insights, and chat with your files"
                : "Ask me anything and I will help you"}
            </p>
           
          </div>
        ) : (
          messages.map((message, index) => (
            <MessageBubble key={index} message={message} />
          ))
        )}
        {isLoading && (
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full glass flex items-center justify-center flex-shrink-0">
              <div className="w-4 h-4 rounded-full border-2 border-primary border-t-transparent animate-spin"></div>
            </div>
            <div className="glass p-3 rounded-lg">
              <p className="text-white/60 text-sm">AI is thinking...</p>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-white/10 p-4 glass-dark">
        <form onSubmit={handleSubmit} className="flex gap-3">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder={
              currentAgent === "PDF_INSIGHT_AGENT"
                ? "Ask about your documents..."
                : "Ask me anything..."
            }
            disabled={isLoading}
            className="input-field flex-1 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!canSend}
            title={
              currentAgent === "PDF_INSIGHT_AGENT" && !uploadedDocument
                ? "Please upload a PDF first"
                : ""
            }
            className="px-6 py-3 rounded-lg bg-gradient-primary hover:shadow-lg hover:shadow-blue-500/50 font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
          >
            {isLoading ? (
              <Loader size={20} className="animate-spin" />
            ) : (
              <Send size={20} />
            )}
            {!isLoading && "Send"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default ChatInterface;
