import React, { useState } from "react";
import {
  Menu,
  X,
  Plus,
  MessageSquare,
  FileText,
  Trash2,
} from "lucide-react";
import { ConfirmDialog, SuccessDialog } from "./ConfirmDialog.jsx";
import { AGENTS } from "../utils/constants.js";

export function Sidebar({
  isOpen,
  setIsOpen,
  currentAgent,
  setCurrentAgent,
  onUploadClick,
  onClearSession,
}) {
  const [showConfirm, setShowConfirm] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");

  const handleAgentChange = (agentId) => {
    setCurrentAgent(agentId);
  };

  const handleDeleteAll = async () => {
    setShowConfirm(true);
  };

  const handleConfirmDelete = async () => {
    try {
      setShowConfirm(false);
      await onClearSession();
      setSuccessMessage("✅ All data cleared successfully. Starting fresh!");
      setShowSuccess(true);
    } catch (error) {
      console.error("Delete error:", error);
      setSuccessMessage("❌ Error clearing data: " + error.message);
      setShowSuccess(true);
    }
  };

  return (
    <>
      {/* Mobile toggle button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed top-4 left-4 z-40 md:hidden p-2 rounded-lg glass"
      >
        {isOpen ? <X size={24} /> : <Menu size={24} />}
      </button>

      {/* Sidebar overlay for mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 md:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed left-0 top-0 h-screen w-64 glass border-r border-white/10 transform transition-transform duration-300 z-35 md:static md:transform-none ${
          isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        }`}
      >
        <div className="h-full flex flex-col p-4">
          {/* Logo */}
          <div className="mb-8">
            <h1 className="text-2xl font-bold gradient-text">PDF Insight</h1>
            <p className="text-xs text-white/50 mt-1">AI Document Assistant</p>
          </div>

          {/* Agents */}
          <div className="flex-1">
            <p className="text-xs text-white/50 font-semibold mb-3">AGENTS</p>
            <div className="space-y-2">
              {Object.entries(AGENTS).map(([key, agent]) => (
                <button
                  key={key}
                  onClick={() => {
                    handleAgentChange(agent.id);
                    setIsOpen(false);
                  }}
                  className={`w-full p-3 rounded-lg transition-all text-left border-2 ${
                    currentAgent === agent.id
                      ? "border-blue-500 bg-blue-500/20 bg-gradient-primary/30 shadow-lg shadow-blue-500/20"
                      : "border-transparent glass hover:bg-white/10"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    {agent.id === "GENERAL_ASSISTANT" && (
                      <MessageSquare
                        size={18}
                        className={
                          currentAgent === agent.id ? "text-blue-400" : ""
                        }
                      />
                    )}
                    {agent.id === "PDF_INSIGHT_AGENT" && (
                      <FileText
                        size={18}
                        className={
                          currentAgent === agent.id ? "text-blue-400" : ""
                        }
                      />
                    )}
                    <div>
                      <div
                        className={`font-semibold text-sm ${
                          currentAgent === agent.id ? "text-blue-300" : ""
                        }`}
                      >
                        {agent.name}
                      </div>
                      <div className="text-xs text-white/50">
                        {agent.description}
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Action Buttons Section */}
          <div className="space-y-3 mb-4">
            {/* Upload button - only show for PDF Insight Agent */}
            {currentAgent === "PDF_INSIGHT_AGENT" && (
              <button
                onClick={onUploadClick}
                className="w-full py-3 px-3 rounded-lg bg-gradient-primary hover:shadow-lg hover:shadow-blue-500/50 font-semibold transition-all flex items-center justify-center gap-2 text-sm"
              >
                <Plus size={18} />
                Upload Document
              </button>
            )}

            {/* Delete All Button - Unified delete for docs + chat */}
            <button
              onClick={handleDeleteAll}
              className="w-full py-2 px-3 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-red-300 text-xs font-semibold transition-all flex items-center justify-center gap-2 border border-red-500/30"
            >
              <Trash2 size={16} />
              Delete All
            </button>
          </div>

          {/* Footer */}
          <div className="text-xs text-white/40 border-t border-white/10 pt-4">
            <p>Session-based temporary storage</p>
            <p className="mt-1">Data auto-clears on refresh</p>
          </div>
        </div>
      </aside>

      {/* Confirm Dialog */}
      <ConfirmDialog
        isOpen={showConfirm}
        title="Delete All Data?"
        message="This will delete all documents, chat history, and uploaded files. This action cannot be undone."
        confirmText="Delete All"
        cancelText="Cancel"
        onConfirm={handleConfirmDelete}
        onCancel={() => setShowConfirm(false)}
        isDangerous={true}
      />

      {/* Success Dialog */}
      <SuccessDialog
        isOpen={showSuccess}
        title="Done!"
        message={successMessage}
        onClose={() => setShowSuccess(false)}
      />
    </>
  );
}

export default Sidebar;
