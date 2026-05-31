import React from "react";
import { FileText, Zap, Brain, HelpCircle, Trash2, Loader } from "lucide-react";

const actions = [
  {
    id: "summary",
    label: "Generate Summary",
    Icon: Zap,
  },
  {
    id: "keyPoints",
    label: "Extract Key Points",
    Icon: Brain,
  },
  {
    id: "questions",
    label: "Generate Questions",
    Icon: HelpCircle,
  },
];

export function DocumentPanel({
  documents,
  onGenerateSummary,
  onGenerateKeyPoints,
  onGenerateQuestions,
  onClear,
  actionLoading,
}) {
  const handlers = {
    summary: onGenerateSummary,
    keyPoints: onGenerateKeyPoints,
    questions: onGenerateQuestions,
  };

  return (
    <aside className="glass rounded-xl p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-white">Document Store</h2>
        <span className="text-xs text-white/50">{documents.length}/5</span>
      </div>

      <div className="space-y-3 max-h-[calc(100vh-8rem)] overflow-y-auto pr-1">
        {documents.map((document) => (
          <div
            key={document.id}
            className="rounded-lg border border-white/10 bg-white/5 p-3 space-y-3"
          >
            <div className="flex items-center gap-2">
              <FileText size={20} className="text-primary flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-sm truncate">
                  {document.name}
                </p>
                <p className="text-xs text-white/50">
                  {document.chunksCreated || 0} chunks
                </p>
              </div>
              <button
                type="button"
                onClick={() => onClear(document.id)}
                disabled={Boolean(actionLoading)}
                className="p-2 rounded-lg text-red-300 hover:bg-red-500/20 transition-all disabled:opacity-50"
                title="Clear document"
              >
                <Trash2 size={16} />
              </button>
            </div>

            <div className="space-y-2">
              {actions.map(({ id, label, Icon }) => {
                const isThisAction =
                  actionLoading?.documentId === document.id &&
                  actionLoading?.type === id;

                return (
                  <button
                    key={id}
                    type="button"
                    onClick={() => handlers[id](document)}
                    disabled={Boolean(actionLoading)}
                    className="w-full flex items-center gap-2 px-3 py-2 bg-white/5 hover:bg-white/10 rounded-lg transition-all disabled:opacity-50 text-sm"
                  >
                    {isThisAction ? (
                      <Loader size={16} className="animate-spin" />
                    ) : (
                      <Icon size={16} />
                    )}
                    {label}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
}

export default DocumentPanel;
