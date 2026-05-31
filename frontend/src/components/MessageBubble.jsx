import React, { useState } from "react";
import { Clock, FileText, Bot, Copy, Check, Info } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export function MessageBubble({ message }) {
  const isUser = message.role === "user";
  const isAction = message.type === "ACTION";
  const isFallbackAnswer = message.source === "FALLBACK_LLM";

  const formatTime = (date) => {
    if (!date) return "";
    const d = new Date(date);
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  if (isAction) {
    return (
      <div className="flex justify-center py-4">
        <div className="glass px-4 py-2 rounded-full text-xs text-white/60">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div
      className={`flex gap-3 animate-slide-in ${isUser ? "justify-end" : "justify-start"}`}
    >
      {!isUser && (
        <div className="w-8 h-8 rounded-full glass flex items-center justify-center flex-shrink-0">
          <Bot size={18} />
        </div>
      )}

      <div
        className={`max-w-xs lg:max-w-md xl:max-w-lg ${
          isUser
            ? "bg-gradient-primary rounded-l-lg rounded-tr-lg"
            : "glass rounded-r-lg rounded-tl-lg"
        } p-3 break-words group relative`}
      >
        {isFallbackAnswer && !isUser && (
          <div className="mb-3 flex gap-2 rounded-lg border border-yellow-400/30 bg-yellow-400/10 px-3 py-2 text-xs text-yellow-100">
            <Info size={14} className="mt-0.5 flex-shrink-0" />
            <span>
              This information was not found in the uploaded document. Answering from general AI knowledge.
            </span>
          </div>
        )}

        <div className="text-white text-sm markdown-content overflow-x-auto">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              p: ({ node, ...props }) => (
                <p className="mb-2 last:mb-0 whitespace-pre-wrap" {...props} />
              ),
              strong: ({ node, ...props }) => (
                <strong className="font-bold text-white" {...props} />
              ),
              em: ({ node, ...props }) => (
                <em className="italic text-white/90" {...props} />
              ),
              h1: ({ node, ...props }) => (
                <h1 className="text-lg font-bold mb-2 mt-2" {...props} />
              ),
              h2: ({ node, ...props }) => (
                <h2 className="text-base font-bold mb-2 mt-2" {...props} />
              ),
              h3: ({ node, ...props }) => (
                <h3 className="text-sm font-bold mb-1" {...props} />
              ),
              ul: ({ node, ...props }) => (
                <ul
                  className="list-disc list-inside mb-2 space-y-1"
                  {...props}
                />
              ),
              ol: ({ node, ...props }) => (
                <ol
                  className="list-decimal list-inside mb-2 space-y-1"
                  {...props}
                />
              ),
              li: ({ node, ...props }) => <li className="ml-2" {...props} />,
              table: ({ node, ...props }) => (
                <table
                  className="border-collapse border border-white/30 text-xs my-2"
                  {...props}
                />
              ),
              thead: ({ node, ...props }) => (
                <thead className="bg-white/10" {...props} />
              ),
              tbody: ({ node, ...props }) => <tbody {...props} />,
              tr: ({ node, ...props }) => (
                <tr className="border border-white/20" {...props} />
              ),
              th: ({ node, ...props }) => (
                <th
                  className="border border-white/20 px-2 py-1 font-bold text-blue-300 text-left"
                  {...props}
                />
              ),
              td: ({ node, ...props }) => (
                <td className="border border-white/20 px-2 py-1" {...props} />
              ),
              code: ({ node, inline, ...props }) =>
                inline ? (
                  <code
                    className="bg-white/10 px-1 py-0.5 rounded text-xs font-mono"
                    {...props}
                  />
                ) : (
                  <code
                    className="block bg-white/10 p-2 rounded text-xs font-mono mb-2 overflow-x-auto"
                    {...props}
                  />
                ),
              blockquote: ({ node, ...props }) => (
                <blockquote
                  className="border-l-2 border-white/30 pl-2 italic text-white/80 my-2"
                  {...props}
                />
              ),
              a: ({ node, ...props }) => (
                <a className="text-blue-400 hover:underline" {...props} />
              ),
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>
        {!isUser && <CopyButton text={message.content} />}

        {message.usedRAG && !isUser && (
          <div className="mt-3 pt-3 border-t border-white/20 text-xs text-white/60 space-y-1">
            <div className="flex items-center gap-1">
              <FileText size={14} />
              <span>Used document context</span>
            </div>
            {message.relevantChunks && message.relevantChunks.length > 0 && (
              <div className="text-white/40">
                {message.relevantChunks.length} source
                {message.relevantChunks.length > 1 ? "s" : ""}
              </div>
            )}
          </div>
        )}

        {message.timestamp && (
          <div className="mt-2 flex items-center gap-1 text-xs text-white/40">
            <Clock size={12} />
            <span>{formatTime(message.timestamp)}</span>
          </div>
        )}
      </div>
    </div>
  );
}

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error("Failed to copy:", error);
    }
  };

  return (
    <button
      onClick={handleCopy}
      className="absolute top-2 right-2 p-1 rounded bg-white/10 hover:bg-white/20 opacity-0 group-hover:opacity-100 transition-all"
      title="Copy message"
    >
      {copied ? (
        <Check size={16} className="text-green-400" />
      ) : (
        <Copy size={16} className="text-white/60" />
      )}
    </button>
  );
}

export default MessageBubble;
