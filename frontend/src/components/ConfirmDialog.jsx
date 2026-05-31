import React from "react";
import { AlertTriangle, X } from "lucide-react";

export function ConfirmDialog({
  isOpen,
  title,
  message,
  confirmText = "Confirm",
  cancelText = "Cancel",
  onConfirm,
  onCancel,
  isDangerous = false,
}) {
  if (!isOpen) return null;

  return (
    <>
      {/* Overlay */}
      <div className="fixed inset-0 bg-black/50 z-40" onClick={onCancel} />

      {/* Dialog */}
      <div className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-md">
        <div className="glass rounded-2xl border border-white/20 shadow-2xl p-6">
          {/* Header */}
          <div className="flex items-start gap-4 mb-4">
            {isDangerous && (
              <AlertTriangle
                className="text-red-400 flex-shrink-0 mt-1"
                size={24}
              />
            )}
            <div className="flex-1">
              <h2 className="text-lg font-bold text-white">{title}</h2>
            </div>
            <button
              onClick={onCancel}
              className="text-white/50 hover:text-white transition-colors"
            >
              <X size={20} />
            </button>
          </div>

          {/* Message */}
          <p className="text-white/80 mb-6 text-sm leading-relaxed">
            {message}
          </p>

          {/* Buttons */}
          <div className="flex gap-3 justify-end">
            <button
              onClick={onCancel}
              className="px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white text-sm font-semibold transition-all"
            >
              {cancelText}
            </button>
            <button
              onClick={onConfirm}
              className={`px-4 py-2 rounded-lg font-semibold text-sm transition-all flex items-center gap-2 ${
                isDangerous
                  ? "bg-red-500/80 hover:bg-red-500 text-white"
                  : "bg-blue-500/80 hover:bg-blue-500 text-white"
              }`}
            >
              {confirmText}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

export function SuccessDialog({ isOpen, title, message, onClose }) {
  React.useEffect(() => {
    if (isOpen) {
      const timer = setTimeout(onClose, 2500);
      return () => clearTimeout(timer);
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <>
      {/* Overlay */}
      <div className="fixed inset-0 bg-black/50 z-40" onClick={onClose} />

      {/* Dialog */}
      <div className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-md">
        <div className="glass rounded-2xl border border-green-500/30 shadow-2xl p-6 border-l-4 border-l-green-500">
          {/* Success Checkmark */}
          <div className="flex items-center justify-center mb-4">
            <div className="w-16 h-16 rounded-full bg-green-500/20 flex items-center justify-center">
              <svg
                className="w-8 h-8 text-green-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>
          </div>

          {/* Message */}
          <h2 className="text-lg font-bold text-center text-green-300 mb-2">
            {title}
          </h2>
          <p className="text-white/80 text-center text-sm">{message}</p>

          {/* Progress bar */}
          <div className="mt-4 h-1 bg-white/10 rounded-full overflow-hidden">
            <div className="h-full bg-green-500 animate-pulse" />
          </div>
        </div>
      </div>
    </>
  );
}

export default { ConfirmDialog, SuccessDialog };
